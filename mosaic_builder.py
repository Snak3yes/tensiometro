"""
mosaic_builder.py
-----------------
Módulo para montagem de mosaico (stitching) de imagens capturadas em grade.

Funcionalidades:
  - Carrega tiles no padrão *_rNNN_cNNN.png
  - Aplica corte de bordas para remover distorções de lente
  - Monta imagem panorâmica com opção de blending nas junções
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
        QCheckBox, QProgressBar,
    )
    from PyQt6.QtGui import QPixmap, QImage
    from PyQt6.QtCore import Qt
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False


# Regex para detectar tiles: nome_r000_c000.png
TILE_RX = re.compile(
    r"^(?P<name>.+)_r(?P<row>\d+)_c(?P<col>\d+)\.(?P<ext>png|jpg|jpeg)$",
    re.IGNORECASE
)


# =============================================================================
# FUNÇÕES CORE (usáveis programaticamente)
# =============================================================================

def load_tiles(folder: str) -> Tuple[Dict[Tuple[int, int], str], Optional[str]]:
    """
    Varre a pasta e devolve dicionário {(row, col): filepath}, program_name.
    
    Args:
        folder: Caminho da pasta contendo as imagens
        
    Returns:
        Tupla (tiles_dict, program_name)
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
    """
    Remove as margens de uma imagem para eliminar distorções de lente.
    
    Args:
        image: Imagem OpenCV (BGR ou grayscale)
        margin: Quantidade de pixels a remover de cada lado
        
    Returns:
        Imagem cortada
    """
    if margin <= 0:
        return image
        
    h, w = image.shape[:2]
    
    # Garante que não cortamos mais do que a imagem permite
    if margin * 2 >= h or margin * 2 >= w:
        return image
        
    return image[margin:h-margin, margin:w-margin].copy()


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


def compose_mosaic(
    tiles: Dict[Tuple[int, int], str],
    delta_x: int = 0,
    delta_y: int = 0,
    invert_rows: bool = False,
    margin: int = 0,
    blend_size: int = 0,
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
    
    # Aplica corte de margem para calcular dimensões finais
    first_cropped = crop_tile_margins(first, margin)
    tile_h, tile_w = first_cropped.shape[:2]

    # Calcula dimensões da grade
    rows = max(r for r, _ in tiles.keys()) + 1
    cols = max(c for _, c in tiles.keys()) + 1

    # Calcula tamanho do canvas
    # O passo efetivo considera o delta (negativo = sobreposição)
    step_x = tile_w + delta_x
    step_y = tile_h + delta_y
    
    canvas_h = tile_h + (rows - 1) * step_y
    canvas_w = tile_w + (cols - 1) * step_x

    # Cria canvas e acumulador de pesos (para blending)
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)
    weights = np.zeros((canvas_h, canvas_w), dtype=np.float32)
    
    # Máscara de blending (reutilizada para todos os tiles)
    blend_mask = create_blend_mask(tile_h, tile_w, blend_size) if blend_size > 0 else None
    
    total_tiles = len(tiles)
    processed = 0

    for (r, c), path in tiles.items():
        img = cv2.imread(path)
        if img is None:
            continue
            
        # Aplica corte de margem
        img = crop_tile_margins(img, margin)
        
        # Índice de linha (com possível inversão)
        r_plot = (rows - 1 - r) if invert_rows else r

        # Calcula posição no canvas
        y0 = r_plot * step_y
        x0 = c * step_x
        y1 = y0 + tile_h
        x1 = x0 + tile_w
        
        # Garante que não ultrapassa o canvas
        y1 = min(y1, canvas_h)
        x1 = min(x1, canvas_w)
        actual_h = y1 - y0
        actual_w = x1 - x0
        
        if blend_mask is not None and blend_size > 0:
            # Blending com máscara
            img_float = img[:actual_h, :actual_w].astype(np.float32)
            mask_slice = blend_mask[:actual_h, :actual_w]
            
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

    # Normaliza pelo peso (evita divisão por zero)
    weights = np.maximum(weights, 1e-6)
    for ch in range(3):
        canvas[:, :, ch] /= weights
        
    # Converte para uint8
    canvas = np.clip(canvas, 0, 255).astype(np.uint8)

    return canvas, rows, cols, (tile_w, tile_h)


def compose_mosaic_from_folder(
    folder: str,
    delta_x: int = 0,
    delta_y: int = 0,
    invert_rows: bool = True,
    margin: int = 0,
    blend_size: int = 20,
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
        
    try:
        mosaic, rows, cols, _ = compose_mosaic(
            tiles,
            delta_x=delta_x,
            delta_y=delta_y,
            invert_rows=invert_rows,
            margin=margin,
            blend_size=blend_size,
            progress_callback=progress_callback,
        )
    except Exception as e:
        print(f"Erro ao montar mosaico: {e}")
        return None
        
    # Salva o resultado
    output_path = os.path.join(folder, f"{program_name}{output_suffix}.png")
    cv2.imwrite(output_path, mosaic)
    
    return output_path


# =============================================================================
# INTERFACE GRÁFICA (STANDALONE)
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
            self._build_ui()

        def _build_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            v = QVBoxLayout(central)

            # --- Seletor de pasta ---
            grp = QGroupBox("Seleção de Imagens")
            gl = QHBoxLayout(grp)
            self.folder_lbl = QLabel("Nenhuma pasta selecionada")
            sel_btn = QPushButton("Selecionar Pasta")
            sel_btn.clicked.connect(self.on_select_folder)
            gl.addWidget(sel_btn)
            gl.addWidget(self.folder_lbl, 1)
            v.addWidget(grp)

            # --- Configurações de Corte ---
            crop_grp = QGroupBox("Corte de Bordas (Remoção de Distorção)")
            crop_layout = QHBoxLayout(crop_grp)
            crop_layout.addWidget(QLabel("Margem (px):"))
            self.spin_margin = QSpinBox()
            self.spin_margin.setRange(0, 500)
            self.spin_margin.setValue(50)
            self.spin_margin.setToolTip("Pixels a remover de cada borda para eliminar distorção de lente")
            crop_layout.addWidget(self.spin_margin)
            crop_layout.addStretch()
            v.addWidget(crop_grp)

            # --- Ajuste de Pitch ---
            adj = QGroupBox("Ajuste de Pitch (Sobreposição)")
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
            self.spin_dy.setToolTip("Negativo = sobreposição, Positivo = gap")
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
            self.spin_blend.setToolTip("Pixels de transição gradual nas bordas")
            blend_layout.addWidget(self.spin_blend)
            blend_layout.addStretch()
            v.addWidget(blend_grp)

            # --- Orientação ---
            orient_grp = QGroupBox("Orientação")
            orient_layout = QHBoxLayout(orient_grp)
            self.chk_invert = QCheckBox("Origem no canto inferior-esquerdo (inverter linhas)")
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

            # --- Preview ---
            self.preview_lbl = QLabel("Resultado aparecerá aqui")
            self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_lbl.setStyleSheet("border:1px solid gray; background:#f8f8f8;")
            self.preview_lbl.setMinimumHeight(400)
            v.addWidget(self.preview_lbl, 1)

            self.statusBar().showMessage("Selecione a pasta com as imagens capturadas")

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
            invert = self.chk_invert.isChecked()
            
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

            # Exibe preview
            h, w = mosaic.shape[:2]
            qimg = QImage(mosaic.data, w, h, w * 3, QImage.Format.Format_BGR888)
            pix = QPixmap.fromImage(qimg)
            
            # Escala para caber na janela
            max_w, max_h = 1200, 600
            if w > max_w or h > max_h:
                pix = pix.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio)
            self.preview_lbl.setPixmap(pix)
            
            self.statusBar().showMessage(
                f"✅ Mosaico criado: {w}x{h} px ({cols}x{rows} tiles, tile={tw}x{th}). Salvo: {out_name}"
            )


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
