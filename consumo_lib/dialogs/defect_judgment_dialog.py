"""
Dialog de Julgamento de Defeitos - Análise Visual Humana

Interface para operador julgar defeitos identificados pelo sistema.
Percorre lista de defeitos, aprova (falha falsa) ou confirma como real.
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QScrollArea, QFrame,
    QComboBox, QLineEdit, QSlider, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QPainter

from .final_decision_dialog import FinalDecisionDialog
from consumo_lib.widgets.zoomable_image_view import ZoomableImageView
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)


class DefectJudgmentDialog(QDialog):
    """
    Dialog de julgamento de defeitos

    Permite operador percorrer defeitos identificados pelo sistema
    e julgar cada um como:
    - Aprovar (Falha Falsa): Não é defeito real
    - Confirmar como Defeito Real: É defeito real

    Sinais:
        analysis_completed: Emitido quando análise completa
                            Argumento: dict com resultados
    """

    analysis_completed = pyqtSignal(dict)

    # Tipos de defeitos padrão (configurável pela engenharia)
    DEFAULT_DEFECT_TYPES = [
        "Bloqueado por resíduo de pasta",
        "Abertura deformada",
        "Dano mecânico",
        "Sujidade generalizada",
        "Corrosão",
        "Outro..."
    ]

    def __init__(
        self,
        defects: list,
        session_data: dict,
        defect_types: list = None,
        parent=None
    ):
        """
        Inicializa dialog de julgamento

        Args:
            defects: Lista de defeitos identificados pelo sistema
                [
                    {
                        "defect_id": "D001",
                        "position": {"x": 125, "y": 78},
                        "type": "blocked",
                        "percentage_open": 26,
                        "image_path": "/data/sessions/.../D001.png",
                        "area_expected": 2.3,
                        "area_observed": 0.6
                    },
                    ...
                ]
            session_data: Dados da sessão
                {
                    "session_id": "XPTO-2025-12-15-001",
                    "stencil_code": "STENCIL-ABC-123",
                    "session_type": "Limpeza XPTO",
                    "operator": "João Silva",
                    "mode": "inspection"
                }
            defect_types: Lista de tipos de defeitos (opcional)
            parent: Widget pai
        """
        super().__init__(parent)

        self.defects = defects
        self.current_index = 0
        self.session_data = session_data
        self.defect_types = defect_types or self.DEFAULT_DEFECT_TYPES

        # Estado do julgamento de cada defeito
        # None = não julgado ainda
        # "approved" = aprovado (falha falsa)
        # "confirmed" = confirmado como defeito real
        self.judgments = [None] * len(defects)

        # Anotações por defeito
        self.annotations = [""] * len(defects)

        # Tipos de defeitos selecionados por defeito
        self.selected_types = [""] * len(defects)

        self.setup_ui()
        self._load_current_defect()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("Análise de Defeitos - Julgamento")
        self.setModal(True)
        self.setFixedSize(1000, 750)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Header
        header = self._create_header()
        layout.addWidget(header)

        # Área principal (split horizontal)
        from PyQt6.QtWidgets import QSplitter

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Lado esquerdo: Info do defeito + Imagem
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Lado direito: Controles de julgamento
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Proporção 60% | 40%
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)

        layout.addWidget(splitter, 1)

        # Rodapé (navegação)
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Cria header com título e progresso"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Título principal
        title_label = QLabel("Julgamento de Defeitos")
        title_label.setFont(TYPO.get_font(TYPO.HEADLINE_LARGE, bold=True))
        title_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(title_label)

        # Info da sessão
        info_text = f"Stencil: {self.session_data.get('stencil_code')}   |   " \
                    f"Operador: {self.session_data.get('operator')}"
        info_label = QLabel(info_text)
        info_label.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.BODY_SMALL}px")
        layout.addWidget(info_label)

        # Barra de progresso
        progress_text = f"Defeito {self.current_index + 1} de {len(self.defects)} " \
                        f"({self._get_analyzed_count()} analisados)"
        self.progress_label = QLabel(progress_text)
        self.progress_label.setStyleSheet(f"""
            QLabel {{
                background-color: {COLORS.SECONDARY_LIGHT};
                color: {COLORS.TEXT_PRIMARY};
                padding: {SPACE.SM}px;
                border-radius: {DIM.RADIUS_MD}px;
                font-weight: 600;
                {TYPO.BODY_MEDIUM}
            }}
        """)
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)

        return widget

    def _create_left_panel(self) -> QWidget:
        """Cria painel esquerdo (info + imagem)"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Info do defeito atual
        info_frame = self._create_defect_info_frame()
        layout.addWidget(info_frame)

        # Preview da imagem
        image_frame = QFrame()
        image_frame.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.MD}px;
            }}
        """)

        image_layout = QVBoxLayout(image_frame)
        image_layout.setContentsMargins(0, 0, 0, 0)

        # Label "Imagem do Defeito"
        image_title = QLabel("Imagem do Defeito")
        image_title.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        image_title.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        image_layout.addWidget(image_title)

        # Widget de imagem com zoom
        self.image_preview = ZoomableImageView()
        image_layout.addWidget(self.image_preview, 1)

        # Controles de zoom
        zoom_layout = QHBoxLayout()
        zoom_layout.addStretch()

        zoom_out_btn = StandardButton("🔍-")
        zoom_out_btn.setMaximumWidth(50)
        zoom_out_btn.clicked.connect(self.image_preview.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)

        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.BODY_SMALL}px")
        zoom_layout.addWidget(zoom_label)

        zoom_in_btn = StandardButton("🔍+")
        zoom_in_btn.setMaximumWidth(50)
        zoom_in_btn.clicked.connect(self.image_preview.zoom_in)
        zoom_layout.addWidget(zoom_in_btn)

        reset_zoom_btn = StandardButton("Reset")
        reset_zoom_btn.setMaximumWidth(70)
        reset_zoom_btn.clicked.connect(self.image_preview.reset_zoom)
        zoom_layout.addWidget(reset_zoom_btn)

        zoom_layout.addStretch()

        image_layout.addLayout(zoom_layout)
        layout.addWidget(image_frame, 1)

        return panel

    def _create_defect_info_frame(self) -> QFrame:
        """Cria frame com informações do defeito atual"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.SURFACE};
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.LG}px;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setSpacing(SPACE.XS)

        # Título
        title = QLabel("Informações do Defeito")
        title.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
        title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        layout.addWidget(title)

        # Campos de informação (serão preenchidos dinamicamente)
        self.info_position = QLabel("Posição: --")
        self.info_position.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.BODY_SMALL}px")
        layout.addWidget(self.info_position)

        self.info_type = QLabel("Tipo: --")
        self.info_type.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.BODY_SMALL}px")
        layout.addWidget(self.info_type)

        self.info_status = QLabel("Status: --")
        self.info_status.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.BODY_SMALL}px")
        layout.addWidget(self.info_status)

        self.info_percentage = QLabel("Abertura: --")
        self.info_percentage.setStyleSheet(f"color: {COLORS.TEXT_HINT}; font-size: {TYPO.BODY_SMALL}px")
        layout.addWidget(self.info_percentage)

        return frame

    def _create_right_panel(self) -> QWidget:
        """Cria painel direito (controles de julgamento)"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Análise do Sistema
        system_frame = QFrame()
        system_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.WARNING_LIGHT};
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.LG}px;
            }}
        """)

        system_layout = QVBoxLayout(system_frame)
        system_layout.setSpacing(SPACE.XS)

        system_title = QLabel("Análise do Sistema")
        system_title.setFont(TYPO.get_font(TYPO.BODY_MEDIUM, bold=True))
        system_title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        system_layout.addWidget(system_title)

        self.system_details = QLabel("--")
        self.system_details.setWordWrap(True)
        self.system_details.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY_DARK}; font-size: {TYPO.BODY_SMALL}px")
        self.system_details.setAlignment(Qt.AlignmentFlag.AlignTop)
        system_layout.addWidget(self.system_details, 1)

        layout.addWidget(system_frame)

        # Tipo de Defeito (dropdown)
        type_frame = QFrame()
        type_frame.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.LG}px;
            }}
        """)

        type_layout = QVBoxLayout(type_frame)
        type_layout.setSpacing(SPACE.SM)

        type_label = QLabel("Classificação do Defeito:")
        type_label.setFont(TYPO.get_font(TYPO.BODY_MEDIUM, bold=True))
        type_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        type_layout.addWidget(type_label)

        self.defect_type_combo = QComboBox()
        self.defect_type_combo.addItems(["Selecione..."] + self.defect_types)
        self.defect_type_combo.setStyleSheet(f"""
            QComboBox {{
                padding: {SPACE.SM}px;
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
                {TYPO.BODY_SMALL}
            }}
        """)
        type_layout.addWidget(self.defect_type_combo)

        layout.addWidget(type_frame)

        # Anotações (opcional)
        notes_frame = QFrame()
        notes_frame.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.LG}px;
            }}
        """)

        notes_layout = QVBoxLayout(notes_frame)
        notes_layout.setSpacing(SPACE.SM)

        notes_label = QLabel("Anotações (opcional):")
        notes_label.setFont(TYPO.get_font(TYPO.BODY_MEDIUM, bold=True))
        notes_label.setStyleSheet(f"color: {COLORS.TEXT_HINT};")
        notes_layout.addWidget(notes_label)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Observações sobre este defeito...")
        self.notes_input.setStyleSheet(f"""
            QLineEdit {{
                padding: {SPACE.SM}px;
                border: 2px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
                {TYPO.BODY_SMALL}
            }}
        """)
        notes_layout.addWidget(self.notes_input)

        layout.addWidget(notes_frame)

        layout.addStretch()

        # Seu Julgamento
        judgment_frame = QFrame()
        judgment_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.PRIMARY_LIGHT};
                border: 2px solid {COLORS.SECONDARY_LIGHT};
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.LG}px;
            }}
        """)

        judgment_layout = QVBoxLayout(judgment_frame)
        judgment_layout.setSpacing(SPACE.MD)

        judgment_title = QLabel("Seu Julgamento")
        judgment_title.setFont(TYPO.get_font(TYPO.HEADLINE_MEDIUM, bold=True))
        judgment_title.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY};")
        judgment_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        judgment_layout.addWidget(judgment_title)

        judgment_subtitle = QLabel("Este defeito é REAL?")
        judgment_subtitle.setStyleSheet(f"color: {COLORS.ON_PRIMARY_DARK}; font-size: {TYPO.BODY_SMALL}px")
        judgment_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        judgment_layout.addWidget(judgment_subtitle)

        # Botões de julgamento
        approve_btn = StandardButton("✓ APROVAR (Falha Falsa)")
        approve_btn.setMinimumHeight(DIM.BUTTON_HEIGHT_LG)
        approve_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SUCCESS};
                color: {COLORS.TEXT_PRIMARY};
                {TYPO.BODY_MEDIUM}
                font-weight: bold;
                border: none;
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.MD}px {SPACE.XL}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SUCCESS_DARK};
            }}
        """)
        approve_btn.clicked.connect(self.on_approve_clicked)
        judgment_layout.addWidget(approve_btn)

        confirm_btn = StandardButton("✓ CONFIRMAR como Defeito Real", variant="primary")
        confirm_btn.setMinimumHeight(DIM.BUTTON_HEIGHT_LG)
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.ERROR};
                color: {COLORS.TEXT_PRIMARY};
                {TYPO.BODY_MEDIUM}
                font-weight: bold;
                border: none;
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.MD}px {SPACE.XL}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.ERROR_DARK};
            }}
        """)
        confirm_btn.clicked.connect(self.on_confirm_clicked)
        judgment_layout.addWidget(confirm_btn)

        layout.addWidget(judgment_frame)

        return panel

    def _create_footer(self) -> QWidget:
        """Cria rodapé com navegação"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Botão Anterior
        self.prev_button = StandardButton("◀ Anterior")
        self.prev_button.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
        self.prev_button.setMinimumWidth(120)
        self.prev_button.setEnabled(False)  # Desabilitado no primeiro
        self.prev_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BORDER_VARIANT};
                color: {COLORS.TEXT_PRIMARY_VARIANT};
                {TYPO.BODY_MEDIUM}
                font-weight: 600;
                border: none;
                border-radius: {DIM.RADIUS_SM}px;
                padding: {SPACE.SM}px {SPACE.LG}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BORDER};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.BORDER};
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        self.prev_button.clicked.connect(self.on_previous_clicked)
        layout.addWidget(self.prev_button)

        layout.addStretch()

        # Botão Finalizar Análise
        self.finish_button = StandardButton("📋 Finalizar Análise")
        self.finish_button.setMinimumHeight(DIM.BUTTON_HEIGHT_LG)
        self.finish_button.setMinimumWidth(180)
        self.finish_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.PRIMARY};
                color: {COLORS.ON_PRIMARY};
                {TYPO.BODY_MEDIUM}
                font-weight: bold;
                border: none;
                border-radius: {DIM.RADIUS_MD}px;
                padding: {SPACE.MD}px {SPACE.XL}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.PRIMARY_DARK};
            }}
        """)
        self.finish_button.clicked.connect(self.on_finish_clicked)
        layout.addWidget(self.finish_button)

        layout.addStretch()

        # Botão Próximo
        self.next_button = StandardButton("Próximo ▶")
        self.next_button.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
        self.next_button.setMinimumWidth(120)
        self.next_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.BORDER_VARIANT};
                color: {COLORS.TEXT_PRIMARY_VARIANT};
                {TYPO.BODY_MEDIUM}
                font-weight: 600;
                border: none;
                border-radius: {DIM.RADIUS_SM}px;
                padding: {SPACE.SM}px {SPACE.LG}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.BORDER};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.BORDER};
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        self.next_button.clicked.connect(self.on_next_clicked)
        layout.addWidget(self.next_button)

        return widget

    def _load_current_defect(self):
        """Carrega defeito atual na interface"""
        if not self.defects:
            return

        defect = self.defects[self.current_index]

        # Atualiza informações
        self.info_position.setText(
            f"Posição: X={defect.get('position', {}).get('x', '--')}, "
            f"Y={defect.get('position', {}).get('y', '--')}"
        )

        self.info_type.setText(f"Tipo: {defect.get('type', '--').upper()}")

        # Status colorido
        percentage = defect.get('percentage_open', 0)
        if percentage < 70:
            status_text = "BLOQUEADA"
            status_color = COLORS.ERROR_DARK
        elif percentage < 90:
            status_text = "PARCIAL"
            status_color = COLORS.WARNING
        else:
            status_text = "OK"
            status_color = COLORS.SUCCESS

        self.info_status.setText(f"Status: {status_text}")
        self.info_status.setStyleSheet(f"color: {status_color}; font-size: {TYPO.BODY_SMALL}px; font-weight: bold;")

        self.info_percentage.setText(f"Abertura: {percentage}%")

        # Análise do sistema
        system_text = f"""
Área esperada: {defect.get('area_expected', '--')} mm²
Área observada: {defect.get('area_observed', '--')} mm²
% Aberta: {percentage}%

Status: {status_text}
        """.strip()

        self.system_details.setText(system_text)

        # Carrega imagem
        image_path = defect.get('image_path', '')
        if image_path:
            self.image_preview.set_image(image_path)

        # Recarrega anotação e tipo se já foram preenchidos
        self.notes_input.setText(self.annotations[self.current_index])
        current_type = self.selected_types[self.current_index]
        if current_type:
            index = self.defect_type_combo.findText(current_type)
            if index >= 0:
                self.defect_type_combo.setCurrentIndex(index)
        else:
            self.defect_type_combo.setCurrentIndex(0)

        # Atualiza barra de progresso
        progress_text = f"Defeito {self.current_index + 1} de {len(self.defects)} " \
                        f"({self._get_analyzed_count()} analisados)"
        self.progress_label.setText(progress_text)

        # Atualiza botões de navegação
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < len(self.defects) - 1)

    def _get_analyzed_count(self) -> int:
        """Retorna quantidade de defeitos já julgados"""
        return sum(1 for j in self.judgments if j is not None)

    def on_previous_clicked(self):
        """Handler: Botão Anterior clicado"""
        if self.current_index > 0:
            # Salva estado atual antes de mudar
            self._save_current_state()

            # Move para anterior
            self.current_index -= 1
            self._load_current_defect()

    def on_next_clicked(self):
        """Handler: Botão Próximo clicado"""
        if self.current_index < len(self.defects) - 1:
            # Salva estado atual antes de mudar
            self._save_current_state()

            # Move para próximo
            self.current_index += 1
            self._load_current_defect()

    def _save_current_state(self):
        """Salva anotação e tipo do defeito atual"""
        # Salva anotação
        self.annotations[self.current_index] = self.notes_input.text().strip()

        # Salva tipo selecionado
        if self.defect_type_combo.currentIndex() > 0:
            self.selected_types[self.current_index] = self.defect_type_combo.currentText()
        else:
            self.selected_types[self.current_index] = ""

    def on_approve_clicked(self):
        """Handler: Botão Aprovar clicado (Falha Falsa)"""
        # Salva estado atual
        self._save_current_state()

        # Registra julgamento
        self.judgments[self.current_index] = "approved"

        logger.info(
            f"Defeito {self.current_index + 1} aprovado (falha falsa) "
            f"por {self.session_data.get('operator')}"
        )

        # Move para próximo ou finaliza
        if self.current_index < len(self.defects) - 1:
            self.current_index += 1
            self._load_current_defect()
        else:
            # Último defeito, finaliza
            self.on_finish_clicked()

    def on_confirm_clicked(self):
        """Handler: Botão Confirmar clicado (Defeito Real)"""
        # Salva estado atual
        self._save_current_state()

        # Verifica se tipo foi selecionado
        if self.defect_type_combo.currentIndex() <= 0:
            QMessageBox.warning(
                self,
                "Tipo de Defeito",
                "Por favor, selecione o tipo de defeito antes de confirmar."
            )
            return

        # Registra julgamento
        self.judgments[self.current_index] = "confirmed"

        logger.info(
            f"Defeito {self.current_index + 1} confirmado como real "
            f"por {self.session_data.get('operator')}"
        )

        # Move para próximo ou finaliza
        if self.current_index < len(self.defects) - 1:
            self.current_index += 1
            self._load_current_defect()
        else:
            # Último defeito, finaliza
            self.on_finish_clicked()

    def on_finish_clicked(self):
        """Handler: Botão Finalizar Análise clicado"""
        # Salva estado atual
        self._save_current_state()

        # Verifica se todos foram julgados
        unjudged = [i for i, j in enumerate(self.judgments) if j is None]

        if unjudged:
            reply = QMessageBox.question(
                self,
                "Defeitos Não Julgados",
                f"{len(unjudged)} defeito(s) não foi(ram) julgado(s).\n\n"
                "Deseja finalizar mesmo assim?\n\n"
                "(Defeitos não julgados serão considerados como confirmados)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                return

            # Considera não julgados como confirmados
            for i in unjudged:
                self.judgments[i] = "confirmed"

        # Conta resultados
        approved_count = sum(1 for j in self.judgments if j == "approved")
        confirmed_count = sum(1 for j in self.judgments if j == "confirmed")

        logger.info(
            f"Análise completa: {approved_count} aprovados, "
            f"{confirmed_count} confirmados"
        )

        # Se há defeitos confirmados, mostra dialog de decisão final
        if confirmed_count > 0:
            # Prepara listas
            defects_approved = [
                {**self.defects[i], "judgment": "approved",
                 "annotation": self.annotations[i], "defect_type": self.selected_types[i]}
                for i, j in enumerate(self.judgments) if j == "approved"
            ]

            defects_confirmed = [
                {**self.defects[i], "judgment": "confirmed",
                 "annotation": self.annotations[i], "defect_type": self.selected_types[i]}
                for i, j in enumerate(self.judgments) if j == "confirmed"
            ]

            # Mostra dialog de decisão final
            decision_dialog = FinalDecisionDialog(
                session_data=self.session_data,
                defects_confirmed=defects_confirmed,
                defects_approved=defects_approved,
                parent=self
            )

            # Conecta sinais
            decision_dialog.decision_discarded.connect(self._on_decision_discarded)
            decision_dialog.decision_rejected.connect(self._on_decision_rejected)

            # Executa como modal
            decision_dialog.exec()

        else:
            # Todos aprovados - salva automaticamente
            self._auto_approve()

    def _on_decision_discarded(self, session_data: dict):
        """Handler: Usuário escolheu descartar"""
        logger.info("Inspeção descartada pelo usuário")

        # Prepara resultados
        results = self._prepare_results("DISCARDED")

        # Emite sinal de análise completa
        self.analysis_completed.emit(results)

        # Fecha dialog
        self.accept()

    def _on_decision_rejected(self, session_data: dict):
        """Handler: Usuário escolheu reprovar"""
        logger.info("Inspeção reprovada pelo usuário")

        # Prepara resultados
        results = self._prepare_results("REJECTED")

        # Emite sinal de análise completa
        self.analysis_completed.emit(results)

        # Fecha dialog
        self.accept()

    def _auto_approve(self):
        """Salva automaticamente quando todos defeitos foram aprovados"""
        # Registra no audit log
        from aoi_lib.audit_log import get_audit_log
        audit_log = get_audit_log()

        defects_judged = {
            "false_alarms": sum(1 for j in self.judgments if j == "approved"),
            "confirmed_real": sum(1 for j in self.judgments if j == "confirmed")
        }

        audit_log.log_user_approved(
            session_id=self.session_data.get("session_id", "UNKNOWN"),
            operator=self.session_data.get("operator", "Unknown"),
            stencil_code=self.session_data.get("stencil_code", "UNKNOWN"),
            session_type=self.session_data.get("session_type", "Unknown"),
            defects_judged=defects_judged
        )

        # Prepara resultados
        results = self._prepare_results("APPROVED_USER")

        # Mensagem de sucesso
        QMessageBox.information(
            self,
            "Análise Completa",
            f"✅ Todos os {len(self.defects)} defeitos foram julgados como falhas falsas.\n\n"
            f"A inspeção será salva no histórico como APROVADA COM JULGAMENTO."
        )

        # Emite sinal
        self.analysis_completed.emit(results)

        # Fecha
        self.accept()

    def _prepare_results(self, final_status: str) -> dict:
        """Prepara dicionário de resultados"""
        defects_approved = [
            {**self.defects[i], "judgment": "approved",
             "annotation": self.annotations[i], "defect_type": self.selected_types[i]}
            for i, j in enumerate(self.judgments) if j == "approved"
        ]

        defects_confirmed = [
            {**self.defects[i], "judgment": "confirmed",
             "annotation": self.annotations[i], "defect_type": self.selected_types[i]}
            for i, j in enumerate(self.judgments) if j == "confirmed"
        ]

        return {
            "final_status": final_status,
            "defects_approved": defects_approved,
            "defects_confirmed": defects_confirmed,
            "total_defects": len(self.defects),
            "approved_count": len(defects_approved),
            "confirmed_count": len(defects_confirmed),
            "session_data": self.session_data
        }
