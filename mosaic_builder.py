"""
mosaic_builder.py
-----------------
Módulo para montagem de mosaico (stitching) de imagens capturadas em grade.

Funcionalidades:
  - Carrega tiles no padrão *_rNNN_cNNN.png
  - Aplica correção de distorção usando calibração de câmera
  - Aplica corte de bordas para remover distorções residuais
  - Monta imagem panorâmica com blending multiband para junções invisíveis
  - Interface PyQt6 standalone ou uso programático

Uso standalone:
    python mosaic_builder.py

Uso programático:
    from mosaic_builder import compose_mosaic_from_folder
    result_path = compose_mosaic_from_folder("pasta/com/imagens", margin=50)
"""

import os
import re
import sys
import cv2
import numpy as np
from typing import Dict, Tuple, Optional, List

# PyQt6 imports apenas se usado em modo GUI
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QFileDialog, QSpinBox, QGroupBox, QMessageBox,
        QCheckBox, QProgressBar, QComboBox, QGraphicsView, QGraphicsScene
    )
    from PyQt6.QtGui import QPixmap, QImage, QWheelEvent, QMouseEvent
    from PyQt6.QtCore import Qt, QPoint
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False

# Calibração de câmera (opcional)
try:
    from camera_calibration import CameraCalibrator
    HAS_CALIBRATION = True
except ImportError:
    HAS_CALIBRATION = False

import logging
log = logging.getLogger(__name__)


# Regex para detectar tiles: nome_r000_c000.png
TILE_RX = re.compile(
    r"^(?P<name>.+)_r(?P<row>\d+)_c(?P<col>\d+)\.(?P<ext>png|jpg|jpeg)$",
    re.IGNORECASE
)


# =============================================================================
# FUNÇÕES DE BLENDING
# =============================================================================

def create_gaussian_pyramid(img: np.ndarray, levels: int) -> List[np.ndarray]:
    """Cria pirâmide Gaussiana."""
    pyramid = [img.astype(np.float32)]
    for _ in range(levels):
        img = cv2.pyrDown(img)
        pyramid.append(img.astype(np.float32))
    return pyramid


def create_laplacian_pyramid(img: np.ndarray, levels: int) -> List[np.ndarray]:
    """Cria pirâmide Laplaciana."""
    gaussian = create_gaussian_pyramid(img, levels)
    laplacian = []
    for i in range(levels):
        size = (gaussian[i].shape[1], gaussian[i].shape[0])
        expanded = cv2.pyrUp(gaussian[i + 1], dstsize=size)
        laplacian.append(gaussian[i] - expanded)
    laplacian.append(gaussian[-1])
    return laplacian


def reconstruct_from_laplacian(pyramid: List[np.ndarray]) -> np.ndarray:
    """Reconstrói imagem a partir da pirâmide Laplaciana."""
    img = pyramid[-1]
    for i in range(len(pyramid) - 2, -1, -1):
        size = (pyramid[i].shape[1], pyramid[i].shape[0])
        img = cv2.pyrUp(img, dstsize=size) + pyramid[i]
    return img


def multiband_blend(img1: np.ndarray, img2: np.ndarray, 
                    mask: np.ndarray, levels: int = 4) -> np.ndarray:
    """
    Faz blending multiband de duas imagens.
    
    Args:
        img1: Primeira imagem
        img2: Segunda imagem
        mask: Máscara (0-1) indicando quanto de img2 usar
        levels: Níveis da pirâmide
        
    Returns:
        Imagem resultante com blending suave
    """
    # Garante que as imagens têm o mesmo tamanho
    if img1.shape != img2.shape:
        return img2 if mask.mean() > 0.5 else img1
        
    # Normaliza máscara
    if mask.max() > 1:
        mask = mask.astype(np.float32) / 255.0
    if len(mask.shape) == 2:
        mask = np.stack([mask] * 3, axis=-1)
        
    # Cria pirâmides Laplacianas
    lp1 = create_laplacian_pyramid(img1, levels)
    lp2 = create_laplacian_pyramid(img2, levels)
    
    # Cria pirâmide Gaussiana da máscara
    gp_mask = create_gaussian_pyramid(mask, levels)
    
    # Combina as pirâmides
    blended_pyramid = []
    for l1, l2, gm in zip(lp1, lp2, gp_mask):
        blended = l1 * (1 - gm) + l2 * gm
        blended_pyramid.append(blended)
        
    # Reconstrói
    result = reconstruct_from_laplacian(blended_pyramid)
    return np.clip(result, 0, 255).astype(np.uint8)


def create_blend_mask(tile_h: int, tile_w: int, blend_size: int) -> np.ndarray:
    """
    Cria máscara de blending gradual para suavizar transições entre tiles.
    
    Args:
        tile_h: Altura do tile
        tile_w: Largura do tile
        blend_size: Tamanho da zona de transição em pixels
        
    Returns:
        Máscara float32 com valores de 0.0 a 1.0
    """
    mask = np.ones((tile_h, tile_w), dtype=np.float32)
    
    if blend_size <= 0:
        return mask
    
    # Feather nas bordas (gradiente linear)
    for i in range(min(blend_size, tile_h // 2)):
        alpha = i / blend_size
        mask[i, :] = min(mask[i, 0], alpha)
        mask[tile_h - 1 - i, :] = min(mask[tile_h - 1 - i, 0], alpha)
        
    for j in range(min(blend_size, tile_w // 2)):
        alpha = j / blend_size
        mask[:, j] = np.minimum(mask[:, j], alpha)
        mask[:, tile_w - 1 - j] = np.minimum(mask[:, tile_w - 1 - j], alpha)
        
    return mask


# =============================================================================
# FUNÇÕES CORE
# =============================================================================

def load_tiles(folder: str) -> Tuple[Dict[Tuple[int, int], str], Optional[str]]:
    """
    Varre a pasta e devolve dicionário {(row, col): filepath}, program_name.
    """
    tiles = {}
    program_name = None
    
    if not os.path.isdir(folder):
        return tiles, program_name
        
    for fn in os.listdir(folder):
        m = TILE_RX.match(fn)
        if m:
            row = int(m.group("row"))
            col = int(m.group("col"))
            tiles[(row, col)] = os.path.join(folder, fn)
            if program_name is None:
                program_name = m.group("name")
                
    return tiles, program_name


def crop_tile_margins(image: np.ndarray, margin: int) -> np.ndarray:
    """Remove as margens de uma imagem para eliminar distorções de lente."""
    if margin <= 0:
        return image
        
    h, w = image.shape[:2]
    
    if margin * 2 >= h or margin * 2 >= w:
        return image
        
    return image[margin:h-margin, margin:w-margin].copy()


def compose_mosaic(
    tiles: Dict[Tuple[int, int], str],
    delta_x: int = 0,
    delta_y: int = 0,
    invert_rows: bool = False,
    margin: int = 0,
    blend_size: int = 0,
    use_multiband: bool = False,
    calibrator: Optional['CameraCalibrator'] = None,
    progress_callback=None,
) -> Tuple[np.ndarray, int, int, Tuple[int, int]]:
    """
    Monta o mosaico a partir dos tiles capturados.
    
    Args:
        tiles: Dicionário {(row, col): filepath}
        delta_x: Ajuste horizontal entre tiles (pixels, negativo = sobreposição)
        delta_y: Ajuste vertical entre tiles (pixels, negativo = sobreposição)
        invert_rows: Se True, inverte a ordem das linhas (origem inferior-esquerda)
        margin: Pixels a cortar de cada borda dos tiles
        blend_size: Tamanho da zona de blending (0 = sem blending)
        use_multiband: Se True, usa blending multiband (mais lento, melhor qualidade)
        calibrator: Objeto CameraCalibrator para correção de distorção
        progress_callback: Função opcional (current, total) para progresso
        
    Returns:
        Tupla (imagem_mosaico, num_rows, num_cols, (tile_w, tile_h))
    """
    if not tiles:
        raise ValueError("Nenhum tile encontrado.")

    # Carrega primeira imagem para obter dimensões
    first_path = next(iter(tiles.values()))
    first = cv2.imread(first_path)
    if first is None:
        raise IOError(f"Falha ao ler imagem: {first_path}")
    
    # Aplica correção de distorção se disponível
    if calibrator is not None:
        first = calibrator.undistort(first, crop=True)
    
    # Aplica corte de margem para calcular dimensões finais
    first_cropped = crop_tile_margins(first, margin)
    tile_h, tile_w = first_cropped.shape[:2]

    # Calcula dimensões da grade
    rows = max(r for r, _ in tiles.keys()) + 1
    cols = max(c for _, c in tiles.keys()) + 1

    # Calcula tamanho do canvas
    step_x = tile_w + delta_x
    step_y = tile_h + delta_y
    
    canvas_h = tile_h + (rows - 1) * step_y
    canvas_w = tile_w + (cols - 1) * step_x

    # Cria canvas e acumulador de pesos
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)
    weights = np.zeros((canvas_h, canvas_w), dtype=np.float32)
    
    # Máscara de blending
    blend_mask = create_blend_mask(tile_h, tile_w, blend_size) if blend_size > 0 else None
    
    total_tiles = len(tiles)
    processed = 0

    # Ordena tiles para processamento (importante para blending)
    sorted_tiles = sorted(tiles.items(), key=lambda x: (x[0][0], x[0][1]))

    for (r, c), path in sorted_tiles:
        img = cv2.imread(path)
        if img is None:
            continue
        
        # Aplica correção de distorção
        if calibrator is not None:
            img = calibrator.undistort(img, crop=True)
            
        # Aplica corte de margem
        img = crop_tile_margins(img, margin)
        
        # Garante que o tile tem o tamanho esperado
        if img.shape[0] != tile_h or img.shape[1] != tile_w:
            img = cv2.resize(img, (tile_w, tile_h))
        
        # Índice de linha (com possível inversão)
        r_plot = (rows - 1 - r) if invert_rows else r

        # Calcula posição no canvas
        y0 = r_plot * step_y
        x0 = c * step_x
        y1 = min(y0 + tile_h, canvas_h)
        x1 = min(x0 + tile_w, canvas_w)
        actual_h = y1 - y0
        actual_w = x1 - x0
        
        if blend_mask is not None and blend_size > 0:
            img_float = img[:actual_h, :actual_w].astype(np.float32)
            mask_slice = blend_mask[:actual_h, :actual_w]
            
            if use_multiband and weights[y0:y1, x0:x1].max() > 0:
                # Blending multiband para sobreposição
                existing = canvas[y0:y1, x0:x1].copy()
                if existing.max() > 0:
                    blend_weight = np.zeros((actual_h, actual_w), dtype=np.float32)
                    blend_weight[:, :actual_w//2] = np.linspace(0, 1, actual_w//2)[np.newaxis, :]
                    blend_weight[:, actual_w//2:] = np.linspace(1, 0, actual_w - actual_w//2)[np.newaxis, :]
                    
                    blended = multiband_blend(
                        existing.astype(np.uint8),
                        img_float.astype(np.uint8),
                        blend_weight,
                        levels=3
                    )
                    canvas[y0:y1, x0:x1] = blended.astype(np.float32)
                    weights[y0:y1, x0:x1] = 1.0
                else:
                    for ch in range(3):
                        canvas[y0:y1, x0:x1, ch] += img_float[:, :, ch] * mask_slice
                    weights[y0:y1, x0:x1] += mask_slice
            else:
                # Blending linear simples
                for ch in range(3):
                    canvas[y0:y1, x0:x1, ch] += img_float[:, :, ch] * mask_slice
                weights[y0:y1, x0:x1] += mask_slice
        else:
            # Sem blending: sobrescreve
            canvas[y0:y1, x0:x1] = img[:actual_h, :actual_w].astype(np.float32)
            weights[y0:y1, x0:x1] = 1.0
            
        processed += 1
        if progress_callback:
            progress_callback(processed, total_tiles)

    # Normaliza pelo peso
    weights = np.maximum(weights, 1e-6)
    for ch in range(3):
        canvas[:, :, ch] /= weights
        
    canvas = np.clip(canvas, 0, 255).astype(np.uint8)

    return canvas, rows, cols, (tile_w, tile_h)


def compose_mosaic_from_folder(
    folder: str,
    delta_x: int = 0,
    delta_y: int = 0,
    invert_rows: bool = True,
    margin: int = 0,
    blend_size: int = 20,
    use_multiband: bool = False,
    calibration_file: Optional[str] = None,
    output_suffix: str = "_mosaic",
    progress_callback=None,
) -> Optional[str]:
    """
    Função de conveniência para montar mosaico de uma pasta.
    
    Args:
        folder: Pasta contendo as imagens *_rNNN_cNNN.png
        delta_x: Ajuste horizontal entre tiles
        delta_y: Ajuste vertical entre tiles
        invert_rows: Inverter ordem das linhas
        margin: Pixels a cortar de cada borda
        blend_size: Tamanho da zona de blending
        use_multiband: Usar blending multiband
        calibration_file: Arquivo JSON com calibração de câmera
        output_suffix: Sufixo para o arquivo de saída
        progress_callback: Função (current, total) para progresso
        
    Returns:
        Caminho do arquivo gerado ou None se falhou
    """
    tiles, program_name = load_tiles(folder)
    
    if not tiles:
        return None
        
    if program_name is None:
        program_name = "mosaic"
    
    # Carrega calibração se disponível
    calibrator = None
    if calibration_file and HAS_CALIBRATION:
        calibrator = CameraCalibrator()
        if not calibrator.load(calibration_file):
            calibrator = None
            log.warning(f"Não foi possível carregar calibração: {calibration_file}")
        
    try:
        mosaic, rows, cols, _ = compose_mosaic(
            tiles,
            delta_x=delta_x,
            delta_y=delta_y,
            invert_rows=invert_rows,
            margin=margin,
            blend_size=blend_size,
            use_multiband=use_multiband,
            calibrator=calibrator,
            progress_callback=progress_callback,
        )
    except Exception as e:
        log.error(f"Erro ao montar mosaico: {e}")
        return None
        
    # Salva o resultado
    output_path = os.path.join(folder, f"{program_name}{output_suffix}.png")
    cv2.imwrite(output_path, mosaic)
    
    return output_path


# =============================================================================
# INTERFACE GRÁFICA
# =============================================================================

if HAS_PYQT:
    class MosaicBuilder(QMainWindow):
        """Interface gráfica para montagem de mosaicos."""
        
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Mosaic Builder - Montagem de Imagem de Stencil")
            self.folder = ""
            self.tiles = {}
            self.program_name = "mosaic"
            self.calibrator = None
            self._build_ui()

        def _build_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            # Layout principal: preview à esquerda, controles à direita
            h_main = QHBoxLayout(central)

            # Preview com zoom/pan
            self.preview = MosaicPreview()
            h_main.addWidget(self.preview, 2)

            # Painel de controles
            v = QVBoxLayout()
            h_main.addLayout(v, 1)

            # --- Seletor de pasta ---
            grp = QGroupBox("Seleção de Imagens")
            gl = QHBoxLayout(grp)
            self.folder_lbl = QLabel("Nenhuma pasta selecionada")
            sel_btn = QPushButton("Selecionar Pasta")
            sel_btn.clicked.connect(self.on_select_folder)
            gl.addWidget(sel_btn)
            gl.addWidget(self.folder_lbl, 1)
            v.addWidget(grp)

            # --- Calibração de Câmera ---
            calib_grp = QGroupBox("Correção de Distorção (Calibração)")
            calib_layout = QHBoxLayout(calib_grp)
            
            self.calib_status = QLabel("Sem calibração carregada")
            calib_layout.addWidget(self.calib_status)
            
            btn_load_calib = QPushButton("Carregar Calibração")
            btn_load_calib.clicked.connect(self._load_calibration)
            calib_layout.addWidget(btn_load_calib)
            
            self.chk_use_calib = QCheckBox("Aplicar correção")
            self.chk_use_calib.setChecked(True)
            self.chk_use_calib.setEnabled(False)
            calib_layout.addWidget(self.chk_use_calib)
            
            v.addWidget(calib_grp)

            # --- Configurações de Corte ---
            crop_grp = QGroupBox("Corte de Bordas")
            crop_layout = QHBoxLayout(crop_grp)
            crop_layout.addWidget(QLabel("Margem (px):"))
            self.spin_margin = QSpinBox()
            self.spin_margin.setRange(0, 500)
            self.spin_margin.setValue(50)
            self.spin_margin.setToolTip("Pixels a remover de cada borda")
            crop_layout.addWidget(self.spin_margin)
            crop_layout.addStretch()
            v.addWidget(crop_grp)

            # --- Ajuste de Pitch ---
            adj = QGroupBox("Ajuste de Sobreposição")
            hl = QHBoxLayout(adj)
            hl.addWidget(QLabel("ΔX:"))
            self.spin_dx = QSpinBox()
            self.spin_dx.setRange(-500, 500)
            self.spin_dx.setValue(0)
            self.spin_dx.setToolTip("Negativo = sobreposição, Positivo = gap")
            hl.addWidget(self.spin_dx)
            hl.addWidget(QLabel("ΔY:"))
            self.spin_dy = QSpinBox()
            self.spin_dy.setRange(-500, 500)
            self.spin_dy.setValue(0)
            hl.addWidget(self.spin_dy)
            v.addWidget(adj)

            # --- Opções de Blending ---
            blend_grp = QGroupBox("Blending (Suavização de Junções)")
            blend_layout = QHBoxLayout(blend_grp)
            
            self.chk_blend = QCheckBox("Aplicar blending")
            self.chk_blend.setChecked(True)
            blend_layout.addWidget(self.chk_blend)
            
            blend_layout.addWidget(QLabel("Tamanho:"))
            self.spin_blend = QSpinBox()
            self.spin_blend.setRange(0, 200)
            self.spin_blend.setValue(20)
            blend_layout.addWidget(self.spin_blend)
            
            blend_layout.addWidget(QLabel("Tipo:"))
            self.combo_blend_type = QComboBox()
            self.combo_blend_type.addItems(["Linear (rápido)", "Multiband (qualidade)"])
            blend_layout.addWidget(self.combo_blend_type)
            
            blend_layout.addStretch()
            v.addWidget(blend_grp)

            # --- Orientação ---
            orient_grp = QGroupBox("Orientação")
            orient_layout = QHBoxLayout(orient_grp)
            self.chk_invert = QCheckBox("Origem no canto inferior-esquerdo")
            self.chk_invert.setChecked(True)
            orient_layout.addWidget(self.chk_invert)
            v.addWidget(orient_grp)

            # --- Botão Montar ---
            build_btn = QPushButton("🔧 Montar Mosaico")
            build_btn.setMinimumHeight(40)
            build_btn.clicked.connect(self.on_build)
            v.addWidget(build_btn)

            # --- Barra de Progresso ---
            self.progress = QProgressBar()
            self.progress.setVisible(False)
            v.addWidget(self.progress)

            v.addStretch(1)

            self.statusBar().showMessage("Selecione a pasta com as imagens capturadas")

        def _load_calibration(self):
            """Carrega arquivo de calibração."""
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Carregar Calibração de Câmera",
                "", "Arquivos JSON (*.json)"
            )
            
            if filepath and HAS_CALIBRATION:
                self.calibrator = CameraCalibrator()
                if self.calibrator.load(filepath):
                    self.calib_status.setText(f"✅ Calibração carregada: RMS={self.calibrator.rms_error:.3f}")
                    self.chk_use_calib.setEnabled(True)
                else:
                    self.calibrator = None
                    self.calib_status.setText("❌ Falha ao carregar")
                    self.chk_use_calib.setEnabled(False)

        def on_select_folder(self):
            folder = QFileDialog.getExistingDirectory(self, "Escolha a pasta com as imagens")
            if folder:
                self.folder = folder
                self.folder_lbl.setText(folder)
                self.tiles, self.program_name = load_tiles(folder)
                if not self.tiles:
                    QMessageBox.warning(self, "Aviso", "Nenhum arquivo *_rNNN_cNNN.png encontrado.")
                else:
                    rows = max(r for r, _ in self.tiles.keys()) + 1
                    cols = max(c for _, c in self.tiles.keys()) + 1
                    self.statusBar().showMessage(
                        f"{len(self.tiles)} imagens encontradas ({cols}x{rows} grid)"
                    )

        def on_build(self):
            if not self.tiles:
                QMessageBox.warning(self, "Erro", "Nenhuma imagem carregada.")
                return
                
            dx = self.spin_dx.value()
            dy = self.spin_dy.value()
            margin = self.spin_margin.value()
            blend_size = self.spin_blend.value() if self.chk_blend.isChecked() else 0
            use_multiband = self.combo_blend_type.currentIndex() == 1
            invert = self.chk_invert.isChecked()
            
            # Usa calibração se disponível e habilitada
            calibrator = None
            if self.calibrator is not None and self.chk_use_calib.isChecked():
                calibrator = self.calibrator
            
            self.progress.setVisible(True)
            self.progress.setRange(0, len(self.tiles))
            self.progress.setValue(0)
            
            def update_progress(current, total):
                self.progress.setValue(current)
                QApplication.processEvents()
            
            try:
                mosaic, rows, cols, (tw, th) = compose_mosaic(
                    self.tiles, dx, dy,
                    invert_rows=invert,
                    margin=margin,
                    blend_size=blend_size,
                    use_multiband=use_multiband,
                    calibrator=calibrator,
                    progress_callback=update_progress,
                )
            except Exception as e:
                QMessageBox.critical(self, "Falha", str(e))
                self.progress.setVisible(False)
                return

            self.progress.setVisible(False)

            # Salva
            out_name = os.path.join(self.folder, f"{self.program_name}_mosaic.png")
            cv2.imwrite(out_name, mosaic)

            # Exibe preview com zoom/pan
            self.preview.set_image(mosaic)
                
            self.statusBar().showMessage(
                f"✅ Mosaico criado: {mosaic.shape[1]}x{mosaic.shape[0]} px ({cols}x{rows} tiles). Salvo: {out_name}"
            )


# =============================================================================
# Preview com zoom e pan
# =============================================================================

class MosaicPreview(QGraphicsView):
    """Preview que suporta zoom com scroll e pan com botão do meio."""
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self._pixmap_item = None
        self._zoom = 1.0
        self._panning = False
        self._pan_start: QPoint | None = None
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setBackgroundBrush(Qt.GlobalColor.lightGray)

    def set_image(self, image: np.ndarray):
        """Recebe imagem BGR (numpy) e exibe com reset de zoom."""
        if image is None:
            return
        h, w = image.shape[:2]
        bytes_per_line = 3 * w
        qimg = QImage(image.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        pix = QPixmap.fromImage(qimg)

        self.scene().clear()
        self._pixmap_item = self.scene().addPixmap(pix)
        self._zoom = 1.0
        self.resetTransform()
        self.fitInView(self._pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    # Zoom com scroll
    def wheelEvent(self, event: QWheelEvent):
        if self._pixmap_item is None:
            return
        angle = event.angleDelta().y()
        factor = 1.15 if angle > 0 else 1/1.15
        self._zoom *= factor
        self.scale(factor, factor)

    # Pan com botão do meio
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._panning and self._pan_start is not None:
            delta = event.position().toPoint() - self._pan_start
            self._pan_start = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseReleaseEvent(event)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    if not HAS_PYQT:
        print("PyQt6 não disponível. Use a função compose_mosaic_from_folder() programaticamente.")
        sys.exit(1)
        
    app = QApplication(sys.argv)
    win = MosaicBuilder()
    win.resize(1200, 900)
    win.show()
    sys.exit(app.exec())
