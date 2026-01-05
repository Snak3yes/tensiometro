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
        
    def connect(self, camera_id=0, timeout_seconds=10):
        """
        Conecta a uma câmera (USB ou stream URL).
        
        Para streams de URL (HTTP/MJPEG), a conexão é feita em uma thread 
        separada com timeout para evitar congelamento da UI.
        
        Args:
            camera_id: ID da câmera (int) ou URL do stream (str)
            timeout_seconds: Timeout máximo para conexão URL (padrão: 10s)
            
        Returns:
            True se conectou com sucesso, False caso contrário
        """
        # 0) Se já está conectado, primeiro desconecta para garantir
        #    liberação correta do dispositivo.
        if self.is_connected:
            self.disconnect()

        # 1) Se existe um objeto pendente de conexão anterior, libera-o.
        if self.camera and hasattr(self.camera, "release"):
            try:
                self.camera.release()
            except Exception:
                pass
            self.camera = None

        # 2) Caso seja uma interface personalizada, usa-la.
        if self.camera and hasattr(self.camera, "connect"):
            try:
                self.is_connected = self.camera.connect()
                return self.is_connected
            except Exception as e:
                self.last_error = str(e)
                return False

        # 3) Caminho padrão OpenCV  -------------------------------
        try:
            import cv2
            
            # Verifica se é uma URL (string não numérica) ou ID numérico
            is_url = False
            if isinstance(camera_id, str):
                # Remove espaços em branco que podem causar erro
                camera_id = camera_id.strip()
                if not camera_id.isdigit():
                    is_url = True
                else:
                    camera_id = int(camera_id)
            
            if is_url:
                # Para URLs, usa conexão com timeout em thread separada
                # para não bloquear a UI principal
                self.camera = self._connect_url_with_timeout(camera_id, timeout_seconds)
                if self.camera is None:
                    self.is_connected = False
                    return False
            else:
                # Para Webcams USB no Windows, CAP_DSHOW é recomendado (mais rápido/estável para USB)
                self.camera = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
                
            self.is_connected = self.camera.isOpened() if self.camera else False
            if not self.is_connected:
                self.last_error = f"cv2.VideoCapture({camera_id}) não abriu (URL={is_url})"
            return self.is_connected
        except Exception as e:
            self.last_error = str(e)
            return False
    
    def _connect_url_with_timeout(self, url, timeout_seconds):
        """
        Tenta conectar a uma URL de stream com timeout.
        
        Executa a conexão em uma thread separada para não bloquear a UI.
        
        Args:
            url: URL do stream de vídeo
            timeout_seconds: Tempo máximo de espera (segundos)
            
        Returns:
            cv2.VideoCapture object se sucesso, None se falhou/timeout
        """
        import cv2
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
        
        def try_connect():
            """Função que será executada na thread separada."""
            # Tenta primeiro com FFMPEG (melhor para streams HTTP/MJPEG)
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
            if cap.isOpened():
                # Tenta ler um frame para confirmar que está funcionando
                ret, _ = cap.read()
                if ret:
                    return cap
                cap.release()
            
            # Fallback: tenta sem backend específico
            cap = cv2.VideoCapture(url)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    return cap
                cap.release()
            
            return None
        
        # Executa a conexão em thread separada com timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(try_connect)
            try:
                result = future.result(timeout=timeout_seconds)
                if result is None:
                    self.last_error = f"Falha ao conectar à URL: {url}"
                return result
            except FuturesTimeoutError:
                self.last_error = f"Timeout ({timeout_seconds}s) ao conectar à URL: {url}"
                # Tenta cancelar a operação pendente
                future.cancel()
                return None
            except Exception as e:
                self.last_error = f"Erro ao conectar à URL {url}: {str(e)}"
                return None
                
    def disconnect(self):
        if not self.is_connected and not self.camera:
            return

        try:
            if self.camera:
                if hasattr(self.camera, "release"):
                    self.camera.release()
                    # Aguarda driver liberar o handle USB
                    import time; time.sleep(0.1)
                elif hasattr(self.camera, "disconnect"):
                    self.camera.disconnect()
        finally:
            # Zera referências para forçar recriação no próximo connect()
            self.camera = None
            self.is_connected = False

    def trigger_capture(self, params=None):
        """
        Aciona o trigger da câmera para captura.
        
        Args:
            params: Parâmetros específicos da câmera para o trigger
            
        Returns:
            A imagem capturada ou None em caso de erro
        """
        # Primeiro realiza o trigger
        if not self._activate_trigger(params):
            return None
            
        # Em seguida, captura a imagem
        return self.capture(params)
        
    def _activate_trigger(self, params=None):
        """
        Ativa o hardware trigger da câmera, se disponível.
        
        Args:
            params: Parâmetros específicos para o trigger
            
        Returns:
            True se o trigger foi bem-sucedido, False caso contrário
        """
        if not self.is_connected:
            self.last_error = "Câmera não conectada"
            return False
            
        try:
            # Verifica se a interface da câmera tem um método de trigger específico
            if hasattr(self.camera, 'trigger'):
                # Interface personalizada com método de trigger
                return self.camera.trigger(params)
                
            # Para câmeras OpenCV padrão, criar um atraso simulando trigger por software
            # e garantir que o frame seja descartado/limpo antes da captura real
            import time
            if hasattr(self.camera, 'grab'):
                # Limpa o buffer de frames
                self.camera.grab()
                time.sleep(0.1)  # Pequeno atraso para simular trigger
                return True
                
            return True  # Se não houver trigger específico, continua com a captura normal
            
        except Exception as e:
            self.last_error = f"Erro ao ativar trigger: {str(e)}"
            return False
            
    def has_hardware_trigger(self):
        """
        Verifica se a câmera possui suporte a hardware trigger.
        
        Returns:
            True se suporta trigger por hardware, False caso contrário
        """
        if not self.is_connected:
            return False
            
        # Verifica se a interface da câmera tem capacidade explícita de trigger
        return hasattr(self.camera, 'trigger') or hasattr(self.camera, 'has_hardware_trigger')
            
    def capture(self, params=None):
        """
        Captura uma imagem da câmera.
        A imagem é automaticamente recortada para formato quadrado (centro da imagem).
        
        Args:
            params: Parâmetros específicos da câmera (exposição, etc.)
            
        Returns:
            A imagem capturada (quadrada) ou None em caso de erro
        """
        if not self.is_connected:
            self.last_error = "Câmera não conectada"
            return None
            
        try:
            # Para interface personalizada
            if hasattr(self.camera, 'capture'):
                image = self.camera.capture(params)
                if image is None:
                    self.last_error = "A captura de imagem retornou None"
                    return None
                # Recorta para quadrado
                return self._crop_to_square(image)
                
            # Para OpenCV
            import cv2
            ret, frame = self.camera.read()
            if ret and frame is not None:
                # Aplicar parâmetros se fornecidos
                if params:
                    # Exemplo: ajustar brilho/contraste
                    if 'brightness' in params:
                        frame = cv2.convertScaleAbs(frame, alpha=params['brightness'])
                
                # Verifica se a imagem possui dados válidos
                if frame.size == 0 or frame.shape[0] == 0 or frame.shape[1] == 0:
                    self.last_error = "Imagem capturada tem dimensões inválidas"
                    return None
                
                # Recorta para formato quadrado (centro da imagem)
                return self._crop_to_square(frame)
            else:
                self.last_error = "Falha ao capturar imagem (sem dados ou retorno negativo)"
                return None
                
        except Exception as e:
            self.last_error = f"Erro na captura de imagem: {str(e)}"
            return None
    
    def _crop_to_square(self, image):
        """
        Recorta uma imagem para formato quadrado, pegando a região central.
        
        Args:
            image: Imagem numpy array (height, width, channels)
            
        Returns:
            Imagem recortada em formato quadrado
        """
        if image is None:
            return None
            
        height, width = image.shape[:2]
        
        # Se já é quadrada, retorna como está
        if height == width:
            return image
        
        # Calcula o tamanho do lado do quadrado (usa a menor dimensão)
        size = min(height, width)
        
        # Calcula o offset para centralizar o recorte
        x_offset = (width - size) // 2
        y_offset = (height - size) // 2
        
        # Recorta a região central
        cropped = image[y_offset:y_offset + size, x_offset:x_offset + size]
        
        return cropped
            
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