"""
Módulo: app_state.py

Gerencia o estado da MainWindow (AOIControllerApp).

Responsabilidades:
- Armazenar estado da aplicação (modo de inspeção, resultados, sequências)
- Gerenciar permissões baseadas em roles
- Atualizar displays de posição
- Fornecer acesso ao usuário atual

Author: Refactoring (2026-01-14)
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MainWindowState:
    """
    Gerencia o estado da MainWindow.

    Centraliza atributos de estado que antes estavam espalhados pela MainWindow,
    facilitando gerenciamento e teste.

    Attributes:
        selected_inspection_mode: Modo de inspeção selecionado ("tension", "inspection", "both")
        inspection_results: Resultados da última inspeção
        current_sequence: Sequência de posições atual
        is_running_sequence: Flag indicando se sequência está em execução
    """

    def __init__(self):
        """Inicializa o estado da aplicação."""
        self.selected_inspection_mode: str = "tension"
        self.inspection_results: Dict[str, Any] = {}
        self.current_sequence: Optional[Any] = None
        self.is_running_sequence: bool = False

        # Referências para UI e services (serão injetadas)
        self._main_window = None
        self._auth_service = None

    def set_references(self, main_window, auth_service):
        """
        Define referências para MainWindow e AuthService.

        Args:
            main_window: Instância da MainWindow (AOIControllerApp)
            auth_service: Instância do AuthService
        """
        self._main_window = main_window
        self._auth_service = auth_service

    def get_current_user(self):
        """
        Retorna o usuário atual autenticado.

        Returns:
            User ou None se não houver usuário logado
        """
        if self._auth_service:
            return self._auth_service.get_current_user()
        return None

    def apply_role_permissions(self):
        """
        Aplica permissões de acesso baseadas no role do usuário.

        Regras:
        - OPERATOR: Apenas aba "Programas" habilitada
        - ENGINEERING: Todas as abas habilitadas
        - ADMIN: Todas as abas habilitadas
        """
        if not self._main_window:
            logger.warning("MainWindow não disponível, não aplicando permissões")
            return

        if not hasattr(self._main_window, 'right_panel') or not self._main_window.right_panel:
            logger.warning("right_panel ainda não criado, permissões serão aplicadas depois")
            return

        user = self.get_current_user()
        if not user:
            logger.warning("Nenhum usuário logado, não aplicando permissões")
            return

        from aoi_lib.auth import UserRole

        # 🔥 CRÍTICO: Atualiza RoleManager com o role do usuário autenticado
        # Isso garante que can_modify_config() e outros métodos funcionem corretamente
        if hasattr(self._main_window, 'role_manager') and self._main_window.role_manager:
            self._main_window.role_manager.set_role(user.role.value)
            logger.info(f"RoleManager atualizado com role: {user.role.value}")

        if user.role == UserRole.OPERATOR:
            # Operador: Apenas aba "Programas" (TreeViewTab)
            logger.info(f"Aplicando permissões OPERATOR para {user.username}")

            # Desabilita todas as abas exceto "Programas"
            for i in range(self._main_window.right_panel.count()):
                tab_text = self._main_window.right_panel.tabText(i)
                if "Programas" not in tab_text:
                    self._main_window.right_panel.setTabEnabled(i, False)
                    logger.debug(f"Aba desabilitada: {tab_text}")

            # Garante que aba "Programas" esteja habilitada e selecionada
            for i in range(self._main_window.right_panel.count()):
                if "Programas" in self._main_window.right_panel.tabText(i):
                    self._main_window.right_panel.setTabEnabled(i, True)
                    self._main_window.right_panel.setCurrentIndex(i)
                    logger.debug(f"Aba habilitada e selecionada: {self._main_window.right_panel.tabText(i)}")
                    break

            # Desabilita grupos de conexão e calibração (painel esquerdo)
            if hasattr(self._main_window, 'connection_group'):
                self._main_window.connection_group.setEnabled(False)
            if hasattr(self._main_window, 'calibration_group'):
                self._main_window.calibration_group.setEnabled(False)

        elif user.role in [UserRole.ENGINEERING, UserRole.ADMIN]:
            # Engineering/Admin: Todas as abas habilitadas
            logger.info(f"Aplicando permissões {user.role.value.upper()} para {user.username}")

            # Habilita todas as abas
            for i in range(self._main_window.right_panel.count()):
                self._main_window.right_panel.setTabEnabled(i, True)
                logger.debug(f"Aba habilitada: {self._main_window.right_panel.tabText(i)}")

            # Habilita grupos de conexão e calibração
            if hasattr(self._main_window, 'connection_group'):
                self._main_window.connection_group.setEnabled(True)
            if hasattr(self._main_window, 'calibration_group'):
                # Calibração fica oculta mesmo para admin, mas habilitada
                self._main_window.calibration_group.setEnabled(True)

    def update_position_display(self):
        """
        Atualiza a exibição da posição atual (WPos calculada).

        Atualiza apenas MovementControlWidget (dentro da aba CNC Control).
        Os labels antigos do painel esquerdo foram removidos - posição
        agora é exibida dentro da groupbox Movement Controls.
        """
        if not self._main_window:
            return

        # ─────────────────────────────────────────────────────────────────────
        # Atualizar MovementControlWidget (dentro da aba CNC Control)
        # ─────────────────────────────────────────────────────────────────────
        self._update_movement_widget_position()

        # NOTA: PositionManagerController.update_position_display() foi removido
        # pois os labels do painel esquerdo não existem mais.
        # O signal position_updated ainda é emitido por PositionManagerController
        # em outros contextos onde necessário.

    def _update_movement_widget_position(self):
        """
        Atualiza display de posição no MovementControlWidget.

        Obtém posição atual e status do CNC e atualiza os labels dentro
        da groupbox Movement Controls.
        """
        if not self._main_window:
            return

        if not hasattr(self._main_window, 'right_panel') or not self._main_window.right_panel:
            return

        # Acessar primeira aba (CNC Control)
        cnc_tab = self._main_window.right_panel.widget(0)
        if not cnc_tab:
            return

        # Verificar se o movimento widget existe
        if not hasattr(cnc_tab, 'movement_widget'):
            return

        try:
            # Obter posição atual do CNC
            pos = self._main_window.controller.cnc.get_current_position()

            # Obter status da máquina
            status = getattr(self._main_window.controller.cnc, 'machine_status', 'Desconectado')

            # Atualizar widget com posição e status
            cnc_tab.movement_widget.update_position(
                x=pos['x'],
                y=pos['y'],
                z=pos.get('z', 0.0),
                status=status
            )
        except Exception as e:
            logger.debug(f"Erro ao atualizar posição no MovementControlWidget: {e}")
            # Silencioso - pode não estar conectado ainda

    # ─────────────────────────────────────────────────────────────────────────
    # Getters e Setters para estado
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def inspection_mode(self) -> str:
        """Retorna o modo de inspeção selecionado."""
        return self.selected_inspection_mode

    @inspection_mode.setter
    def inspection_mode(self, mode: str):
        """Define o modo de inspeção."""
        self.selected_inspection_mode = mode

    @property
    def results(self) -> Dict[str, Any]:
        """Retorna os resultados da última inspeção."""
        return self.inspection_results

    @results.setter
    def results(self, results: Dict[str, Any]):
        """Define os resultados da inspeção."""
        self.inspection_results = results

    @property
    def sequence(self) -> Optional[Any]:
        """Retorna a sequência atual."""
        return self.current_sequence

    @sequence.setter
    def sequence(self, sequence: Optional[Any]):
        """Define a sequência atual."""
        self.current_sequence = sequence

    @property
    def sequence_running(self) -> bool:
        """Retorna True se sequência está em execução."""
        return self.is_running_sequence

    @sequence_running.setter
    def sequence_running(self, running: bool):
        """Define o estado de execução da sequência."""
        self.is_running_sequence = running
