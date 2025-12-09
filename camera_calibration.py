"""
camera_calibration.py
---------------------
Módulo para calibração de câmera e correção de distorção.

Funcionalidades:
  - Captura de imagens de padrão de calibração (tabuleiro de xadrez)
  - Cálculo da matriz intrínseca e coeficientes de distorção
  - Correção de distorção em imagens
  - Salvamento/carregamento de parâmetros de calibração

Uso:
    from camera_calibration import CameraCalibrator, undistort_image
    
    # Calibração
    calibrator = CameraCalibrator()
    calibrator.add_calibration_image(img)
    success = calibrator.calibrate()
    calibrator.save("camera_calibration.json")
    
    # Correção
    corrected = undistort_image(img, "camera_calibration.json")
"""

import os
import json
import cv2
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
import logging

log = logging.getLogger(__name__)


class CameraCalibrator:
    """
    Classe para calibração de câmera usando padrão de tabuleiro de xadrez.
    """
    
    def __init__(self, pattern_size: Tuple[int, int] = (9, 6), square_size_mm: float = 25.0):
        """
        Inicializa o calibrador.
        
        Args:
            pattern_size: Número de cantos internos (colunas, linhas)
            square_size_mm: Tamanho do quadrado em mm
        """
        self.pattern_size = pattern_size
        self.square_size_mm = square_size_mm
        
        # Pontos 3D do padrão (Z=0 pois é plano)
        self.objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
        self.objp *= square_size_mm
        
        # Listas para armazenar pontos
        self.obj_points: List[np.ndarray] = []  # Pontos 3D no mundo
        self.img_points: List[np.ndarray] = []  # Pontos 2D na imagem
        self.image_size: Optional[Tuple[int, int]] = None
        
        # Resultados da calibração
        self.camera_matrix: Optional[np.ndarray] = None
        self.dist_coeffs: Optional[np.ndarray] = None
        self.rvecs: Optional[List[np.ndarray]] = None
        self.tvecs: Optional[List[np.ndarray]] = None
        self.rms_error: float = 0.0
        
        # Mapas para undistort otimizado
        self._map1: Optional[np.ndarray] = None
        self._map2: Optional[np.ndarray] = None
        
    def add_calibration_image(self, image: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Adiciona uma imagem de calibração.
        
        Args:
            image: Imagem BGR com o padrão de tabuleiro
            
        Returns:
            (sucesso, imagem_com_cantos_marcados)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        self.image_size = (gray.shape[1], gray.shape[0])
        
        # Encontra os cantos do tabuleiro
        flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE
        ret, corners = cv2.findChessboardCorners(gray, self.pattern_size, flags)
        
        if ret:
            # Refina os cantos com precisão sub-pixel
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners_refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            
            self.obj_points.append(self.objp)
            self.img_points.append(corners_refined)
            
            # Desenha os cantos na imagem
            img_with_corners = image.copy()
            cv2.drawChessboardCorners(img_with_corners, self.pattern_size, corners_refined, ret)
            
            log.info(f"Padrão encontrado! Total de imagens: {len(self.obj_points)}")
            return True, img_with_corners
        else:
            log.warning("Padrão de tabuleiro não encontrado na imagem")
            return False, None
    
    def clear_calibration_images(self):
        """Remove todas as imagens de calibração."""
        self.obj_points.clear()
        self.img_points.clear()
        self._map1 = None
        self._map2 = None
        
    def get_image_count(self) -> int:
        """Retorna o número de imagens de calibração."""
        return len(self.obj_points)
    
    def calibrate(self) -> bool:
        """
        Executa a calibração da câmera.
        
        Returns:
            True se a calibração foi bem-sucedida
        """
        if len(self.obj_points) < 5:
            log.error(f"Precisamos de pelo menos 5 imagens para calibração. Temos: {len(self.obj_points)}")
            return False
            
        if self.image_size is None:
            log.error("Tamanho da imagem não definido")
            return False
        
        log.info(f"Iniciando calibração com {len(self.obj_points)} imagens...")
        
        try:
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
                self.obj_points,
                self.img_points,
                self.image_size,
                None,
                None,
                flags=cv2.CALIB_RATIONAL_MODEL
            )
            
            if ret:
                self.camera_matrix = mtx
                self.dist_coeffs = dist
                self.rvecs = rvecs
                self.tvecs = tvecs
                self.rms_error = ret
                
                # Pré-calcula mapas de undistort
                self._compute_undistort_maps()
                
                log.info(f"Calibração concluída! Erro RMS: {ret:.4f}")
                return True
            else:
                log.error("Calibração falhou")
                return False
                
        except cv2.error as e:
            log.error(f"Erro OpenCV durante calibração: {e}")
            return False
            
    def _compute_undistort_maps(self):
        """Pré-calcula mapas para undistort otimizado."""
        if self.camera_matrix is None or self.dist_coeffs is None:
            return
            
        # Obtém matriz de câmera otimizada
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
            self.camera_matrix,
            self.dist_coeffs,
            self.image_size,
            alpha=0,  # 0 = corta pixels inválidos, 1 = mantém tudo
            newImgSize=self.image_size
        )
        
        # Calcula mapas de remapeamento
        self._map1, self._map2 = cv2.initUndistortRectifyMap(
            self.camera_matrix,
            self.dist_coeffs,
            None,
            new_camera_matrix,
            self.image_size,
            cv2.CV_32FC1
        )
        
        self._roi = roi
        self._new_camera_matrix = new_camera_matrix
        
    def undistort(self, image: np.ndarray, crop: bool = True) -> np.ndarray:
        """
        Remove distorção de uma imagem.
        
        Args:
            image: Imagem a ser corrigida
            crop: Se True, recorta para região válida
            
        Returns:
            Imagem corrigida
        """
        if self._map1 is None or self._map2 is None:
            if self.camera_matrix is not None:
                self._compute_undistort_maps()
            else:
                log.warning("Calibração não disponível, retornando imagem original")
                return image
        
        # Aplica remapeamento (mais rápido que cv2.undistort)
        dst = cv2.remap(image, self._map1, self._map2, cv2.INTER_LINEAR)
        
        if crop and hasattr(self, '_roi'):
            x, y, w, h = self._roi
            if w > 0 and h > 0:
                dst = dst[y:y+h, x:x+w]
                
        return dst
    
    def save(self, filepath: str):
        """
        Salva parâmetros de calibração em arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo
        """
        if self.camera_matrix is None:
            raise ValueError("Calibração não realizada")
            
        data = {
            "image_size": list(self.image_size),
            "camera_matrix": self.camera_matrix.tolist(),
            "dist_coeffs": self.dist_coeffs.tolist(),
            "rms_error": self.rms_error,
            "pattern_size": list(self.pattern_size),
            "square_size_mm": self.square_size_mm,
            "num_calibration_images": len(self.obj_points)
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        log.info(f"Calibração salva em: {filepath}")
        
    def load(self, filepath: str) -> bool:
        """
        Carrega parâmetros de calibração de arquivo JSON.
        
        Args:
            filepath: Caminho do arquivo
            
        Returns:
            True se carregou com sucesso
        """
        if not os.path.exists(filepath):
            log.error(f"Arquivo não encontrado: {filepath}")
            return False
            
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                
            self.image_size = tuple(data["image_size"])
            self.camera_matrix = np.array(data["camera_matrix"])
            self.dist_coeffs = np.array(data["dist_coeffs"])
            self.rms_error = data.get("rms_error", 0.0)
            self.pattern_size = tuple(data.get("pattern_size", [9, 6]))
            self.square_size_mm = data.get("square_size_mm", 25.0)
            
            # Recalcula mapas
            self._compute_undistort_maps()
            
            log.info(f"Calibração carregada de: {filepath}")
            return True
            
        except Exception as e:
            log.error(f"Erro ao carregar calibração: {e}")
            return False
            
    def get_fov_mm(self, distance_mm: float) -> Tuple[float, float]:
        """
        Calcula o campo de visão em mm para uma dada distância.
        
        Args:
            distance_mm: Distância do objeto à câmera em mm
            
        Returns:
            (largura_mm, altura_mm) do campo de visão
        """
        if self.camera_matrix is None or self.image_size is None:
            raise ValueError("Calibração não disponível")
            
        fx = self.camera_matrix[0, 0]  # Focal length X em pixels
        fy = self.camera_matrix[1, 1]  # Focal length Y em pixels
        
        width_px, height_px = self.image_size
        
        # FOV = (tamanho_sensor_px / focal_length_px) * distância
        fov_width_mm = (width_px / fx) * distance_mm
        fov_height_mm = (height_px / fy) * distance_mm
        
        return fov_width_mm, fov_height_mm


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def undistort_image(image: np.ndarray, calibration_file: str, crop: bool = True) -> np.ndarray:
    """
    Função de conveniência para corrigir distorção de uma imagem.
    
    Args:
        image: Imagem BGR
        calibration_file: Caminho do arquivo de calibração JSON
        crop: Se True, recorta para região válida
        
    Returns:
        Imagem corrigida
    """
    calibrator = CameraCalibrator()
    if calibrator.load(calibration_file):
        return calibrator.undistort(image, crop)
    else:
        return image


def generate_checkerboard_pattern(
    cols: int = 9,
    rows: int = 6,
    square_size_px: int = 100,
    output_path: str = "checkerboard.png"
) -> str:
    """
    Gera uma imagem de padrão de tabuleiro para impressão.
    
    Args:
        cols: Número de colunas
        rows: Número de linhas
        square_size_px: Tamanho de cada quadrado em pixels
        output_path: Caminho para salvar a imagem
        
    Returns:
        Caminho do arquivo gerado
    """
    # Adiciona margem
    margin = square_size_px
    width = cols * square_size_px + 2 * margin
    height = rows * square_size_px + 2 * margin
    
    # Cria imagem branca
    img = np.ones((height, width), dtype=np.uint8) * 255
    
    # Desenha quadrados pretos
    for i in range(rows):
        for j in range(cols):
            if (i + j) % 2 == 0:
                x1 = margin + j * square_size_px
                y1 = margin + i * square_size_px
                x2 = x1 + square_size_px
                y2 = y1 + square_size_px
                img[y1:y2, x1:x2] = 0
                
    cv2.imwrite(output_path, img)
    log.info(f"Padrão de calibração salvo: {output_path}")
    return output_path


# =============================================================================
# INTERFACE GRÁFICA
# =============================================================================

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QSpinBox, QDoubleSpinBox, QGroupBox,
        QMessageBox, QFileDialog, QProgressBar,
    )
    from PyQt6.QtGui import QPixmap, QImage
    from PyQt6.QtCore import Qt, QTimer
    HAS_PYQT = True
except ImportError:
    HAS_PYQT = False


if HAS_PYQT:
    class CameraCalibrationDialog(QMainWindow):
        """Interface gráfica para calibração de câmera."""
        
        def __init__(self, camera_controller=None, parent=None):
            super().__init__(parent)
            self.setWindowTitle("Calibração de Câmera - Correção de Distorção")
            self.camera = camera_controller
            self.calibrator = CameraCalibrator()
            self._build_ui()
            
            # Timer para preview
            self.preview_timer = QTimer(self)
            self.preview_timer.timeout.connect(self._update_preview)
            
        def _build_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            
            # Instruções
            instructions = QLabel(
                "📋 <b>Instruções de Calibração:</b><br>"
                "1. Imprima um padrão de tabuleiro de xadrez (9×6 cantos internos)<br>"
                "2. Posicione o padrão em diferentes ângulos e distâncias<br>"
                "3. Capture pelo menos 10-15 imagens boas<br>"
                "4. Clique em 'Calibrar' quando tiver imagens suficientes"
            )
            instructions.setWordWrap(True)
            layout.addWidget(instructions)
            
            # Configurações do padrão
            pattern_group = QGroupBox("Configurações do Padrão")
            pattern_layout = QHBoxLayout(pattern_group)
            
            pattern_layout.addWidget(QLabel("Cantos (colunas):"))
            self.spin_cols = QSpinBox()
            self.spin_cols.setRange(4, 20)
            self.spin_cols.setValue(9)
            pattern_layout.addWidget(self.spin_cols)
            
            pattern_layout.addWidget(QLabel("Cantos (linhas):"))
            self.spin_rows = QSpinBox()
            self.spin_rows.setRange(4, 20)
            self.spin_rows.setValue(6)
            pattern_layout.addWidget(self.spin_rows)
            
            pattern_layout.addWidget(QLabel("Tamanho quadrado (mm):"))
            self.spin_square = QDoubleSpinBox()
            self.spin_square.setRange(1, 100)
            self.spin_square.setValue(25.0)
            pattern_layout.addWidget(self.spin_square)
            
            btn_print = QPushButton("Gerar Padrão para Impressão")
            btn_print.clicked.connect(self._generate_pattern)
            pattern_layout.addWidget(btn_print)
            
            layout.addWidget(pattern_group)
            
            # Preview
            self.preview_label = QLabel("Preview da Câmera")
            self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.preview_label.setMinimumSize(640, 480)
            self.preview_label.setStyleSheet("background: #333; border: 1px solid #666;")
            layout.addWidget(self.preview_label)
            
            # Status
            self.status_label = QLabel("Imagens capturadas: 0")
            layout.addWidget(self.status_label)
            
            # Barra de progresso (para calibração)
            self.progress = QProgressBar()
            self.progress.setVisible(False)
            layout.addWidget(self.progress)
            
            # Botões de ação
            btn_layout = QHBoxLayout()
            
            self.btn_preview = QPushButton("▶ Iniciar Preview")
            self.btn_preview.clicked.connect(self._toggle_preview)
            btn_layout.addWidget(self.btn_preview)
            
            self.btn_capture = QPushButton("📷 Capturar Imagem")
            self.btn_capture.clicked.connect(self._capture_image)
            self.btn_capture.setEnabled(False)
            btn_layout.addWidget(self.btn_capture)
            
            self.btn_clear = QPushButton("🗑 Limpar")
            self.btn_clear.clicked.connect(self._clear_images)
            btn_layout.addWidget(self.btn_clear)
            
            layout.addLayout(btn_layout)
            
            # Botões de calibração
            calib_layout = QHBoxLayout()
            
            self.btn_calibrate = QPushButton("🔧 Calibrar Câmera")
            self.btn_calibrate.clicked.connect(self._run_calibration)
            calib_layout.addWidget(self.btn_calibrate)
            
            self.btn_save = QPushButton("💾 Salvar Calibração")
            self.btn_save.clicked.connect(self._save_calibration)
            self.btn_save.setEnabled(False)
            calib_layout.addWidget(self.btn_save)
            
            self.btn_load = QPushButton("📂 Carregar Calibração")
            self.btn_load.clicked.connect(self._load_calibration)
            calib_layout.addWidget(self.btn_load)
            
            layout.addLayout(calib_layout)
            
            # Resultado
            self.result_label = QLabel("")
            layout.addWidget(self.result_label)
            
        def _generate_pattern(self):
            """Gera padrão de calibração para impressão."""
            cols = self.spin_cols.value()
            rows = self.spin_rows.value()
            
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Salvar Padrão de Calibração",
                f"checkerboard_{cols}x{rows}.png",
                "Imagens PNG (*.png)"
            )
            
            if filepath:
                generate_checkerboard_pattern(cols, rows, 100, filepath)
                QMessageBox.information(
                    self, "Padrão Gerado",
                    f"Padrão de calibração salvo em:\n{filepath}\n\n"
                    f"Imprima este padrão e cole em uma superfície plana e rígida."
                )
                
        def _toggle_preview(self):
            """Liga/desliga preview da câmera."""
            if self.preview_timer.isActive():
                self.preview_timer.stop()
                self.btn_preview.setText("▶ Iniciar Preview")
                self.btn_capture.setEnabled(False)
            else:
                if self.camera is None or not hasattr(self.camera, 'capture'):
                    QMessageBox.warning(self, "Erro", "Câmera não disponível")
                    return
                self.preview_timer.start(50)  # 20 FPS
                self.btn_preview.setText("⏹ Parar Preview")
                self.btn_capture.setEnabled(True)
                
        def _update_preview(self):
            """Atualiza preview da câmera."""
            if self.camera is None:
                return
                
            try:
                frame = self.camera.capture()
                if frame is None:
                    return
                    
                # Tenta encontrar padrão
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                pattern_size = (self.spin_cols.value(), self.spin_rows.value())
                ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)
                
                if ret:
                    cv2.drawChessboardCorners(frame, pattern_size, corners, ret)
                    
                # Converte para QImage
                h, w = frame.shape[:2]
                bytes_per_line = 3 * w
                qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
                pixmap = QPixmap.fromImage(qimg)
                
                # Escala para caber no label
                scaled = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled)
                
            except Exception as e:
                pass
                
        def _capture_image(self):
            """Captura imagem para calibração."""
            if self.camera is None:
                return
                
            frame = self.camera.capture()
            if frame is None:
                QMessageBox.warning(self, "Erro", "Falha ao capturar imagem")
                return
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Primeiro tenta com o tamanho configurado
            target_cols = self.spin_cols.value()
            target_rows = self.spin_rows.value()
            pattern_size = (target_cols, target_rows)
            
            flags = cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK
            ret, corners = cv2.findChessboardCorners(gray, pattern_size, flags)
            
            if ret:
                # Atualiza padrão no calibrador
                self.calibrator.pattern_size = pattern_size
                self.calibrator.square_size_mm = self.spin_square.value()
                # Recalcula objp com novo tamanho
                self.calibrator.objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
                self.calibrator.objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
                self.calibrator.objp *= self.spin_square.value()
                
                success, img_with_corners = self.calibrator.add_calibration_image(frame)
                
                if success:
                    self.status_label.setText(f"Imagens capturadas: {self.calibrator.get_image_count()}")
                    QMessageBox.information(self, "Sucesso", 
                        f"Padrão {target_cols}×{target_rows} detectado e adicionado!")
                    return
            
            # Se não encontrou, tenta tamanhos menores automaticamente
            found_size = None
            for cols in range(target_cols, 3, -1):
                for rows in range(target_rows, 3, -1):
                    test_size = (cols, rows)
                    ret, corners = cv2.findChessboardCorners(gray, test_size, flags)
                    if ret:
                        found_size = test_size
                        break
                if found_size:
                    break
            
            if found_size:
                # Pergunta ao usuário se quer usar o tamanho encontrado
                reply = QMessageBox.question(
                    self, "Padrão Menor Encontrado",
                    f"O padrão {target_cols}×{target_rows} não foi encontrado, mas\n"
                    f"foi detectado um padrão de {found_size[0]}×{found_size[1]}.\n\n"
                    f"Isso pode acontecer se:\n"
                    f"- O tabuleiro está parcialmente cortado\n"
                    f"- O número de cantos configurado está incorreto\n\n"
                    f"Deseja ajustar para {found_size[0]}×{found_size[1]} e tentar novamente?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.spin_cols.setValue(found_size[0])
                    self.spin_rows.setValue(found_size[1])
                    self._capture_image()  # Tenta novamente com novo tamanho
                    return
            
            # Nenhum padrão encontrado
            QMessageBox.warning(
                self, "Padrão Não Encontrado",
                f"Não foi possível encontrar o padrão de tabuleiro.\n\n"
                f"Certifique-se de que:\n"
                f"• O padrão está TOTALMENTE visível na imagem\n"
                f"• O número de cantos está correto ({target_cols}×{target_rows})\n"
                f"• A iluminação está adequada (sem reflexos)\n"
                f"• A imagem está em foco\n\n"
                f"Dica: Conte os cantos internos do tabuleiro\n"
                f"(onde 4 quadrados se encontram) e ajuste os valores."
            )
                
        def _clear_images(self):
            """Limpa imagens de calibração."""
            self.calibrator.clear_calibration_images()
            self.status_label.setText("Imagens capturadas: 0")
            self.btn_save.setEnabled(False)
            self.result_label.setText("")
            
        def _run_calibration(self):
            """Executa calibração."""
            if self.calibrator.get_image_count() < 5:
                QMessageBox.warning(
                    self, "Imagens Insuficientes",
                    f"Precisamos de pelo menos 5 imagens. Você tem: {self.calibrator.get_image_count()}"
                )
                return
                
            self.progress.setVisible(True)
            self.progress.setRange(0, 0)  # Indeterminado
            QApplication.processEvents()
            
            success = self.calibrator.calibrate()
            
            self.progress.setVisible(False)
            
            if success:
                self.btn_save.setEnabled(True)
                
                # Mostra resultado
                fx = self.calibrator.camera_matrix[0, 0]
                fy = self.calibrator.camera_matrix[1, 1]
                cx = self.calibrator.camera_matrix[0, 2]
                cy = self.calibrator.camera_matrix[1, 2]
                
                self.result_label.setText(
                    f"<b>✅ Calibração Concluída!</b><br>"
                    f"Erro RMS: {self.calibrator.rms_error:.4f} pixels<br>"
                    f"Focal Length: fx={fx:.1f}, fy={fy:.1f} pixels<br>"
                    f"Centro Óptico: ({cx:.1f}, {cy:.1f})"
                )
                
                QMessageBox.information(
                    self, "Calibração Concluída",
                    f"Calibração realizada com sucesso!\n\n"
                    f"Erro RMS: {self.calibrator.rms_error:.4f} pixels\n"
                    f"(Valores abaixo de 1.0 são excelentes)"
                )
            else:
                QMessageBox.critical(self, "Erro", "Falha na calibração")
                
        def _save_calibration(self):
            """Salva calibração em arquivo."""
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Salvar Calibração",
                "camera_calibration.json",
                "Arquivos JSON (*.json)"
            )
            
            if filepath:
                self.calibrator.save(filepath)
                QMessageBox.information(self, "Salvo", f"Calibração salva em:\n{filepath}")
                
        def _load_calibration(self):
            """Carrega calibração de arquivo."""
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Carregar Calibração",
                "",
                "Arquivos JSON (*.json)"
            )
            
            if filepath and self.calibrator.load(filepath):
                self.btn_save.setEnabled(True)
                
                fx = self.calibrator.camera_matrix[0, 0]
                fy = self.calibrator.camera_matrix[1, 1]
                
                self.result_label.setText(
                    f"<b>📂 Calibração Carregada</b><br>"
                    f"Erro RMS: {self.calibrator.rms_error:.4f}<br>"
                    f"Focal Length: fx={fx:.1f}, fy={fy:.1f}"
                )
                
                QMessageBox.information(self, "Carregado", "Calibração carregada com sucesso!")
                
        def closeEvent(self, event):
            """Para o preview ao fechar."""
            self.preview_timer.stop()
            event.accept()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if HAS_PYQT:
        # Cria uma câmera mock para teste
        class MockCamera:
            def __init__(self):
                self.cap = cv2.VideoCapture(0)
            def capture(self):
                ret, frame = self.cap.read()
                return frame if ret else None
                
        app = QApplication(sys.argv)
        camera = MockCamera()
        win = CameraCalibrationDialog(camera)
        win.resize(800, 700)
        win.show()
        sys.exit(app.exec())
    else:
        print("PyQt6 não disponível. Use as funções programaticamente.")
