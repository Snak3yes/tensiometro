"""
ErrorHandler - Utilitário centralizado para tratamento de erros

Fornece funções para tratamento de erros comuns no Engineering Wizard:
- Desconexão de hardware (câmera, PLC)
- Timeout em operações
- Erros de I/O de arquivos
- Erros de validação de dados

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import logging
import traceback
from typing import Optional, Tuple, Callable, Any
from functools import wraps
from PyQt6.QtWidgets import QMessageBox, QWidget

logger = logging.getLogger(__name__)


class EngineeringWizardError(Exception):
    """Classe base para erros do Engineering Wizard."""
    pass


class HardwareError(EngineeringWizardError):
    """Erro de hardware (câmera, PLC, etc)."""
    def __init__(self, message: str, hardware_type: str = "hardware"):
        self.hardware_type = hardware_type
        super().__init__(message)


class TimeoutError(EngineeringWizardError):
    """Erro de timeout em operações."""
    pass


class FileIOError(EngineeringWizardError):
    """Erro de leitura/escrita de arquivo."""
    pass


class ValidationError(EngineeringWizardError):
    """Erro de validação de dados."""
    pass


class ErrorHandler:
    """
    Utilitário centralizado para tratamento de erros.

    Fornece métodos para:
    - Tratar erros de hardware
    - Tratar erros de timeout
    - Tratar erros de I/O
    - Exibir mensagens amigáveis ao usuário
    - Log detalhado para debugging
    """

    @staticmethod
    def handle_camera_error(
        error: Exception,
        parent: Optional[QWidget] = None,
        context: str = ""
    ) -> Tuple[bool, str]:
        """
        Trata erro de câmera desconectada.

        Args:
            error: Exceção capturada
            parent: Widget pai para diálogo
            context: Contexto onde erro ocorreu

        Returns:
            Tuple[bool, str]: (pode_continuar, mensagem_log)
        """
        error_msg = f"Erro de câmera: {str(error)}"

        if context:
            error_msg = f"{context} - {error_msg}"

        logger.error(error_msg, exc_info=True)

        # Mensagem amigável para usuário
        user_message = (
            "⚠️ Erro na Câmera\n\n"
            "A câmera foi desconectada ou não está respondendo.\n\n"
            "Soluções:\n"
            "• Verifique se a câmera está conectada\n"
            "• Tente reconectar a câmera\n"
            "• Reinicie o aplicativo se necessário"
        )

        if parent:
            QMessageBox.critical(
                parent,
                "Erro de Câmera",
                user_message
            )

        return False, error_msg

    @staticmethod
    def handle_plc_error(
        error: Exception,
        parent: Optional[QWidget] = None,
        context: str = ""
    ) -> Tuple[bool, str]:
        """
        Trata erro de PLC desconectado.

        Args:
            error: Exceção capturada
            parent: Widget pai para diálogo
            context: Contexto onde erro ocorreu

        Returns:
            Tuple[bool, str]: (pode_continuar, mensagem_log)
        """
        error_msg = f"Erro de PLC: {str(error)}"

        if context:
            error_msg = f"{context} - {error_msg}"

        logger.error(error_msg, exc_info=True)

        user_message = (
            "⚠️ Erro no PLC\n\n"
            "O PLC (Controlador Lógico Programável) não está respondendo.\n\n"
            "Soluções:\n"
            "• Verifique se o PLC está ligado\n"
            "• Verifique a conexão de rede\n"
            "• Confirme o endereço IP: 192.168.1.5\n"
            "• Reinicie o PLC se necessário"
        )

        if parent:
            QMessageBox.critical(
                parent,
                "Erro de PLC",
                user_message
            )

        return False, error_msg

    @staticmethod
    def handle_timeout_error(
        error: Exception,
        parent: Optional[QWidget] = None,
        context: str = "",
        timeout_seconds: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Trata erro de timeout.

        Args:
            error: Exceção capturada
            parent: Widget pai para diálogo
            context: Contexto onde erro ocorreu
            timeout_seconds: Tempo limite (opcional, para mensagem)

        Returns:
            Tuple[bool, str]: (pode_continuar, mensagem_log)
        """
        error_msg = f"Timeout: {str(error)}"

        if context:
            error_msg = f"{context} - {error_msg}"

        logger.error(error_msg, exc_info=True)

        timeout_info = f"({timeout_seconds} segundos)" if timeout_seconds else ""

        user_message = (
            "⏱️ Timeout\n\n"
            f"A operação demorou muito tempo {timeout_info}.\n\n"
            "Soluções:\n"
            "• Tente novamente\n"
            "• Verifique se o hardware está funcionando\n"
            "• Reinicie o aplicativo se o problema persistir"
        )

        if parent:
            QMessageBox.warning(
                parent,
                "Timeout",
                user_message
            )

        return False, error_msg

    @staticmethod
    def handle_file_error(
        error: Exception,
        parent: Optional[QWidget] = None,
        context: str = "",
        file_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Trata erro de I/O de arquivo.

        Args:
            error: Exceção capturada
            parent: Widget pai para diálogo
            context: Contexto onde erro ocorreu
            file_path: Caminho do arquivo (opcional)

        Returns:
            Tuple[bool, str]: (pode_continuar, mensagem_log)
        """
        error_msg = f"Erro de arquivo: {str(error)}"

        if context:
            error_msg = f"{context} - {error_msg}"

        logger.error(error_msg, exc_info=True)

        file_info = f"\nArquivo: {file_path}" if file_path else ""

        user_message = (
            "⚠️ Erro de Arquivo\n\n"
            f"Não foi possível ler ou escrever o arquivo.{file_info}\n\n"
            "Soluções:\n"
            "• Verifique se o arquivo existe\n"
            "• Verifique permissões de escrita\n"
            "• Verifique se há espaço em disco\n"
            "• Feche o arquivo se estiver aberto em outro programa"
        )

        if parent:
            QMessageBox.critical(
                parent,
                "Erro de Arquivo",
                user_message
            )

        return False, error_msg

    @staticmethod
    def handle_validation_error(
        error: Exception,
        parent: Optional[QWidget] = None,
        context: str = ""
    ) -> Tuple[bool, str]:
        """
        Trata erro de validação de dados.

        Args:
            error: Exceção capturada
            parent: Widget pai para diálogo
            context: Contexto onde erro ocorreu

        Returns:
            Tuple[bool, str]: (pode_continuar, mensagem_log)
        """
        error_msg = f"Erro de validação: {str(error)}"

        if context:
            error_msg = f"{context} - {error_msg}"

        logger.warning(error_msg)  # Warning, não error (é esperado)

        user_message = (
            "⚠️ Dados Inválidos\n\n"
            f"{str(error)}\n\n"
            "Por favor, verifique os dados e tente novamente."
        )

        if parent:
            QMessageBox.warning(
                parent,
                "Validação",
                user_message
            )

        return False, error_msg

    @staticmethod
    def handle_generic_error(
        error: Exception,
        parent: Optional[QWidget] = None,
        context: str = "",
        show_traceback: bool = False
    ) -> Tuple[bool, str]:
        """
        Trata erro genérico não categorizado.

        Args:
            error: Exceção capturada
            parent: Widget pai para diálogo
            context: Contexto onde erro ocorreu
            show_traceback: Se True, mostra traceback na mensagem (debug only)

        Returns:
            Tuple[bool, str]: (pode_continuar, mensagem_log)
        """
        error_msg = f"Erro: {type(error).__name__}: {str(error)}"

        if context:
            error_msg = f"{context} - {error_msg}"

        logger.error(error_msg, exc_info=True)

        traceback_str = traceback.format_exc() if show_traceback else ""

        user_message = (
            "⚠️ Erro Inesperado\n\n"
            f"Ocorreu um erro: {str(error)}\n\n"
            "Por favor, tente novamente.\n"
            "Se o problema persistir, contate o suporte técnico."
        )

        if show_traceback:
            user_message += f"\n\nDetalhes técnicos:\n{traceback_str}"

        if parent:
            QMessageBox.critical(
                parent,
                "Erro",
                user_message
            )

        return False, error_msg


def safe_execute(
    error_handler: Optional[Callable] = None,
    default_return: Any = None,
    log_error: bool = True
):
    """
    Decorator para execução segura de funções.

    Args:
        error_handler: Função customizada para tratar erros
        default_return: Valor de retorno em caso de erro
        log_error: Se True, loga erros

    Example:
        @safe_execute(error_handler=ErrorHandler.handle_camera_error)
        def capture_image():
            # Código que pode falhar
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(
                        f"Erro em {func.__name__}: {e}",
                        exc_info=True
                    )

                if error_handler:
                    # Tentar encontrar parent_widget nos argumentos
                    parent = None
                    if args and hasattr(args[0], 'parent'):
                        parent = args[0].parent()
                    elif args and isinstance(args[0], QWidget):
                        parent = args[0]

                    error_handler(e, parent=parent, context=func.__name__)

                return default_return

        return wrapper
    return decorator


def show_error_dialog(
    parent: QWidget,
    title: str,
    message: str,
    error_type: str = "error",
    details: Optional[str] = None
):
    """
    Exibe diálogo de erro padronizado.

    Args:
        parent: Widget pai
        title: Título do diálogo
        message: Mensagem principal
        error_type: Tipo de erro ("error", "warning", "info")
        details: Detalhes adicionais (opcional)
    """
    full_message = message

    if details:
        full_message += f"\n\nDetalhes:\n{details}"

    if error_type == "error":
        QMessageBox.critical(parent, title, full_message)
    elif error_type == "warning":
        QMessageBox.warning(parent, title, full_message)
    else:
        QMessageBox.information(parent, title, full_message)


def is_motion_interlock_error(message: Optional[str]) -> bool:
    """Retorna True quando a mensagem representa bloqueio por M137/M138."""
    normalized = (message or "").lower()
    return (
        "movimento absoluto bloqueado pelo clp" in normalized
        and ("m137" in normalized or "m138" in normalized)
    )


def show_motion_interlock_dialog(
    parent: Optional[QWidget],
    message: str,
    operation: str = "movimento",
) -> bool:
    """
    Exibe um dialogo padronizado para bloqueio de movimento pelo CLP.

    Retorna True quando o dialogo especializado foi exibido.
    """
    if parent is None or not is_motion_interlock_error(message):
        return False

    user_message = (
        f"O {operation} foi bloqueado pelo CLP.\n\n"
        f"{message}\n\n"
        "Verifique os sensores X1.0/M137 e X1.1/M138 antes de tentar novamente."
    )
    QMessageBox.critical(parent, "Intertravamento de Movimento", user_message)
    return True
