import os
import json
import datetime
import requests
import logging
from typing import Optional, Tuple, Dict, Any, Union

# module‐level logger
logger = logging.getLogger(__name__)


class InspectionLogger:
    """
    Classe responsável por gerenciar todas as operações relacionadas a logs e envio de dados
    durante a inspeção visual.
    """
    def __init__(self, 
                 parent=None, 
                 config_manager=None,
                 *, 
                 api_url: Optional[str] = None,
                 json_posto: str = '',
                 json_usuario: str = '',
                 json_linha: str = '',):
        """
        Inicializa o logger de inspeção.

        Parâmetros opcionais (injeção direta ou via config_manager):
          api_url: URL para envio SFCS
          json_posto, json_usuario, json_linha
          log_dir, images_dir
          http_timeout (segundos)
          session (requests.Session)
          logger_ (logging.Logger)
        """
        self.parent = parent
        self.config_manager = config_manager

        # runtime‐configurable fields
        self.api_url: str = ''
        self.json_posto: str = ''
        self.json_usuario: str = ''
        self.json_linha: str = ''

        # directories
        self.log_dir: Optional[str] = None
        self.images_dir: Optional[str] = None

        # HTTP/session/logger
        self.http_timeout: float = 5.0
        self._session: Optional[requests.Session] = None
        self._logger: logging.Logger = logger

        # load from config_manager if provided
        if config_manager:
            self.api_url       = config_manager.get_config('api_url',       self.api_url)            
            self.json_posto    = config_manager.get_config('json_posto',    self.json_posto)
            self.json_usuario  = config_manager.get_config('json_usuario',  self.json_usuario)
            self.json_linha    = config_manager.get_config('json_linha',    self.json_linha)
        # else: leave defaults or override via setters/env
       
            self.json_posto = config_manager.get_config('json_posto', '')
            self.json_usuario = config_manager.get_config('json_usuario', '')
            self.json_linha = config_manager.get_config('json_linha', '')
        else:
            self.api_url = ''
         
            self.json_posto = ''
            self.json_usuario = ''
            self.json_linha = ''
            
        # nível mínimo para o root logger (padrão INFO)
        logging.basicConfig(level=logging.INFO)
        # suprime logs verbosos do pymodbus (ex.: "Frame advanced")
        logging.getLogger('pymodbus.logging').setLevel(logging.WARNING)
        # opcional: também silencia todos os logs do pymodbus
        logging.getLogger('pymodbus').setLevel(logging.WARNING)
        
    def set_log_directory(self, log_dir):
        """Define o diretório para armazenar logs"""
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
    def set_images_directory(self, images_dir):
        """Define o diretório para armazenar imagens"""
        self.images_dir = images_dir
        os.makedirs(images_dir, exist_ok=True)
        
    def generate_log_json(self, components, codigo_barras=None, codigo_externo=None):
        """
        Gera um arquivo JSON estruturado com os resultados da inspeção.
        
        Args:
            components: Dicionário com os componentes inspecionados
            codigo_barras: Informações do código de barras detectado
            codigo_externo: Código externo, se fornecido pelo usuário
                
        Returns:
            Tuple com os dados do log, o caminho para o arquivo detalhado e o caminho para o arquivo SFCS
        """
        if not self.log_dir:
            logging.error("Diretório de log não definido")
            return None, None, None
            
        # Preparar informações de código
        codigo_info = {
            "valor": "Não Identificado",
            "tipo": "Desconhecido",
            "encontrado": False
        }
        
        # Usar código externo se disponível
        if codigo_externo:
            codigo_info = {
                "valor": codigo_externo,
                "tipo": "EXTERNO",
                "encontrado": True
            }
        # Senão, usar código de barras se disponível
        elif codigo_barras and isinstance(codigo_barras, dict) and "valor" in codigo_barras and codigo_barras["valor"]:
            codigo_info = codigo_barras
            
        try:
            # Criar pasta baseada em timestamp e código
            timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            if codigo_info["encontrado"] and codigo_info["valor"].strip():
                folder_name = f"{timestamp_str}_{codigo_info['valor']}"
            else:
                folder_name = timestamp_str
                
            destino = os.path.join(self.log_dir, folder_name)
            os.makedirs(destino, exist_ok=True)
            
            if hasattr(self.parent, 'imagem_map') and self.parent.imagem_map is not None:
                try:
                    image_path = os.path.join(destino, "placa.png")
                    # Garantir formato PNG original de alta qualidade
                    self.parent.imagem_map.save(image_path, format="PNG", compress_level=0)
                    logging.info("Imagem da placa completa salva em: %s", image_path)
                except Exception as e:
                    logging.error(f"Erro ao salvar imagem da placa: {str(e)}")
            
            # Formato de data/hora para os logs
            data_hora_formatada = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Criar estrutura de dados do log detalhado (formato original)
            log_data = {
                "posto": self.json_posto,
                "usuario": self.json_usuario,
                "data_hora": data_hora_formatada,
                "quantidade_componentes": len([c for c in components.values() if isinstance(c, dict)]),
                "codigo_barras": codigo_info,
                "componentes": {}
            }
            
            # Adicionar informações de cada componente ao log detalhado
            for comp, info in components.items():
                if isinstance(info, dict):
                    componente_log = {
                        "status": "Aprovado" if info.get("status", False) else "Reprovado",
                        "similaridade_minima": info.get("similaridade_minima"),
                        "posicao_componente":  info.get("posicao"),             # [x, y] absolutos (px)
                        "dimensoes_componente": info.get("dimensoes"),          # [w, h] absolutos (px)
                        "similaridade": info.get("similaridade"),
                        "janela_azul": info.get("janela_azul_config"),
                        "janelas_vermelhas": []
                    }
                    
                    if "inspecoes" in info:
                        for i, janela in enumerate(info["inspecoes"]):
                            janela_log = {
                                "habilitada": janela.get("habilitada", True),
                                "posicao": janela.get("posicao"),
                                "tamanho": janela.get("tamanho"),
                                "threshold": janela.get("threshold", 128),
                                "cor_pixel": janela.get("cor_pixel"),
                                "percentual_minimo": janela.get("percentual_minimo"),
                                "resultado": janela.get("resultado", 0),
                                "status": "Aprovado" if janela.get("status", False) else "Reprovado"
                            }
                            componente_log["janelas_vermelhas"].append(janela_log)
                            
                    log_data["componentes"][comp] = componente_log
            
            # Salvar arquivo JSON detalhado (formato original)
            log_filename = f"{folder_name}.json"
            log_path = os.path.join(destino, log_filename)
            
            with open(log_path, 'w', encoding='utf-8') as log_file:
                json.dump(log_data, log_file, indent=4, ensure_ascii=False)
            
            # NOVO: Criar estrutura de dados do log simplificado (SFCS)
            sfcs_data = {
                "posto": self.json_posto,
                "usuario": self.json_usuario,
                "data_hora": data_hora_formatada,
                "quantidade_componentes": len([c for c in components.values() if isinstance(c, dict)]),
                # Extrair apenas o valor do código de barras para o formato simplificado
                "codigo_barras": codigo_info.get("valor", "Não Identificado"),
                "componentes": {}
            }
            
            # Adicionar informações simplificadas de cada componente (1=aprovado, 0=reprovado)
            for comp, info in components.items():
                if isinstance(info, dict):
                    sfcs_data["componentes"][comp] = 1 if info.get("status", False) else 0
            
            # Salvar arquivo JSON simplificado (SFCS)
            sfcs_filename = f"{timestamp_str}_SFCS.json"
            sfcs_path = os.path.join(destino, sfcs_filename)
            
            with open(sfcs_path, 'w', encoding='utf-8') as sfcs_file:
                json.dump(sfcs_data, sfcs_file, indent=4, ensure_ascii=False)
                
            logging.info(f"Log de inspeção detalhado salvo em: {log_path}")
            logging.info(f"Log de inspeção SFCS salvo em: {sfcs_path}")
            
            return log_data, log_path, sfcs_path
            
        except Exception as e:
            logging.error(f"Erro durante a geração do log: {str(e)}")
            return None, None, None
        
    def send_sfcs_data(self, sfcs_path):
        """
        Envia os dados do arquivo SFCS para a API e exclui o arquivo em caso de sucesso.
        
        Args:
            sfcs_path: Caminho para o arquivo SFCS JSON
            
        Returns:
            Boolean: True se o envio foi bem-sucedido, False caso contrário
        """
        if not sfcs_path or not os.path.exists(sfcs_path):
            logging.error(f"Arquivo SFCS não encontrado: {sfcs_path}")
            return False
            
        if not self.api_url:
            logging.error("URL da API não configurada")
            return False
            
        try:
            # Carregar arquivo JSON
            with open(sfcs_path, 'r') as file:
                sfcs_data = json.load(file)
                
            # Enviar para a API
            logging.info(f"Enviando dados SFCS para: {self.api_url}")
            response = requests.post(self.api_url, json=sfcs_data)
            response.raise_for_status()  # Lança exceção para códigos de status 4xx/5xx
            
            # Excluir o arquivo após envio bem-sucedido
            os.remove(sfcs_path)
            logging.info(f"Dados SFCS enviados com sucesso e arquivo excluído: {sfcs_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao enviar dados SFCS: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Erro ao processar envio de dados SFCS: {str(e)}")
            return False
            
    def send_data_http(self, log_path):
        """
        Envia os dados do log para um servidor via HTTP.
        
        Args:
            log_path: Caminho para o arquivo JSON de log
            
        Returns:
            Tuple (success, response): Indica sucesso e retorna a resposta HTTP se houver
        """
        if not log_path or not os.path.exists(log_path):
            logging.error(f"Arquivo de log não encontrado: {log_path}")
            return False, None
            
        if not self.api_url:
            logging.error("URL da API não configurada")
            return False, None
            
        try:
            # Carregar arquivo JSON
            with open(log_path, 'r') as file:
                log_data = json.load(file)
                
            # Enviar para a API
            response = requests.post(self.api_url, json=log_data)
            response.raise_for_status()  # Lança exceção para códigos de status 4xx/5xx
            
            logging.info("Dados enviados com sucesso para a API")
            return True, response
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro ao enviar dados: {str(e)}")
            return False, None
        except Exception as e:
            logging.error(f"Erro ao processar envio de dados: {str(e)}")
            return False, None
        
    def send_sfcs_data_from_dict(self, sfcs_data: Dict[str, Any]) -> bool:
        """
        Envia diretamente um dicionário SFCS para a API configurada,
        sem gravar arquivo intermediário.
        """
        if not self.api_url:
            self._logger.error("API URL not configured")
            return False
        sess = self._session or requests
        try:
            resp = sess.post(self.api_url,
                             json=sfcs_data,
                             timeout=self.http_timeout,
                             headers={"User-Agent": f"{__name__}/inspection_logger"})
            resp.raise_for_status()
            self._logger.info("SFCS dict sent successfully")
            return True
        except requests.RequestException as e:
            self._logger.error("Error sending SFCS dict: %s", e)
            return False

    def set_context(self,
                    *, posto: Optional[str] = None,
                       usuario: Optional[str] = None,
                       linha: Optional[str] = None):
        """
        Atualiza valores JSON de posto, usuário e linha
        sem reinstanciar o logger.
        """
        if posto is not None:
            self.json_posto = posto
        if usuario is not None:
            self.json_usuario = usuario
        if linha is not None:
            self.json_linha = linha

__all__ = ["InspectionLogger"]
