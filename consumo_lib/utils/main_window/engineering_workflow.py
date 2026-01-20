"""
Módulo: engineering_workflow.py

Gerencia o workflow de engenharia da MainWindow (AOIControllerApp).

Responsabilidades:
- Abrir Engineering Wizard (open_wizard)
- Handler quando programa é completado (on_program_completed)
- Mostrar programas salvos (show_saved_programs)
- Carregar programa selecionado (load_selected_program)
- Excluir programa selecionado (delete_selected_program)

Author: Refactoring (2026-01-14)
"""

import logging
from pathlib import Path
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QHBoxLayout, QLabel, QMessageBox
)

from consumo_lib.ui import COLORS

logger = logging.getLogger(__name__)


class MainWindowEngineeringWorkflow:
    """
    Gerencia o workflow de engenharia da MainWindow.

    Centraliza toda lógica relacionada ao Engineering Wizard e
    gerenciamento de programas de inspeção salvos.

    Attributes:
        main_window: Instância da MainWindow (AOIControllerApp)
    """

    def __init__(self, main_window):
        """
        Inicializa o MainWindowEngineeringWorkflow.

        Args:
            main_window: Instância da MainWindow (AOIControllerApp)
        """
        self.main_window = main_window

    # =========================================================================
    # ENGINEERING WIZARD
    # =========================================================================

    def open_wizard(self):
        """
        Abre o Engineering Wizard - Assistente de criação de programas de inspeção.

        Cria EngineeringHardwareCoordinator com os controllers de hardware disponíveis
        e abre o diálogo com 7 abas para criar programa de inspeção completo.
        """
        logger.info("Abrindo Engineering Wizard")

        try:
            # Importa dependências
            from consumo_lib.dialogs import EngineeringWizardDialog
            from consumo_lib.coordinators import EngineeringHardwareCoordinator

            # Cria hardware coordinator com controllers disponíveis
            camera_ctrl = None
            plc_ctrl = None

            # Obtém controller de câmera se disponível
            if hasattr(self.main_window, 'camera_controller') and self.main_window.camera_controller is not None:
                camera_ctrl = self.main_window.camera_controller

            # Obtém controller de CNC/PLC se disponível
            if hasattr(self.main_window, 'controller') and hasattr(self.main_window.controller, 'cnc') and self.main_window.controller.cnc is not None:
                plc_ctrl = self.main_window.controller.cnc

            # Cria hardware coordinator
            hardware_coordinator = EngineeringHardwareCoordinator(
                camera_controller=camera_ctrl,
                plc_controller=plc_ctrl,
                fiducial_aligner=None  # Alinhador fiducial será criado internamente
            )

            logger.debug(
                f"Hardware coordinator criado: "
                f"camera={camera_ctrl is not None}, plc={plc_ctrl is not None}"
            )

            # Busca CNCControlTab diretamente na MainWindow (criada pelo MainUIBuilder)
            cnc_control_tab = getattr(self.main_window, 'cnc_control_tab', None)
            logger.debug(f"CNCControlTab encontrada: {cnc_control_tab is not None}")

            # Cria e abre diálogo passando CNCControlTab
            dialog = EngineeringWizardDialog(
                parent=self.main_window,
                cnc_control_tab=cnc_control_tab
            )

            # Conecta signal de programa completado
            dialog.program_completed.connect(self.on_program_completed)

            # Abre diálogo
            result = dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                logger.info("Engineering Wizard concluído com sucesso")
            else:
                logger.info("Engineering Wizard cancelado")

        except Exception as e:
            logger.exception("Erro ao abrir Engineering Wizard")
            QMessageBox.critical(
                self.main_window,
                "Erro - Engineering Wizard",
                f"Erro ao abrir Engineering Wizard:\n{str(e)}"
            )

    def on_program_completed(self, program_data: Dict[str, Any]):
        """
        Handler chamado quando Engineering Wizard completa um programa.

        Salva o programa usando EngineeringProgramManager e opcionalmente
        cria uma Recipe no RecipeManager.

        Args:
            program_data: Dicionário com dados do programa criado
        """
        from consumo_lib.managers.engineering_program_manager import EngineeringProgramManager
        from consumo_lib.models.engineering.program_config import ProgramConfig

        logger.info(f"Programa de engenharia criado: {program_data.get('program_name', 'Sem nome')}")

        try:
            # Salva programa usando EngineeringProgramManager
            program_manager = EngineeringProgramManager()

            # Recupera ProgramConfig do state do wizard (se disponível)
            # Nota: program_data pode vir diretamente do ProgramConfig.to_dict()
            program = ProgramConfig.from_dict(program_data)

            # Salva programa
            filepath = program_manager.save_program(program)

            logger.info(f"Programa salvo em: {filepath}")

            # Pergunta se deseja criar Recipe
            reply = QMessageBox.question(
                self.main_window,
                "📦 Programa Salvo",
                f"Programa salvo com sucesso!\n\n"
                f"Nome: {program.program_name}\n"
                f"Código Stencil: {program.stencil_code}\n"
                f"Versão: {program.version}\n\n"
                f"Deseja criar uma Recipe para usar no sistema?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Cria Recipe usando RecipeManagerWrapper
                if self.main_window.recipe_manager_controller is not None:
                    recipe = self.main_window.recipe_manager_controller.create_recipe_from_program(program)

                    if recipe:
                        QMessageBox.information(
                            self.main_window,
                            "✅ Recipe Criada",
                            f"Recipe '{recipe.name}' criada com sucesso!\n\n"
                            f"Recipe ID: {recipe.recipe_id}\n\n"
                            f"A Recipe agora está disponível no sistema."
                        )
                    else:
                        QMessageBox.warning(
                            self.main_window,
                            "⚠️ Aviso",
                            "Programa foi salvo, mas houve erro ao criar Recipe.\n"
                            "Consulte os logs para mais detalhes."
                        )
                else:
                    QMessageBox.warning(
                        self.main_window,
                        "⚠️ RecipeManager Não Disponível",
                        "RecipeManagerController não está disponível.\n"
                        "Programa foi salvo, mas Recipe não foi criada."
                    )
            else:
                QMessageBox.information(
                    self.main_window,
                    "✅ Concluído",
                    f"Programa '{program.program_name}' salvo.\n\n"
                    f"Para criar uma Recipe depois, use o menu:\n"
                    f"Engenharia → Programas Salvos"
                )

        except Exception as e:
            logger.exception("Erro ao salvar programa de engenharia")
            QMessageBox.critical(
                self.main_window,
                "Erro - Salvamento",
                f"Erro ao salvar programa:\n{str(e)}"
            )

    # =========================================================================
    # GERENCIAMENTO DE PROGRAMAS SALVOS
    # =========================================================================

    def show_saved_programs(self):
        """
        Mostra gerenciador de programas salvos.

        Lista todos os programas salvos pelo EngineeringProgramManager
        e permite carregar um programa como Recipe.
        """
        from consumo_lib.managers.engineering_program_manager import EngineeringProgramManager

        logger.info("Mostrando programas salvos")

        try:
            # Cria diálogo
            dialog = QDialog(self.main_window)
            dialog.setWindowTitle("Programas de Inspeção Salvos")
            dialog.setMinimumSize(700, 400)

            layout = QVBoxLayout(dialog)

            # Título
            title = QLabel("📁 Programas de Inspeção Salvos")
            title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS.PRIMARY};")
            layout.addWidget(title)

            # Tabela de programas
            table = QTableWidget()
            table.setColumnCount(6)
            table.setHorizontalHeaderLabels([
                "Nome", "Stencil", "Versão", "Criado em", "Modificado em", "Caminho"
            ])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            layout.addWidget(table)

            # Botões
            button_layout = QHBoxLayout()

            btn_load = QPushButton("📂 Carregar como Recipe")
            btn_load.setEnabled(False)
            btn_load.clicked.connect(lambda: self.load_selected_program(table, dialog))

            btn_delete = QPushButton("🗑️ Excluir")
            btn_delete.setEnabled(False)
            btn_delete.clicked.connect(lambda: self.delete_selected_program(table, dialog))

            btn_close = QPushButton("Fechar")
            btn_close.clicked.connect(dialog.accept)

            button_layout.addWidget(btn_load)
            button_layout.addWidget(btn_delete)
            button_layout.addStretch()
            button_layout.addWidget(btn_close)

            layout.addLayout(button_layout)

            # Conecta signal de seleção
            table.itemSelectionChanged.connect(
                lambda: (
                    btn_load.setEnabled(True),
                    btn_delete.setEnabled(True)
                )
            )

            # Carrega programas
            program_manager = EngineeringProgramManager()
            programs = program_manager.list_programs()

            # Preenche tabela
            table.setRowCount(len(programs))
            for row, prog in enumerate(programs):
                table.setItem(row, 0, QTableWidgetItem(prog.get("program_name", "N/A")))
                table.setItem(row, 1, QTableWidgetItem(prog.get("stencil_code", "N/A")))
                table.setItem(row, 2, QTableWidgetItem(prog.get("version", "N/A")))
                table.setItem(row, 3, QTableWidgetItem(prog.get("created_at", "N/A")[:19]))
                table.setItem(row, 4, QTableWidgetItem(prog.get("modified_at", "N/A")[:19]))
                table.setItem(row, 5, QTableWidgetItem(prog.get("filepath", "")))

            table.resizeColumnsToContents()

            # Mostra diálogo
            dialog.exec()

        except Exception as e:
            logger.exception("Erro ao listar programas salvos")
            QMessageBox.critical(
                self.main_window,
                "Erro",
                f"Erro ao listar programas:\n{str(e)}"
            )

    def load_selected_program(self, table, dialog):
        """
        Carrega programa selecionado como Recipe.

        Args:
            table: Tabela com programas
            dialog: Dialog a ser fechado após sucesso
        """
        try:
            row = table.currentRow()
            filepath = table.item(row, 5).text()

            if not filepath:
                QMessageBox.warning(self.main_window, "Aviso", "Caminho do arquivo não encontrado")
                return

            # Extrai nome do arquivo
            filename = Path(filepath).name

            # Carrega usando RecipeManagerWrapper
            if self.main_window.recipe_manager_controller is not None:
                recipe = self.main_window.recipe_manager_controller.load_from_engineering_program(filename)

                if recipe:
                    QMessageBox.information(
                        self.main_window,
                        "✅ Recipe Carregada",
                        f"Programa '{filename}' carregado como Recipe!\n\n"
                        f"Recipe: {recipe.name}\n"
                        f"ID: {recipe.recipe_id}"
                    )
                    dialog.accept()
                else:
                    QMessageBox.warning(
                        self.main_window,
                        "⚠️ Erro",
                        "Falha ao carregar programa como Recipe"
                    )
            else:
                QMessageBox.warning(
                    self.main_window,
                    "⚠️ RecipeManager Não Disponível",
                    "RecipeManagerController não está disponível."
                )

        except Exception as e:
            logger.exception("Erro ao carregar programa")
            QMessageBox.critical(
                self.main_window,
                "Erro",
                f"Erro ao carregar programa:\n{str(e)}"
            )

    def delete_selected_program(self, table, dialog):
        """
        Exclui programa selecionado.

        Args:
            table: Tabela com programas
            dialog: Dialog a ser fechado após exclusão
        """
        try:
            row = table.currentRow()
            filepath = table.item(row, 5).text()
            filename = Path(filepath).name

            # Confirma
            reply = QMessageBox.question(
                self.main_window,
                "Confirmar Exclusão",
                f"Deseja excluir o programa?\n\n{filename}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                from consumo_lib.managers.engineering_program_manager import EngineeringProgramManager

                program_manager = EngineeringProgramManager()
                program_manager.delete_program(filename)

                QMessageBox.information(
                    self.main_window,
                    "✅ Excluído",
                    f"Programa '{filename}' excluído com sucesso."
                )

                # Recarrega lista
                dialog.accept()
                self.show_saved_programs()

        except Exception as e:
            logger.exception("Erro ao excluir programa")
            QMessageBox.critical(
                self.main_window,
                "Erro",
                f"Erro ao excluir programa:\n{str(e)}"
            )
