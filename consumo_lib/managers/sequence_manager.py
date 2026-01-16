"""
Sequence Manager - Gerenciador de sequências de inspeção

Responsável por gerenciar sequências de inspeção (criar, executar, parar, salvar, carregar).
"""

import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SequenceManager:
    """
    Gerenciador de sequências de inspeção.

    Esta classe gerencia a criação, execução e manipulação de
    sequências de posições de inspeção.

    Responsabilidades:
    - Criar sequência a partir do registro de posições
    - Executar sequência (mover para cada posição)
    - Parar execução de sequência
    - Salvar sequência em arquivo JSON
    - Carregar sequência de arquivo JSON
    - Exportar/Importar G-code

    O manager delega para SequenceController, mas proporciona
    métodos com nomes mais simples e adequados para a MainWindow.
    """

    def __init__(self, sequence_controller, main_window):
        """
        Inicializa o manager.

        Args:
            sequence_controller: Controller de sequência existente
            main_window: Janela principal (para atualizar UI)
        """
        self.sequence_controller = sequence_controller
        self.main_window = main_window

        self._is_running = False
        self._current_sequence = []

        logger.debug("SequenceManager inicializado")

    def create_sequence_from_registry(self) -> bool:
        """
        Cria uma sequência a partir do registro de posições.

        Returns:
            True se criada com sucesso, False caso contrário
        """
        try:
            # Obtém posições do registro
            if not hasattr(self.main_window, 'position_list_widget'):
                logger.error("position_list_widget não encontrado")
                return False

            positions = self.main_window.position_list_widget.get_positions()

            if not positions:
                logger.warning("Nenhuma posição no registro para criar sequência")
                self.main_window.statusBar().showMessage(
                    "Nenhuma posição disponível", 3000
                )
                return False

            # Cria sequência
            self._current_sequence = positions
            logger.info(f"Sequência criada com {len(positions)} posições")

            self.main_window.statusBar().showMessage(
                f"Sequência criada: {len(positions)} posições", 3000
            )

            return True
        except Exception as e:
            logger.error(f"Erro ao criar sequência: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao criar sequência: {e}", 3000
            )
            return False

    def create_sequence(self, positions: list) -> bool:
        """
        Cria uma sequência com as posições fornecidas.

        Args:
            positions: Lista de posições (x, y, z)

        Returns:
            True se criada com sucesso, False caso contrário
        """
        try:
            self._current_sequence = positions
            logger.info(f"Sequência criada com {len(positions)} posições")

            self.main_window.statusBar().showMessage(
                f"Sequência criada: {len(positions)} posições", 3000
            )

            return True
        except Exception as e:
            logger.error(f"Erro ao criar sequência: {e}")
            return False

    def run_sequence(self) -> bool:
        """
        Executa a sequência atual.

        Returns:
            True se iniciada com sucesso, False caso contrário
        """
        try:
            if not self._current_sequence:
                logger.warning("Nenhuma sequência para executar")
                self.main_window.statusBar().showMessage(
                    "Crie uma sequência primeiro", 3000
                )
                return False

            if self._is_running:
                logger.warning("Sequência já está em execução")
                return False

            # Executa sequência via controller
            success = self.sequence_controller.run_sequence(self._current_sequence)

            if success:
                self._is_running = True
                logger.info(f"Executando sequência de {len(self._current_sequence)} posições")
                self.main_window.statusBar().showMessage(
                    f"Executando sequência: {len(self._current_sequence)} posições", 3000
                )
            else:
                logger.error("Falha ao iniciar sequência")
                self.main_window.statusBar().showMessage(
                    "Falha ao iniciar sequência", 3000
                )

            return success
        except Exception as e:
            logger.error(f"Erro ao executar sequência: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao executar sequência: {e}", 3000
            )
            return False

    def stop_sequence(self) -> bool:
        """
        Para a execução da sequência.

        Returns:
            True se parada com sucesso, False caso contrário
        """
        try:
            if not self._is_running:
                logger.warning("Nenhuma sequência em execução")
                return False

            success = self.sequence_controller.stop_sequence()

            if success:
                self._is_running = False
                logger.info("Sequência parada")
                self.main_window.statusBar().showMessage(
                    "Sequência parada", 3000
                )
            else:
                logger.error("Falha ao parar sequência")
                self.main_window.statusBar().showMessage(
                    "Falha ao parar sequência", 3000
                )

            return success
        except Exception as e:
            logger.error(f"Erro ao parar sequência: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao parar sequência: {e}", 3000
            )
            return False

    def save_program(self, filepath: Optional[str] = None) -> bool:
        """
        Salva a sequência atual em arquivo JSON.

        Args:
            filepath: Caminho do arquivo (opcional, abre dialog se None)

        Returns:
            True se salvo com sucesso, False caso contrário
        """
        try:
            if not self._current_sequence:
                logger.warning("Nenhuma sequência para salvar")
                self.main_window.statusBar().showMessage(
                    "Nenhuma sequência para salvar", 3000
                )
                return False

            # Se não fornecido filepath, abre dialog
            if filepath is None:
                from PyQt6.QtWidgets import QFileDialog

                filepath, _ = QFileDialog.getSaveFileName(
                    self.main_window,
                    "Salvar Programa",
                    "",
                    "JSON Files (*.json);;All Files (*)"
                )

                if not filepath:
                    return False

            # Salva sequência em JSON
            data = {
                'positions': self._current_sequence,
                'total_positions': len(self._current_sequence)
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Programa salvo: {filepath}")
            self.main_window.statusBar().showMessage(
                f"Programa salvo: {Path(filepath).name}", 3000
            )

            return True
        except Exception as e:
            logger.error(f"Erro ao salvar programa: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao salvar programa: {e}", 3000
            )
            return False

    def load_program(self, filepath: Optional[str] = None) -> bool:
        """
        Carrega uma sequência de arquivo JSON.

        Args:
            filepath: Caminho do arquivo (opcional, abre dialog se None)

        Returns:
            True se carregado com sucesso, False caso contrário
        """
        try:
            # Se não fornecido filepath, abre dialog
            if filepath is None:
                from PyQt6.QtWidgets import QFileDialog

                filepath, _ = QFileDialog.getOpenFileName(
                    self.main_window,
                    "Carregar Programa",
                    "",
                    "JSON Files (*.json);;All Files (*)"
                )

                if not filepath:
                    return False

            # Carrega sequência do JSON
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._current_sequence = data.get('positions', [])

            logger.info(f"Programa carregado: {filepath} ({len(self._current_sequence)} posições)")
            self.main_window.statusBar().showMessage(
                f"Programa carregado: {len(self._current_sequence)} posições", 3000
            )

            # Atualiza UI se position_list_widget existir
            if hasattr(self.main_window, 'position_list_widget'):
                self.main_window.position_list_widget.clear()
                for pos in self._current_sequence:
                    self.main_window.position_list_widget.add_position(*pos)

            return True
        except Exception as e:
            logger.error(f"Erro ao carregar programa: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao carregar programa: {e}", 3000
            )
            return False

    def save_gcode(self, filepath: Optional[str] = None) -> bool:
        """
        Exporta a sequência atual como G-code.

        Args:
            filepath: Caminho do arquivo (opcional, abre dialog se None)

        Returns:
            True se exportado com sucesso, False caso contrário
        """
        try:
            if not self._current_sequence:
                logger.warning("Nenhuma sequência para exportar")
                self.main_window.statusBar().showMessage(
                    "Nenhuma sequência para exportar", 3000
                )
                return False

            # Se não fornecido filepath, abre dialog
            if filepath is None:
                from PyQt6.QtWidgets import QFileDialog

                filepath, _ = QFileDialog.getSaveFileName(
                    self.main_window,
                    "Exportar G-code",
                    "",
                    "G-code Files (*.gcode *.nc);;All Files (*)"
                )

                if not filepath:
                    return False

            # Gera G-code
            gcode_lines = []
            gcode_lines.append("; Programa de Inspeção")
            gcode_lines.append(f"; {len(self._current_sequence)} posições")
            gcode_lines.append("G21 ; Milímetros")
            gcode_lines.append("G90 ; Posicionamento absoluto")

            for i, pos in enumerate(self._current_sequence, 1):
                x, y, z = pos
                gcode_lines.append(f"; Posição {i}")
                gcode_lines.append(f"G0 X{x:.3f} Y{y:.3f} Z{z:.3f}")
                gcode_lines.append("M0 ; Pausa para inspeção")

            gcode_lines.append("M30 ; Fim de programa")

            # Salva arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(gcode_lines))

            logger.info(f"G-code exportado: {filepath}")
            self.main_window.statusBar().showMessage(
                f"G-code exportado: {Path(filepath).name}", 3000
            )

            return True
        except Exception as e:
            logger.error(f"Erro ao exportar G-code: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao exportar G-code: {e}", 3000
            )
            return False

    def load_gcode(self, filepath: Optional[str] = None) -> bool:
        """
        Importa posições de um arquivo G-code.

        Args:
            filepath: Caminho do arquivo (opcional, abre dialog se None)

        Returns:
            True se importado com sucesso, False caso contrário
        """
        try:
            # Se não fornecido filepath, abre dialog
            if filepath is None:
                from PyQt6.QtWidgets import QFileDialog

                filepath, _ = QFileDialog.getOpenFileName(
                    self.main_window,
                    "Importar G-code",
                    "",
                    "G-code Files (*.gcode *.nc);;All Files (*)"
                )

                if not filepath:
                    return False

            # Lê arquivo G-code e extrai posições
            positions = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('G0') or line.startswith('G1'):
                        # Extrai coordenadas X, Y, Z
                        x = y = z = 0.0
                        for token in line.split():
                            if token.startswith('X'):
                                x = float(token[1:])
                            elif token.startswith('Y'):
                                y = float(token[1:])
                            elif token.startswith('Z'):
                                z = float(token[1:])
                        positions.append((x, y, z))

            self._current_sequence = positions

            logger.info(f"G-code importado: {filepath} ({len(positions)} posições)")
            self.main_window.statusBar().showMessage(
                f"G-code importado: {len(positions)} posições", 3000
            )

            # Atualiza UI se position_list_widget existir
            if hasattr(self.main_window, 'position_list_widget'):
                self.main_window.position_list_widget.clear()
                for pos in self._current_sequence:
                    self.main_window.position_list_widget.add_position(*pos)

            return True
        except Exception as e:
            logger.error(f"Erro ao importar G-code: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao importar G-code: {e}", 3000
            )
            return False

    @property
    def is_running_sequence(self) -> bool:
        """
        Verifica se há sequência em execução.

        Returns:
            True se executando, False caso contrário
        """
        return self._is_running

    @property
    def current_sequence(self) -> list:
        """
        Retorna a sequência atual.

        Returns:
            Lista de posições da sequência
        """
        return self._current_sequence
