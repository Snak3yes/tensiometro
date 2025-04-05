class CameraController:
    """
    Classe para controlar uma câmera e capturar imagens.
    Pode ser adaptada para diferentes interfaces de câmera.
    """
    
    def __init__(self, camera_interface=None):
        """
        Inicializa o controlador de câmera.
        
        Args:
            camera_interface: Interface de câmera personalizada (opcional)
        """
        self.camera = camera_interface
        self.is_connected = False
        self.last_error = ""
        
    def connect(self, camera_id=0):
        """
        Conecta à câmera.
        
        Args:
            camera_id: ID da câmera (para OpenCV)
            
        Returns:
            bool: True se conectado com sucesso
        """
        if self.camera:
            # Usa a interface fornecida
            try:
                self.is_connected = self.camera.connect()
                return self.is_connected
            except Exception as e:
                self.last_error = str(e)
                return False
        else:
            # Implementação padrão com OpenCV
            try:
                import cv2
                self.camera = cv2.VideoCapture(camera_id)
                self.is_connected = self.camera.isOpened()
                return self.is_connected
            except Exception as e:
                self.last_error = str(e)
                return False
                
    def disconnect(self):
        """Desconecta da câmera."""
        if not self.is_connected:
            return
            
        try:
            if hasattr(self.camera, 'release'):
                self.camera.release()
            elif hasattr(self.camera, 'disconnect'):
                self.camera.disconnect()
                
            self.is_connected = False
            
        except Exception as e:
            self.last_error = str(e)
            
    def capture(self, params=None):
        """
        Captura uma imagem da câmera.
        
        Args:
            params: Parâmetros específicos da câmera (exposição, etc.)
            
        Returns:
            A imagem capturada ou None em caso de erro
        """
        if not self.is_connected:
            return None
            
        try:
            # Para interface personalizada
            if hasattr(self.camera, 'capture'):
                return self.camera.capture(params)
                
            # Para OpenCV
            import cv2
            ret, frame = self.camera.read()
            if ret:
                # Aplicar parâmetros se fornecidos
                if params:
                    # Exemplo: ajustar brilho/contraste
                    if 'brightness' in params:
                        frame = cv2.convertScaleAbs(frame, alpha=params['brightness'])
                return frame
            else:
                self.last_error = "Falha ao capturar imagem"
                return None
                
        except Exception as e:
            self.last_error = str(e)
            return None
            
    def set_parameters(self, **kwargs):
        """
        Define parâmetros da câmera.
        
        Args:
            **kwargs: Parâmetros específicos da câmera
        """
        if not self.is_connected:
            return False
            
        try:
            # Para interface personalizada
            if hasattr(self.camera, 'set_parameters'):
                return self.camera.set_parameters(**kwargs)
                
            # Para OpenCV
            import cv2
            for key, value in kwargs.items():
                if key.lower() == 'exposure':
                    self.camera.set(cv2.CAP_PROP_EXPOSURE, value)
                elif key.lower() == 'focus':
                    self.camera.set(cv2.CAP_PROP_FOCUS, value)
                # Adicione outros parâmetros conforme necessário
                
            return True
            
        except Exception as e:
            self.last_error = str(e)
            return False