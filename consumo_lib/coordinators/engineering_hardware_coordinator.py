"""
EngineeringHardwareCoordinator - Coordenação de Hardware para Engineering Wizard

Este módulo coordena as operações de hardware (PLC, câmera, fiducial alignment)
necessárias para as abas 3, 4 e 5 do Engineering Wizard.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum

logger = logging.getLogger(__name__)


class HardwareType(Enum):
    """Tipos de hardware disponíveis."""
    CAMERA = "camera"
    PLC = "plc"
    FIDUCIAL_ALIGNER = "fiducial_aligner"


class EngineeringHardwareCoordinator:
    """
    Coordenador de hardware para o Engineering Wizard.

    Centraliza o acesso a hardware (PLC, câmera, fiducial aligner)
    e fornece métodos de alto nível para as abas do wizard.

    Attributes:
        camera_controller: Controller da câmera (opcional)
        plc_controller: Controller do PLC (opcional)
        fiducial_aligner: Alinhador fiducial (opcional)
    """

    def __init__(
        self,
        camera_controller: Optional[Any] = None,
        plc_controller: Optional[Any] = None,
        fiducial_aligner: Optional[Any] = None
    ):
        """Inicializa o coordenador de hardware.

        Args:
            camera_controller: Instância de CameraController (opcional)
            plc_controller: Instância de PLCAxisController (opcional)
            fiducial_aligner: Instância de FiducialAlignment (opcional)
        """
        self.camera_controller = camera_controller
        self.plc_controller = plc_controller
        self.fiducial_aligner = fiducial_aligner

        logger.info("🔧 EngineeringHardwareCoordinator inicializado")
        logger.debug(f"  Camera: {'✅' if camera_controller else '❌'}")
        logger.debug(f"  PLC: {'✅' if plc_controller else '❌'}")
        logger.debug(f"  Fiducial Aligner: {'✅' if fiducial_aligner else '❌'}")

    def is_hardware_ready(self, required: List[HardwareType]) -> Tuple[bool, str]:
        """Verifica se o hardware necessário está disponível.

        Args:
            required: Lista de tipos de hardware necessários

        Returns:
            Tuple[bool, str]: (True, "") se tudo pronto, (False, mensagem) se não
        """
        missing = []

        for hw in required:
            if hw == HardwareType.CAMERA:
                if self.camera_controller is None:
                    missing.append("Câmera")
                elif not getattr(self.camera_controller, 'is_connected', False):
                    missing.append("Câmera (não conectada)")

            elif hw == HardwareType.PLC:
                if self.plc_controller is None:
                    missing.append("PLC")
                elif not getattr(self.plc_controller, 'is_connected', False):
                    missing.append("PLC (não conectado)")

            elif hw == HardwareType.FIDUCIAL_ALIGNER:
                if self.fiducial_aligner is None:
                    missing.append("Fiducial Aligner")

        if missing:
            message = f"Hardware indisponível: {', '.join(missing)}"
            logger.warning(f"⚠️ {message}")
            return False, message

        logger.debug("✅ Hardware verificado e pronto")
        return True, ""

    def capture_fiducial_template(
        self,
        x: float,
        y: float,
        z: float,
        window_size: int = 50
    ) -> Dict[str, Any]:
        """Captura template fiducial em posição XYZ.

        Args:
            x: Posição X em mm
            y: Posição Y em mm
            z: Posição Z em mm
            window_size: Tamanho da janela de captura (px)

        Returns:
            Dict com template capturado:
                - id: int (deve ser definido pelo caller)
                - x, y, z: Posições
                - image: np.ndarray com a imagem
                - window_size: int
                - captured_at: str ISO timestamp

        Raises:
            RuntimeError: Se hardware não disponível
        """
        logger.info(f"🎯 Capturando template fiducial em ({x:.2f}, {y:.2f}, {z:.2f})")

        # Verificar disponibilidade de hardware
        ready, message = self.is_hardware_ready([
            HardwareType.CAMERA,
            HardwareType.PLC
        ])
        if not ready:
            raise RuntimeError(f"Não é possível capturar fiducial: {message}")

        try:
            # Mover PLC para posição
            if self.plc_controller:
                logger.debug(f"  → Movendo PLC para X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
                self.plc_controller.move_absolute('X', x, feed_rate=1000)
                self.plc_controller.move_absolute('Y', y, feed_rate=1000)
                self.plc_controller.move_absolute('Z', z, feed_rate=500)

                # Aguardar movimento completar
                self.plc_controller.wait_for_idle('X')
                self.plc_controller.wait_for_idle('Y')
                self.plc_controller.wait_for_idle('Z')
                logger.debug("  ✅ Movimento completado")

            # Capturar imagem
            if self.camera_controller:
                logger.debug(f"  → Capturando imagem ({window_size}x{window_size})")
                frame = self.camera_controller.capture_frame()

                if frame is None:
                    raise RuntimeError("Falha ao capturar imagem da câmera")

                import numpy as np
                height, width = frame.shape[:2]

                # Extrair região central (window_size x window_size)
                cy, cx = height // 2, width // 2
                half_size = window_size // 2

                template = frame[
                    cy - half_size:cy + half_size,
                    cx - half_size:cx + half_size
                ]

                logger.debug(f"  ✅ Template capturado: {template.shape}")

                from datetime import datetime
                return {
                    'x': x,
                    'y': y,
                    'z': z,
                    'image': template,
                    'window_size': window_size,
                    'captured_at': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"❌ Erro ao capturar template fiducial: {e}")
            raise RuntimeError(f"Erro na captura: {e}")

    def capture_mosaic_grid(
        self,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Captura mosaico via grid automatizado.

        Args:
            config: Configuração do grid com:
                - x1, y1: Canto superior esquerdo (mm)
                - x2, y2: Canto inferior direito (mm)
                - rows: Número de linhas
                - cols: Número de colunas
                - overlap_percent: Sobreposição (%)
                - delay_ms: Delay entre capturas (ms)
                - z_height: Altura Z para captura (mm)

        Returns:
            Dict com resultado:
                - config: Configuração usada
                - images: List[np.ndarray] com imagens capturadas
                - grid_points: List[Tuple] com (x, y) de cada ponto
                - captured_at: str ISO timestamp

        Raises:
            RuntimeError: Se hardware não disponível
        """
        logger.info("🖼️ Iniciando captura de mosaico")

        # Verificar disponibilidade de hardware
        ready, message = self.is_hardware_ready([
            HardwareType.CAMERA,
            HardwareType.PLC
        ])
        if not ready:
            raise RuntimeError(f"Não é possível capturar mosaico: {message}")

        try:
            # Extrair parâmetros
            x1 = config.get('x1', 0.0)
            y1 = config.get('y1', 0.0)
            x2 = config.get('x2', 100.0)
            y2 = config.get('y2', 50.0)
            rows = config.get('rows', 5)
            cols = config.get('cols', 5)
            overlap_percent = config.get('overlap_percent', 10.0)
            delay_ms = config.get('delay_ms', 200)
            z_height = config.get('z_height', 0.0)

            logger.debug(f"  Grid: {rows}x{cols}, Área: ({x1:.1f},{y1:.1f}) → ({x2:.1f},{y2:.1f})")
            logger.debug(f"  Overlap: {overlap_percent}%, Delay: {delay_ms}ms")

            # Calcular pontos do grid
            import numpy as np
            grid_points = []

            # Dimensões do grid
            width_mm = x2 - x1
            height_mm = y2 - y1

            # Espaçamento entre pontos (com sobreposição)
            x_spacing = width_mm / (cols - 1) if cols > 1 else 0
            y_spacing = height_mm / (rows - 1) if rows > 1 else 0

            # Gerar pontos
            for row in range(rows):
                for col in range(cols):
                    x = x1 + col * x_spacing
                    y = y1 + row * y_spacing
                    grid_points.append((x, y))

            logger.debug(f"  {len(grid_points)} pontos calculados")

            # Capturar imagens
            images = []
            import time

            for i, (x, y) in enumerate(grid_points):
                logger.info(f"  📍 [{i+1}/{len(grid_points)}] ({x:.1f}, {y:.1f})")

                # Mover para posição
                if self.plc_controller:
                    self.plc_controller.move_absolute('X', x, feed_rate=2000)
                    self.plc_controller.move_absolute('Y', y, feed_rate=2000)
                    self.plc_controller.move_absolute('Z', z_height, feed_rate=1000)

                    self.plc_controller.wait_for_idle('X')
                    self.plc_controller.wait_for_idle('Y')
                    self.plc_controller.wait_for_idle('Z')

                # Delay para estabilização
                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)

                # Capturar imagem
                if self.camera_controller:
                    frame = self.camera_controller.capture_frame()
                    if frame is not None:
                        images.append(frame)
                    else:
                        logger.warning(f"  ⚠️ Falha ao capturar frame {i+1}")

            logger.info(f"✅ Mosaico capturado: {len(images)} imagens")

            from datetime import datetime
            return {
                'config': config,
                'images': images,
                'grid_points': grid_points,
                'total_points': len(grid_points),
                'captured_count': len(images),
                'captured_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Erro ao capturar mosaico: {e}")
            raise RuntimeError(f"Erro na captura do mosaico: {e}")

    def perform_fiducial_alignment(
        self,
        fiducial_templates: List[Dict[str, Any]],
        mosaic_image: Any
    ) -> Dict[str, Any]:
        """Executa alinhamento fiducial usando templates e mosaico.

        Args:
            fiducial_templates: Lista de templates fiduciais (2 mínimo)
                Cada template deve ter: image, x, y, z, window_size
            mosaic_image: Imagem do mosaico capturado

        Returns:
            Dict com transformação:
                - tx: Translação X (mm)
                - ty: Translação Y (mm)
                - angle: Rotação (graus)
                - scale: Escala (fator)
                - scores: List[float] com scores de matching
                - matched_positions: List[Tuple] com (x, y) encontrados

        Raises:
            RuntimeError: Se hardware não disponível ou fiduciais insuficientes
        """
        logger.info("🔧 Iniciando alinhamento fiducial")

        # Verificar fiduciais
        if len(fiducial_templates) < 2:
            raise RuntimeError(f"Mínimo de 2 fiduciais necessário, recebido: {len(fiducial_templates)}")

        # Verificar disponibilidade de hardware
        ready, message = self.is_hardware_ready([HardwareType.FIDUCIAL_ALIGNER])
        if not ready:
            logger.warning(f"⚠️ {message}")
            logger.info("ℹ️ Continuando sem FiducialAligner (usando OpenCV)")

        try:
            import cv2
            import numpy as np

            # Converter imagens para grayscale se necessário
            templates_gray = []
            for template in fiducial_templates:
                img = template['image']
                if len(img.shape) == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                templates_gray.append(img)

            mosaic_gray = mosaic_image
            if len(mosaic_gray.shape) == 3:
                mosaic_gray = cv2.cvtColor(mosaic_gray, cv2.COLOR_BGR2GRAY)

            matched_positions = []
            scores = []

            # Executar template matching para cada fiducial
            for i, template in enumerate(templates_gray):
                logger.info(f"  🔍 Procurando fiducial {i+1}/{len(templates_gray)}")

                # Template matching
                result = cv2.matchTemplate(mosaic_gray, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                # Calcular centro do template
                template_h, template_w = template.shape
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2

                matched_positions.append((center_x, center_y))
                scores.append(max_val)

                logger.info(f"    ✅ Encontrado em ({center_x}, {center_y}), score: {max_val:.3f}")

            # Calcular transformação (simplificada - assume translação + rotação)
            if len(matched_positions) >= 2:
                # Posições esperadas (do template)
                expected_pts = np.array([
                    [t['x'], t['y']]
                    for t in fiducial_templates[:len(matched_positions)]
                ], dtype=np.float32)

                # Posições encontradas (no mosaico)
                found_pts = np.array(matched_positions, dtype=np.float32)

                # Calcular translação média
                tx = np.mean(found_pts[:, 0] - expected_pts[:, 0])
                ty = np.mean(found_pts[:, 1] - expected_pts[:, 1])

                # Calcular rotação (aproximada)
                if len(matched_positions) >= 2:
                    # Vetor esperado
                    dx_exp = expected_pts[1][0] - expected_pts[0][0]
                    dy_exp = expected_pts[1][1] - expected_pts[0][1]
                    angle_exp = np.arctan2(dy_exp, dx_exp)

                    # Vetor encontrado
                    dx_found = found_pts[1][0] - found_pts[0][0]
                    dy_found = found_pts[1][1] - found_pts[0][1]
                    angle_found = np.arctan2(dy_found, dx_found)

                    # Diferença de ângulo em graus
                    angle_diff = np.degrees(angle_found - angle_exp)
                else:
                    angle_diff = 0.0

                # Escala (aproximada)
                dist_exp = np.sqrt(dx_exp**2 + dy_exp**2)
                dist_found = np.sqrt(dx_found**2 + dy_found**2)
                scale = dist_found / dist_exp if dist_exp > 0 else 1.0

                logger.info(f"✅ Alinhamento concluído:")
                logger.info(f"   Translação: tx={tx:.2f} px, ty={ty:.2f} px")
                logger.info(f"   Rotação: {angle_diff:.2f}°")
                logger.info(f"   Escala: {scale:.3f}")
                logger.info(f"   Scores: {[f'{s:.3f}' for s in scores]}")

                from datetime import datetime
                return {
                    'tx': tx,
                    'ty': ty,
                    'angle': angle_diff,
                    'scale': scale,
                    'scores': scores,
                    'matched_positions': matched_positions,
                    'average_score': np.mean(scores),
                    'aligned_at': datetime.now().isoformat()
                }
            else:
                raise RuntimeError("Insuficient fiduciais matched para calcular transformação")

        except Exception as e:
            logger.error(f"❌ Erro no alinhamento fiducial: {e}")
            raise RuntimeError(f"Erro no alinhamento: {e}")

    def move_to_position(self, x: float, y: float, z: float) -> bool:
        """Move PLC para posição XYZ.

        Args:
            x: Posição X em mm
            y: Posição Y em mm
            z: Posição Z em mm

        Returns:
            bool: True se movimento bem-sucedido
        """
        logger.debug(f"📍 Movendo para ({x:.2f}, {y:.2f}, {z:.2f})")

        ready, _ = self.is_hardware_ready([HardwareType.PLC])
        if not ready:
            return False

        try:
            if self.plc_controller:
                self.plc_controller.move_absolute('X', x)
                self.plc_controller.move_absolute('Y', y)
                self.plc_controller.move_absolute('Z', z)

                self.plc_controller.wait_for_idle('X')
                self.plc_controller.wait_for_idle('Y')
                self.plc_controller.wait_for_idle('Z')

                logger.debug("  ✅ Movimento completado")
                return True
        except Exception as e:
            logger.error(f"  ❌ Erro no movimento: {e}")
            return False

    def capture_current_frame(self) -> Optional[Any]:
        """Captura frame atual da câmera.

        Returns:
            np.ndarray ou None se falhar
        """
        ready, _ = self.is_hardware_ready([HardwareType.CAMERA])
        if not ready:
            return None

        try:
            if self.camera_controller:
                return self.camera_controller.capture_frame()
        except Exception as e:
            logger.error(f"❌ Erro ao capturar frame: {e}")

        return None

    def get_current_position(self) -> Dict[str, float]:
        """Retorna posição atual do PLC.

        Returns:
            Dict com 'x', 'y', 'z' em mm (0 se não disponível)
        """
        position = {'x': 0.0, 'y': 0.0, 'z': 0.0}

        ready, _ = self.is_hardware_ready([HardwareType.PLC])
        if not ready:
            return position

        try:
            if self.plc_controller:
                position['x'] = self.plc_controller.read_position('X')
                position['y'] = self.plc_controller.read_position('Y')
                position['z'] = self.plc_controller.read_position('Z')
        except Exception as e:
            logger.error(f"❌ Erro ao ler posição: {e}")

        return position
