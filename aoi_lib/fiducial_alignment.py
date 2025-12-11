"""
fiducial_alignment.py
---------------------
Módulo de alinhamento de fiduciais para inspeção de stencil.

Este módulo implementa:
- Captura e armazenamento de templates de fiduciais
- Busca de fiduciais em imagens usando template matching
- Cálculo de transformação (translação, rotação, escala) baseado em 2+ fiduciais
- Interface para alinhamento manual/semi-automático do Gerber sobre a imagem

Diferenças da implementação da Adesivadora:
- Na Adesivadora: fiducial corrige offset em tempo real para aplicação de dots
- No Stencil AOI: fiducial alinha o Gerber sobre a imagem capturada do mosaico

Workflow esperado:
1. Usuário define fiduciais no editor Gerber (marca posições A e B)
2. Sistema captura mosaico do stencil
3. Usuário posiciona Gerber aproximadamente sobre a imagem (drag & drop)
4. Sistema busca fiduciais automaticamente dentro de região de busca
5. Sistema calcula transformação (translação, rotação, escala)
6. Usuário pode ajustar manualmente se necessário
7. Transformação é aplicada a todas as aberturas do Gerber
"""

import cv2
import numpy as np
import base64
import math
import logging
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

log = logging.getLogger(__name__)


# ============================================================================
#  DATACLASSES PARA CONFIGURAÇÃO E RESULTADOS
# ============================================================================

@dataclass
class FiducialTemplate:
    """Template de um fiducial capturado."""
    name: str                           # Nome identificador (ex: "Fiducial A", "Fiducial B")
    template_gray: np.ndarray = None    # Imagem grayscale do template
    template_bgr: np.ndarray = None     # Imagem BGR original (para visualização)
    window_size: int = 50               # Tamanho da janela de captura (pixels)
    search_radius: int = 100            # Raio de busca ao redor da posição esperada
    threshold: float = 70.0             # Similaridade mínima para aceitar match (0-100)
    
    # Posição no Gerber (coordenadas do arquivo Gerber em mm ou unidades nativas)
    gerber_x: float = 0.0
    gerber_y: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário (para salvar em JSON)."""
        result = {
            "name": self.name,
            "window_size": self.window_size,
            "search_radius": self.search_radius,
            "threshold": self.threshold,
            "gerber_x": self.gerber_x,
            "gerber_y": self.gerber_y,
        }
        # Salva template como PNG base64
        if self.template_bgr is not None:
            _, png_bytes = cv2.imencode(".png", self.template_bgr)
            result["template_png_b64"] = base64.b64encode(png_bytes).decode("utf-8")
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FiducialTemplate":
        """Deserializa de dicionário."""
        fid = cls(
            name=data.get("name", "Fiducial"),
            window_size=data.get("window_size", 50),
            search_radius=data.get("search_radius", 100),
            threshold=data.get("threshold", 70.0),
            gerber_x=data.get("gerber_x", 0.0),
            gerber_y=data.get("gerber_y", 0.0),
        )
        # Decodifica template de base64
        if "template_png_b64" in data:
            png_bytes = base64.b64decode(data["template_png_b64"])
            img = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                fid.template_bgr = img
                fid.template_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return fid


@dataclass
class FiducialMatchResult:
    """Resultado da busca de um fiducial."""
    found: bool = False             # Se o fiducial foi encontrado
    similarity: float = 0.0         # Percentual de similaridade (0-100)
    image_x: float = 0.0            # Posição X encontrada na imagem (pixels)
    image_y: float = 0.0            # Posição Y encontrada na imagem (pixels)
    offset_x: float = 0.0           # Deslocamento X do centro esperado (pixels)
    offset_y: float = 0.0           # Deslocamento Y do centro esperado (pixels)
    match_rect: Tuple[int, int, int, int] = (0, 0, 0, 0)  # (x, y, w, h) do retângulo match


@dataclass
class AlignmentTransform:
    """Transformação calculada a partir dos fiduciais.
    
    Representa a transformação afim necessária para alinhar o Gerber com a imagem:
    - Translação (tx, ty)
    - Rotação (angle em graus)
    - Escala (scale_x, scale_y) - geralmente iguais
    """
    tx: float = 0.0                 # Translação X (pixels)
    ty: float = 0.0                 # Translação Y (pixels)
    angle: float = 0.0              # Ângulo de rotação (graus)
    scale_x: float = 1.0            # Escala X
    scale_y: float = 1.0            # Escala Y
    
    # Centro de rotação (para rotações ao redor de um ponto específico)
    center_x: float = 0.0
    center_y: float = 0.0
    
    # Matriz de transformação 3x3 (homografia) calculada
    matrix: Optional[np.ndarray] = None
    
    def get_affine_matrix(self) -> np.ndarray:
        """Retorna matriz de transformação afim 2x3."""
        if self.matrix is not None and self.matrix.shape == (3, 3):
            # Extrai os primeiros 2 linhas da homografia
            return self.matrix[:2, :]
        
        # Constrói matriz a partir dos parâmetros
        cos_a = math.cos(math.radians(self.angle))
        sin_a = math.sin(math.radians(self.angle))
        
        # Matriz: rotação + escala + translação
        # [sx*cos  -sy*sin  tx]
        # [sx*sin   sy*cos  ty]
        matrix = np.array([
            [self.scale_x * cos_a, -self.scale_y * sin_a, self.tx],
            [self.scale_x * sin_a,  self.scale_y * cos_a, self.ty]
        ], dtype=np.float64)
        
        return matrix
    
    def apply_to_point(self, x: float, y: float) -> Tuple[float, float]:
        """Aplica transformação a um ponto (x, y)."""
        m = self.get_affine_matrix()
        point = np.array([x, y, 1.0])
        transformed = m @ point
        return float(transformed[0]), float(transformed[1])
    
    def apply_to_points(self, points: np.ndarray) -> np.ndarray:
        """Aplica transformação a array de pontos Nx2."""
        if points.shape[0] == 0:
            return points
        
        m = self.get_affine_matrix()
        # Adiciona coluna de 1s para multiplicação homogênea
        ones = np.ones((points.shape[0], 1))
        points_h = np.hstack([points, ones])
        transformed = (m @ points_h.T).T
        return transformed


# ============================================================================
#  CLASSE PRINCIPAL DE ALINHAMENTO DE FIDUCIAIS
# ============================================================================

class FiducialAligner:
    """
    Classe principal para alinhamento de fiduciais.
    
    Responsabilidades:
    - Armazenar templates de fiduciais (A e B)
    - Buscar fiduciais em imagens usando template matching
    - Calcular transformação (translação, rotação, escala) baseado nos fiduciais encontrados
    - Permitir ajuste manual da transformação
    """
    
    def __init__(self):
        self.fiducials: List[FiducialTemplate] = []
        self.last_results: List[FiducialMatchResult] = []
        self.transform: Optional[AlignmentTransform] = None
        
        # Parâmetros padrão
        self.default_window_size = 50
        self.default_search_radius = 100
        self.default_threshold = 70.0
    
    # -------------------------------------------------------------------------
    #  GERENCIAMENTO DE FIDUCIAIS
    # -------------------------------------------------------------------------
    
    def add_fiducial(self, name: str, gerber_x: float, gerber_y: float) -> FiducialTemplate:
        """Adiciona um novo fiducial na lista."""
        fid = FiducialTemplate(
            name=name,
            gerber_x=gerber_x,
            gerber_y=gerber_y,
            window_size=self.default_window_size,
            search_radius=self.default_search_radius,
            threshold=self.default_threshold
        )
        self.fiducials.append(fid)
        log.info(f"Fiducial '{name}' adicionado em ({gerber_x}, {gerber_y})")
        return fid
    
    def remove_fiducial(self, name: str) -> bool:
        """Remove fiducial pelo nome."""
        for i, fid in enumerate(self.fiducials):
            if fid.name == name:
                del self.fiducials[i]
                log.info(f"Fiducial '{name}' removido")
                return True
        return False
    
    def get_fiducial(self, name: str) -> Optional[FiducialTemplate]:
        """Retorna fiducial pelo nome."""
        for fid in self.fiducials:
            if fid.name == name:
                return fid
        return None
    
    def clear_fiducials(self):
        """Remove todos os fiduciais."""
        self.fiducials.clear()
        self.last_results.clear()
        self.transform = None
    
    # -------------------------------------------------------------------------
    #  CAPTURA DE TEMPLATE
    # -------------------------------------------------------------------------
    
    def capture_template(self, fiducial: FiducialTemplate, 
                         frame_bgr: np.ndarray,
                         center_x: Optional[int] = None,
                         center_y: Optional[int] = None) -> bool:
        """
        Captura template de fiducial a partir de um frame.
        
        Args:
            fiducial: Template de fiducial a ser preenchido
            frame_bgr: Frame BGR da câmera
            center_x, center_y: Centro da captura (None = centro do frame)
            
        Returns:
            True se captura foi bem-sucedida
        """
        if frame_bgr is None or frame_bgr.size == 0:
            log.error("Frame inválido para captura de template")
            return False
        
        h, w = frame_bgr.shape[:2]
        sz = fiducial.window_size
        
        # Usa centro do frame se não especificado
        if center_x is None:
            center_x = w // 2
        if center_y is None:
            center_y = h // 2
        
        # Calcula ROI
        x0 = max(0, center_x - sz // 2)
        y0 = max(0, center_y - sz // 2)
        x1 = min(w, x0 + sz)
        y1 = min(h, y0 + sz)
        
        roi = frame_bgr[y0:y1, x0:x1].copy()
        if roi.size == 0:
            log.error("ROI vazia para captura de template")
            return False
        
        fiducial.template_bgr = roi
        fiducial.template_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        log.info(f"Template '{fiducial.name}' capturado: {roi.shape[1]}x{roi.shape[0]}px")
        return True
    
    # -------------------------------------------------------------------------
    #  BUSCA DE FIDUCIAL (TEMPLATE MATCHING)
    # -------------------------------------------------------------------------
    
    def find_fiducial(self, fiducial: FiducialTemplate,
                      image_gray: np.ndarray,
                      expected_x: Optional[int] = None,
                      expected_y: Optional[int] = None) -> FiducialMatchResult:
        """
        Busca um fiducial na imagem usando template matching.
        
        Args:
            fiducial: Template do fiducial a buscar
            image_gray: Imagem grayscale onde buscar
            expected_x, expected_y: Posição esperada (para limitar busca ao raio)
            
        Returns:
            FiducialMatchResult com resultado da busca
        """
        result = FiducialMatchResult()
        
        if fiducial.template_gray is None:
            log.error(f"Fiducial '{fiducial.name}' não possui template")
            return result
        
        if image_gray is None or image_gray.size == 0:
            log.error("Imagem inválida para busca de fiducial")
            return result
        
        tmpl = fiducial.template_gray
        t_h, t_w = tmpl.shape
        i_h, i_w = image_gray.shape
        
        # Define região de busca
        if expected_x is not None and expected_y is not None:
            rad = fiducial.search_radius
            x0 = max(0, expected_x - rad - t_w // 2)
            y0 = max(0, expected_y - rad - t_h // 2)
            x1 = min(i_w, expected_x + rad + t_w // 2)
            y1 = min(i_h, expected_y + rad + t_h // 2)
            search_roi = image_gray[y0:y1, x0:x1]
            offset_x, offset_y = x0, y0
        else:
            search_roi = image_gray
            offset_x, offset_y = 0, 0
            expected_x = i_w // 2
            expected_y = i_h // 2
        
        # Verifica se ROI é grande o suficiente
        if search_roi.shape[0] < t_h or search_roi.shape[1] < t_w:
            log.warning(f"Região de busca muito pequena para template '{fiducial.name}'")
            return result
        
        # Template matching
        res = cv2.matchTemplate(search_roi, tmpl, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        similarity = max_val * 100
        result.similarity = similarity
        
        # Posição do match (canto superior esquerdo)
        tx = max_loc[0] + offset_x
        ty = max_loc[1] + offset_y
        
        # Centro do match
        cx = tx + t_w // 2
        cy = ty + t_h // 2
        
        result.image_x = cx
        result.image_y = cy
        result.match_rect = (tx, ty, t_w, t_h)
        
        # Verifica se está dentro do raio de busca
        dx = cx - expected_x
        dy = cy - expected_y
        result.offset_x = dx
        result.offset_y = dy
        
        in_radius = (abs(dx) <= fiducial.search_radius and 
                     abs(dy) <= fiducial.search_radius)
        
        if similarity >= fiducial.threshold and in_radius:
            result.found = True
            log.info(f"Fiducial '{fiducial.name}' encontrado: "
                    f"sim={similarity:.1f}%, pos=({cx}, {cy}), offset=({dx}, {dy})")
        else:
            if similarity < fiducial.threshold:
                log.warning(f"Fiducial '{fiducial.name}': similaridade baixa "
                           f"({similarity:.1f}% < {fiducial.threshold}%)")
            else:
                log.warning(f"Fiducial '{fiducial.name}': fora do raio de busca "
                           f"(Δx={dx}, Δy={dy})")
        
        return result
    
    def find_all_fiducials(self, image_gray: np.ndarray,
                           expected_positions: Optional[List[Tuple[int, int]]] = None
                           ) -> List[FiducialMatchResult]:
        """
        Busca todos os fiduciais configurados na imagem.
        
        Args:
            image_gray: Imagem grayscale
            expected_positions: Lista de posições esperadas [(x, y), ...] 
                               (uma para cada fiducial na ordem)
        
        Returns:
            Lista de FiducialMatchResult
        """
        self.last_results = []
        
        for i, fid in enumerate(self.fiducials):
            exp_x, exp_y = None, None
            if expected_positions and i < len(expected_positions):
                exp_x, exp_y = expected_positions[i]
            
            result = self.find_fiducial(fid, image_gray, exp_x, exp_y)
            self.last_results.append(result)
        
        return self.last_results
    
    # -------------------------------------------------------------------------
    #  CÁLCULO DE TRANSFORMAÇÃO
    # -------------------------------------------------------------------------
    
    def calculate_transform(self, 
                            gerber_points: List[Tuple[float, float]],
                            image_points: List[Tuple[float, float]]
                            ) -> Optional[AlignmentTransform]:
        """
        Calcula transformação afim a partir de pares de pontos correspondentes.
        
        Args:
            gerber_points: Pontos no espaço do Gerber [(x1, y1), (x2, y2), ...]
            image_points: Pontos correspondentes na imagem [(x1, y1), (x2, y2), ...]
            
        Returns:
            AlignmentTransform com a transformação calculada, ou None em caso de erro
        """
        if len(gerber_points) < 2 or len(image_points) < 2:
            log.error("São necessários pelo menos 2 pares de pontos para calcular transformação")
            return None
        
        if len(gerber_points) != len(image_points):
            log.error("Número de pontos Gerber e imagem deve ser igual")
            return None
        
        src = np.array(gerber_points, dtype=np.float32)
        dst = np.array(image_points, dtype=np.float32)
        
        transform = AlignmentTransform()
        
        if len(gerber_points) == 2:
            # Com 2 pontos: calcula translação, rotação e escala uniforme
            # (Transformação de similaridade)
            
            # Vetores entre os pontos
            v_src = src[1] - src[0]
            v_dst = dst[1] - dst[0]
            
            # Escala = razão entre as magnitudes
            mag_src = np.linalg.norm(v_src)
            mag_dst = np.linalg.norm(v_dst)
            
            if mag_src < 1e-6:
                log.error("Pontos Gerber muito próximos para calcular transformação")
                return None
            
            scale = mag_dst / mag_src
            transform.scale_x = scale
            transform.scale_y = scale
            
            # Ângulo = diferença entre as direções
            angle_src = math.atan2(v_src[1], v_src[0])
            angle_dst = math.atan2(v_dst[1], v_dst[0])
            angle = math.degrees(angle_dst - angle_src)
            transform.angle = angle
            
            # Translação = diferença entre centros (após escala e rotação)
            # Aplica rotação e escala ao primeiro ponto Gerber
            cos_a = math.cos(math.radians(angle))
            sin_a = math.sin(math.radians(angle))
            
            src_scaled_rotated = np.array([
                scale * (src[0, 0] * cos_a - src[0, 1] * sin_a),
                scale * (src[0, 0] * sin_a + src[0, 1] * cos_a)
            ])
            
            transform.tx = dst[0, 0] - src_scaled_rotated[0]
            transform.ty = dst[0, 1] - src_scaled_rotated[1]
            
            # Centro de rotação
            transform.center_x = float(src[0, 0])
            transform.center_y = float(src[0, 1])
            
            log.info(f"Transformação calculada (2 pontos): "
                    f"escala={scale:.4f}, ângulo={angle:.2f}°, "
                    f"translação=({transform.tx:.1f}, {transform.ty:.1f})")
            
        else:
            # Com 3+ pontos: calcula transformação afim completa
            # (pode incluir escala não-uniforme e cisalhamento)
            
            if len(gerber_points) >= 3:
                # Usa os primeiros 3 pontos para affine
                matrix = cv2.getAffineTransform(src[:3], dst[:3])
                
                # Converte para 3x3 (homografia)
                transform.matrix = np.vstack([matrix, [0, 0, 1]])
                
                # Extrai parâmetros aproximados
                # A = [[a b tx], [c d ty]] ≈ [[s*cos -s*sin tx], [s*sin s*cos ty]]
                a, b = matrix[0, 0], matrix[0, 1]
                c, d = matrix[1, 0], matrix[1, 1]
                
                transform.tx = matrix[0, 2]
                transform.ty = matrix[1, 2]
                transform.scale_x = math.sqrt(a*a + c*c)
                transform.scale_y = math.sqrt(b*b + d*d)
                transform.angle = math.degrees(math.atan2(c, a))
                
                log.info(f"Transformação calculada ({len(gerber_points)} pontos): "
                        f"escala=({transform.scale_x:.4f}, {transform.scale_y:.4f}), "
                        f"ângulo={transform.angle:.2f}°")
            
            if len(gerber_points) >= 4:
                # Com 4+ pontos: pode usar homografia (perspectiva)
                # Mas para stencil plano, affine é suficiente
                pass
        
        self.transform = transform
        return transform
    
    def calculate_transform_from_fiducials(self,
                                            scale_gerber_to_pixels: float = 1.0
                                            ) -> Optional[AlignmentTransform]:
        """
        Calcula transformação usando os fiduciais configurados e seus resultados de match.
        
        Args:
            scale_gerber_to_pixels: Fator de conversão de unidades Gerber para pixels
            
        Returns:
            AlignmentTransform calculada
        """
        if len(self.fiducials) < 2:
            log.error("São necessários pelo menos 2 fiduciais para calcular transformação")
            return None
        
        if len(self.last_results) != len(self.fiducials):
            log.error("Execute find_all_fiducials antes de calcular transformação")
            return None
        
        # Filtra apenas fiduciais encontrados com sucesso
        gerber_points = []
        image_points = []
        
        for fid, result in zip(self.fiducials, self.last_results):
            if result.found:
                # Converte coordenadas Gerber para pixels
                gx = fid.gerber_x * scale_gerber_to_pixels
                gy = fid.gerber_y * scale_gerber_to_pixels
                gerber_points.append((gx, gy))
                image_points.append((result.image_x, result.image_y))
        
        if len(gerber_points) < 2:
            log.error("Menos de 2 fiduciais foram encontrados com sucesso")
            return None
        
        return self.calculate_transform(gerber_points, image_points)
    
    # -------------------------------------------------------------------------
    #  APLICAÇÃO DE TRANSFORMAÇÃO
    # -------------------------------------------------------------------------
    
    def transform_point(self, x: float, y: float) -> Tuple[float, float]:
        """Aplica transformação a um ponto."""
        if self.transform is None:
            return x, y
        return self.transform.apply_to_point(x, y)
    
    def transform_points(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Aplica transformação a uma lista de pontos."""
        if self.transform is None:
            return points
        
        pts = np.array(points, dtype=np.float64)
        transformed = self.transform.apply_to_points(pts)
        return [(float(p[0]), float(p[1])) for p in transformed]
    
    def transform_polygon(self, polygon: np.ndarray) -> np.ndarray:
        """Aplica transformação a um polígono (array Nx2)."""
        if self.transform is None:
            return polygon
        return self.transform.apply_to_points(polygon)
    
    # -------------------------------------------------------------------------
    #  SERIALIZAÇÃO
    # -------------------------------------------------------------------------
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "fiducials": [f.to_dict() for f in self.fiducials],
            "default_window_size": self.default_window_size,
            "default_search_radius": self.default_search_radius,
            "default_threshold": self.default_threshold,
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Deserializa de dicionário."""
        self.fiducials = [
            FiducialTemplate.from_dict(f) 
            for f in data.get("fiducials", [])
        ]
        self.default_window_size = data.get("default_window_size", 50)
        self.default_search_radius = data.get("default_search_radius", 100)
        self.default_threshold = data.get("default_threshold", 70.0)


# ============================================================================
#  FUNÇÕES UTILITÁRIAS
# ============================================================================

def create_alignment_preview(image_bgr: np.ndarray,
                             fiducials: List[FiducialTemplate],
                             results: List[FiducialMatchResult],
                             transform: Optional[AlignmentTransform] = None,
                             gerber_contours: Optional[List[np.ndarray]] = None
                             ) -> np.ndarray:
    """
    Cria imagem de preview com fiduciais e transformação desenhados.
    
    Args:
        image_bgr: Imagem base
        fiducials: Lista de templates de fiduciais
        results: Lista de resultados de match
        transform: Transformação calculada (opcional)
        gerber_contours: Lista de contornos do Gerber para visualização (opcional)
        
    Returns:
        Imagem BGR com anotações
    """
    preview = image_bgr.copy()
    
    # Desenha resultados de fiduciais
    for fid, result in zip(fiducials, results):
        x, y, w, h = result.match_rect
        
        if result.found:
            # Verde para match bem-sucedido
            color = (0, 255, 0)
            thickness = 2
        else:
            # Vermelho para falha
            color = (0, 0, 255)
            thickness = 1
        
        # Desenha retângulo do match
        cv2.rectangle(preview, (x, y), (x + w, y + h), color, thickness)
        
        # Desenha nome do fiducial
        label = f"{fid.name}: {result.similarity:.1f}%"
        cv2.putText(preview, label, (x, y - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Desenha centro
        cx = int(result.image_x)
        cy = int(result.image_y)
        cv2.drawMarker(preview, (cx, cy), color, 
                       cv2.MARKER_CROSS, 10, thickness)
    
    # Desenha contornos do Gerber transformados
    if transform is not None and gerber_contours is not None:
        for contour in gerber_contours:
            transformed = transform.apply_to_points(contour.reshape(-1, 2))
            pts = transformed.reshape((-1, 1, 2)).astype(np.int32)
            cv2.polylines(preview, [pts], True, (255, 0, 255), 1)
    
    return preview


def calculate_error_metrics(gerber_points: List[Tuple[float, float]],
                            image_points: List[Tuple[float, float]],
                            transform: AlignmentTransform
                            ) -> Dict[str, float]:
    """
    Calcula métricas de erro da transformação.
    
    Returns:
        Dicionário com:
        - 'max_error': erro máximo em pixels
        - 'mean_error': erro médio em pixels
        - 'rms_error': erro RMS
    """
    if len(gerber_points) != len(image_points):
        return {"max_error": float('inf'), "mean_error": float('inf'), "rms_error": float('inf')}
    
    errors = []
    for (gx, gy), (ix, iy) in zip(gerber_points, image_points):
        tx, ty = transform.apply_to_point(gx, gy)
        err = math.sqrt((tx - ix)**2 + (ty - iy)**2)
        errors.append(err)
    
    if not errors:
        return {"max_error": 0.0, "mean_error": 0.0, "rms_error": 0.0}
    
    return {
        "max_error": max(errors),
        "mean_error": sum(errors) / len(errors),
        "rms_error": math.sqrt(sum(e*e for e in errors) / len(errors))
    }
