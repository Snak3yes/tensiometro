"""
Theme Settings Dialog

Diálogo para configuração de temas do sistema.
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton,
    QButtonGroup, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt

from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

logger = logging.getLogger(__name__)


class ThemeSettingsDialog(QDialog):
    """
    Diálogo para seleção de tema da aplicação

    Permite ao usuário escolher entre:
    - Light Theme (tema claro)
    - Dark Theme (tema escuro)
    - System Theme (segue configuração do OS)

    A escolha é salva no arquivo de configuração e aplicada imediatamente.

    Usage:
        >>> from consumo_lib.dialogs.theme_settings import ThemeSettingsDialog
        >>> from consumo_lib.ui.theme_manager import get_theme_manager
        >>>
        >>> mgr = get_theme_manager()
        >>> dialog = ThemeSettingsDialog(mgr, parent=self)
        >>> if dialog.exec() == QDialog.DialogCode.Accepted:
        >>>     print(f"Tema selecionado: {mgr.get_current_theme()}")
    """

    def __init__(self, theme_manager, parent=None):
        """
        Inicializa diálogo de configurações de tema

        Args:
            theme_manager: Instância de ThemeManager
            parent: Widget pai
        """
        super().__init__(parent)
        self.theme_manager = theme_manager
        self.current_theme = theme_manager.get_current_theme()

        self._setup_ui()
        self._connect_signals()
        self._load_current_theme()

    def _setup_ui(self):
        """Configura interface do diálogo"""
        self.setWindowTitle("Configurações de Tema")
        self.setModal(True)
        self.setMinimumSize(500, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(SPACE.MD)
        layout.setContentsMargins(SPACE.LG, SPACE.LG, SPACE.LG, SPACE.LG)

        # ================== TÍTULO ==================
        title = QLabel("Selecione o tema da aplicação:")
        title.setFont(TYPO.get_font(TYPO.HEADLINE_SMALL, bold=True))
        layout.addWidget(title)

        # ================== DESCRIÇÃO ==================
        desc = QLabel(
            "O tema selecionado será aplicado imediatamente e salvo como preferência.\n"
            "Você pode alterar o tema a qualquer momento através do menu Engenharia."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY};")
        layout.addWidget(desc)

        # ================== OPÇÕES DE TEMA ==================
        theme_group = QFrame()
        theme_group.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.MD}px;
                background-color: {COLORS.SURFACE};
            }}
        """)
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setSpacing(SPACE.SM)

        # Radio buttons para seleção de tema
        self.radio_group = QButtonGroup(self)

        # Light Theme
        self.radio_light = QRadioButton("🌞 Light Theme (Claro)")
        self.radio_light.setFont(TYPO.get_font(TYPO.BODY_LARGE))
        theme_layout.addWidget(self.radio_light)

        light_desc = QLabel("Tema claro com cores vibrantes, ideal para ambientes bem iluminados")
        light_desc.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-style: italic; padding-left: 24px;")
        theme_layout.addWidget(light_desc)

        theme_layout.addSpacing(SPACE.SM)

        # Dark Theme
        self.radio_dark = QRadioButton("🌙 Dark Theme (Escuro)")
        self.radio_dark.setFont(TYPO.get_font(TYPO.BODY_LARGE))
        theme_layout.addWidget(self.radio_dark)

        dark_desc = QLabel("Tema escuro para reduzir fadiga visual em ambientes com pouca luz")
        dark_desc.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-style: italic; padding-left: 24px;")
        theme_layout.addWidget(dark_desc)

        theme_layout.addSpacing(SPACE.SM)

        # System Theme
        self.radio_system = QRadioButton("💻 System Theme (Automático)")
        self.radio_system.setFont(TYPO.get_font(TYPO.BODY_LARGE))
        theme_layout.addWidget(self.radio_system)

        system_desc = QLabel("Segue automaticamente a configuração de tema do sistema operacional")
        system_desc.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-style: italic; padding-left: 24px;")
        theme_layout.addWidget(system_desc)

        # Adicionar ao button group
        self.radio_group.addButton(self.radio_light, 0)
        self.radio_group.addButton(self.radio_dark, 1)
        self.radio_group.addButton(self.radio_system, 2)

        layout.addWidget(theme_group)

        # ================== BOTÕES ==================
        button_layout = QHBoxLayout()

        self.btn_apply = QPushButton("Aplicar")
        self.btn_apply.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        self.btn_apply.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
        self.btn_apply.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                color: {COLORS.ON_PRIMARY};
                border-radius: {DIM.RADIUS_SM}px;
                padding: {SPACE.SM}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_DARK};
            }}
        """)
        button_layout.addWidget(self.btn_apply)

        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setFont(TYPO.get_font(TYPO.BODY_LARGE))
        self.btn_cancel.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
        button_layout.addWidget(self.btn_cancel)

        layout.addLayout(button_layout)
        layout.addStretch()

    def _connect_signals(self):
        """Conecta sinais e slots"""
        self.btn_apply.clicked.connect(self._apply_theme)
        self.btn_cancel.clicked.connect(self.reject)
        self.radio_group.buttonClicked.connect(self._on_theme_selected)

    def _load_current_theme(self):
        """Carrega tema atual e seleciona radio button correspondente"""
        if self.current_theme == "light":
            self.radio_light.setChecked(True)
        elif self.current_theme == "dark":
            self.radio_dark.setChecked(True)
        elif self.current_theme == "system":
            self.radio_system.setChecked(True)
        else:
            # Fallback para light
            logger.warning(f"Tema desconhecido: '{self.current_theme}', usando light")
            self.radio_light.setChecked(True)

    def _on_theme_selected(self, button):
        """
        Slot chamado quando um radio button é clicado

        Args:
            button: QRadioButton clicado
        """
        # Atualiza botão Aplicar para mostrar qual tema será aplicado
        if button == self.radio_light:
            theme_name = "Light"
        elif button == self.radio_dark:
            theme_name = "Dark"
        elif button == self.radio_system:
            theme_name = "System"
        else:
            theme_name = "Light"

        self.btn_apply.setText(f"Aplicar ({theme_name})")

    def _apply_theme(self):
        """Aplica o tema selecionado e salva na configuração"""
        # Determina qual tema foi selecionado
        if self.radio_light.isChecked():
            selected_theme = "light"
        elif self.radio_dark.isChecked():
            selected_theme = "dark"
        elif self.radio_system.isChecked():
            selected_theme = "system"
        else:
            selected_theme = "light"

        # Aplica tema via ThemeManager
        try:
            self.theme_manager.set_theme(selected_theme)

            # Salva no arquivo de configuração
            self._save_theme_to_config(selected_theme)

            # Mensagem de sucesso
            QMessageBox.information(
                self,
                "Tema Aplicado",
                f"O tema '{self._get_theme_display_name(selected_theme)}' foi aplicado com sucesso!\n\n"
                f"A configuração foi salva e será usada na próxima vez que você iniciar a aplicação."
            )

            # Fecha diálogo
            self.accept()

        except Exception as e:
            logger.error(f"Erro ao aplicar tema: {e}")
            QMessageBox.critical(
                self,
                "Erro",
                f"Ocorreu um erro ao aplicar o tema:\n\n{str(e)}"
            )

    def _save_theme_to_config(self, theme: str):
        """
        Salva preferência de tema no arquivo de configuração

        Args:
            theme: Nome do tema ("light" | "dark" | "system")
        """
        try:
            from aoi_lib.config_manager import AOIConfigManager

            config_mgr = AOIConfigManager()
            config_mgr.set("ui", "theme", value=theme)
            config_mgr.save()

            logger.info(f"✅ Tema salvo no config: {theme}")

        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar tema no config: {e}")
            # Não interrompe - o tema foi aplicado mesmo sem salvar

    def _get_theme_display_name(self, theme: str) -> str:
        """
        Retorna nome para exibição do tema

        Args:
            theme: Nome do tema

        Returns:
            Nome formatado para exibição
        """
        names = {
            "light": "Light (Claro)",
            "dark": "Dark (Escuro)",
            "system": "System (Automático)"
        }
        return names.get(theme, theme)


def show_theme_settings_dialog(theme_manager, parent=None) -> str:
    """
    Função de conveniência para mostrar diálogo de configurações de tema

    Args:
        theme_manager: Instância de ThemeManager
        parent: Widget pai

    Returns:
        Tema selecionado ("light" | "dark" | "system") ou None se cancelado

    Usage:
        >>> from consumo_lib.dialogs.theme_settings import show_theme_settings_dialog
        >>> from consumo_lib.ui.theme_manager import get_theme_manager
        >>>
        >>> mgr = get_theme_manager()
        >>> theme = show_theme_settings_dialog(mgr)
        >>> if theme:
        >>>     print(f"Tema: {theme}")
    """
    dialog = ThemeSettingsDialog(theme_manager, parent)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.theme_manager.get_current_theme()

    return None


__all__ = [
    "ThemeSettingsDialog",
    "show_theme_settings_dialog",
]
