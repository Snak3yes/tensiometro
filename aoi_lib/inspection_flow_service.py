"""
inspection_flow_service.py
--------------------------
Orquestrador de fluxo de inspeção visual.

Isola a lógica de carregamento de arquivos, configuração e execução
da inspeção visual, removendo dependências de UI.
"""

import logging
import os
import cv2
import numpy as np
from typing import Optional, Tuple, Dict, Any

from aoi_lib.stencil_inspector import StencilInspector, InspectionThresholds, InspectionResult
from aoi_lib.gerber_renderer import AlignmentTransform

logger = logging.getLogger(__name__)

class InspectionFlowService:
    """
    Service para executar o fluxo completo de inspeção visual.
    """
    
    def __init__(self):
        """Inicializa o service."""
        self.inspector = StencilInspector()
        
    def execute_inspection(self, 
                           gerber_path: str, 
                           mosaic_path: str, 
                           alignment_config: Optional[Dict[str, float]] = None,
                           thresholds: Optional[InspectionThresholds] = None) -> Tuple[InspectionResult, Optional[np.ndarray]]:
        """
        Executa uma inspeção completa.
        
        Args:
            gerber_path: Caminho do arquivo Gerber
            mosaic_path: Caminho da imagem de mosaico
            alignment_config: Dicionário com chaves 'tx', 'ty', 'angle', 'scale' (opcional)
            thresholds: Thresholds de inspeção (opcional)
            
        Returns:
            Tuple[InspectionResult, np.ndarray]: Resultado e imagem de overlay
            
        Raises:
            FileNotFoundError: Se arquivos não existirem
            ValueError: Se falhar ao carregar imagem
            Exception: Outros erros de execução
        """
        # 1. Validar e Carregar Gerber
        if not os.path.exists(gerber_path):
            raise FileNotFoundError(f"Arquivo Gerber não encontrado: {gerber_path}")
            
        # Atualiza thresholds se fornecidos
        if thresholds:
            self.inspector.thresholds = thresholds
            
        logger.info(f"Carregando Gerber: {gerber_path}")
        if not self.inspector.load_gerber(gerber_path):
            raise Exception("Falha ao processar arquivo Gerber")
            
        # 2. Carregar Mosaico
        if not os.path.exists(mosaic_path):
            raise FileNotFoundError(f"Arquivo de mosaico não encontrado: {mosaic_path}")
            
        logger.info(f"Carregando mosaico: {mosaic_path}")
        mosaic = cv2.imread(mosaic_path)
        if mosaic is None:
            raise ValueError(f"Falha ao decodificar imagem: {mosaic_path}")
            
        self.inspector.set_mosaic(mosaic)
        
        # 3. Configurar Alinhamento
        if alignment_config:
            transform = AlignmentTransform(
                tx=alignment_config.get('tx', 0.0),
                ty=alignment_config.get('ty', 0.0),
                angle=alignment_config.get('angle', 0.0),
                scale_x=alignment_config.get('scale', 1.0),
                scale_y=alignment_config.get('scale', 1.0)
            )
            self.inspector.set_alignment(transform)
            logger.info("Alinhamento configurado")
        else:
            # Reset alignment if explicitly None passed? Or keep previous? 
            # Ideally reset.
            self.inspector.set_alignment(AlignmentTransform())
            
        # 4. Executar Inspeção
        logger.info("Executando inspeção...")
        result = self.inspector.inspect()
        
        # 5. Gerar Overlay
        overlay = self.inspector.get_result_overlay(show_all=True)
        
        # Anexar caminhos ao resultado (para referência)
        result.gerber_file = gerber_path
        result.mosaic_file = mosaic_path
        
        return result, overlay
