"""
Inspection Windows Configuration Widget for Engineering Workflow.

This widget provides UI for configuring inspection windows (apertures) from Gerber,
including grouping, threshold configuration, library management, and exception handling.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTreeWidget, QTreeWidgetItem, QGroupBox,
    QLabel, QPushButton, QSpinBox, QDoubleSpinBox,
    QComboBox, QCheckBox, QSplitter, QFrame,
    QScrollArea, QMessageBox, QFileDialog, QDialog,
    QProgressBar, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QImage, QBrush, QColor

from consumo_lib.models.inspection_window import (
    InspectionWindow,
    WindowConfig,
    WindowGroup,
    WindowLibrary,
    WindowStatus,
    BinarizationMethod,
    PreprocessMethod,
    GroupingCriteria,
    create_groups_from_windows,
    create_default_config
)
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

logger = logging.getLogger(__name__)


# ============================================================================
# PREVIEW WIDGET
# ============================================================================

class WindowPreviewWidget(QWidget):
    """
    Widget for displaying preview of inspection windows.

    Shows visual representation of apertures with their configuration status.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.windows: List[InspectionWindow] = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("Preview Visual (3 exemplos)")
        title.setStyleSheet(f"font-weight: bold; color: {COLORS.ON_SURFACE};")
        layout.addWidget(title)

        # Preview area
        self.preview_area = QWidget()
        self.preview_area.setMinimumHeight(150)
        self.preview_area.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.SURFACE};
                border: 1px solid {COLORS.OUTLINE};
                border-radius: {DIM.RADIUS_SM}px;
            }}
        """)
        preview_layout = QHBoxLayout(self.preview_area)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.preview_area)

        # Status label
        self.status_label = QLabel("Nenhum grupo selecionado")
        self.status_label.setStyleSheet(f"color: {COLORS.ON_SURFACE}; {TYPO.BODY_SMALL}")
        layout.addWidget(self.status_label)

    def set_windows(self, windows: List[InspectionWindow]) -> None:
        """Update preview with windows."""
        self.windows = windows[:3]  # Show max 3 examples
        self._update_preview()

    def _update_preview(self) -> None:
        """Update preview display."""
        # Clear existing
        for i in reversed(range(self.preview_area.layout().count())):
            self.preview_area.layout().itemAt(i).widget().setParent(None)

        if not self.windows:
            self.status_label.setText("Nenhum grupo selecionado")
            return

        # Add previews
        for i, window in enumerate(self.windows):
            preview = self._create_window_preview(window, i)
            self.preview_area.layout().addWidget(preview)

        self.status_label.setText(f"Mostrando {len(self.windows)} exemplos do grupo")

    def _create_window_preview(self, window: InspectionWindow, index: int) -> QWidget:
        """Create preview widget for single window."""
        widget = QWidget()
        widget.setMinimumSize(80, 80)
        widget.setMaximumSize(120, 120)

        # Determine border color based on status
        status_colors = {
            WindowStatus.NOT_CONFIGURED: "#9E9E9E",  # Gray
            WindowStatus.CONFIGURED: "#4CAF50",  # Green
            WindowStatus.CONFIRMED: "#1976D2"  # Blue
        }
        border_color = status_colors.get(window.status, "#9E9E9E")

        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS.BACKGROUND};
                border: 2px solid {border_color};
                border-radius: {DIM.RADIUS_MD}px;
            }}
        """)

        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Status icon
        status_icons = {
            WindowStatus.NOT_CONFIGURED: "⚪",
            WindowStatus.CONFIGURED: "🟢",
            WindowStatus.CONFIRMED: "✅"
        }
        icon_label = QLabel(status_icons.get(window.status, "⚪"))
        icon_label.setStyleSheet("font-size: 24px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Window info
        info_label = QLabel(f"ID: {window.id}\n{window.kind}")
        info_label.setStyleSheet(f"{TYPO.BODY_SMALL}; color: {COLORS.ON_SURFACE};")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        return widget


# ============================================================================
# CONFIGURATION PANEL
# ============================================================================

class GroupConfigPanel(QWidget):
    """
    Panel for configuring inspection window groups.

    Provides controls for thresholds, binarization, and preprocessing.
    """

    config_changed = pyqtSignal(object)  # Emitted when config changes
    confirm_clicked = pyqtSignal()  # Emitted when user confirms config
    exception_clicked = pyqtSignal()  # Emitted when user adds exception
    library_save_clicked = pyqtSignal(str, object)  # Emitted when saving to library

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_group: Optional[WindowGroup] = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Group info
        self.group_info_label = QLabel("Nenhum grupo selecionado")
        self.group_info_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {COLORS.PRIMARY};
            padding: {SPACE.XS}px;
            background-color: {COLORS.SECONDARY_LIGHT};
            border-radius: {DIM.RADIUS_SM}px;
        """)
        layout.addWidget(self.group_info_label)

        # Thresholds section
        thresholds_group = QGroupBox("Thresholds")
        thresholds_layout = QGridLayout()

        # OK threshold
        thresholds_layout.addWidget(QLabel("✅ OK ≥"), 0, 0)
        self.ok_threshold_spin = QDoubleSpinBox()
        self.ok_threshold_spin.setRange(0.0, 100.0)
        self.ok_threshold_spin.setValue(90.0)
        self.ok_threshold_spin.setSuffix(" %")
        self.ok_threshold_spin.valueChanged.connect(self._on_config_changed)
        thresholds_layout.addWidget(self.ok_threshold_spin, 0, 1)

        # Partial threshold
        thresholds_layout.addWidget(QLabel("⚠️ PARTIAL ≥"), 1, 0)
        self.partial_threshold_spin = QDoubleSpinBox()
        self.partial_threshold_spin.setRange(0.0, 100.0)
        self.partial_threshold_spin.setValue(70.0)
        self.partial_threshold_spin.setSuffix(" %")
        self.partial_threshold_spin.valueChanged.connect(self._on_config_changed)
        thresholds_layout.addWidget(self.partial_threshold_spin, 1, 1)

        # Blocked note
        blocked_label = QLabel("❌ BLOQUEADO < threshold PARTIAL")
        blocked_label.setStyleSheet(f"color: {COLORS.ERROR}; {TYPO.BODY_SMALL}")
        thresholds_layout.addWidget(blocked_label, 2, 0, 1, 2)

        thresholds_group.setLayout(thresholds_layout)
        layout.addWidget(thresholds_group)

        # Binarization section
        binarization_group = QGroupBox("Binarização")
        binarization_layout = QGridLayout()

        binarization_layout.addWidget(QLabel("Método:"), 0, 0)
        self.binarization_combo = QComboBox()
        self.binarization_combo.addItems(["Otsu", "Adaptativo", "Fixed"])
        self.binarization_combo.currentIndexChanged.connect(self._on_config_changed)
        binarization_layout.addWidget(self.binarization_combo, 0, 1)

        binarization_layout.addWidget(QLabel("Pré-process:"), 1, 0)
        self.preprocess_combo = QComboBox()
        self.preprocess_combo.addItems(["Blur", "Denoise", "Median", "Nenhum"])
        self.preprocess_combo.currentIndexChanged.connect(self._on_config_changed)
        binarization_layout.addWidget(self.preprocess_combo, 1, 1)

        binarization_group.setLayout(binarization_layout)
        layout.addWidget(binarization_group)

        # Preview
        self.preview_widget = WindowPreviewWidget()
        layout.addWidget(self.preview_widget)

        # Apply checkbox
        self.apply_all_checkbox = QCheckBox("Aplicar a todas do grupo")
        self.apply_all_checkbox.setChecked(True)
        self.apply_all_checkbox.setStyleSheet(f"color: {COLORS.ON_SURFACE}; padding: {SPACE.XS}px;")
        layout.addWidget(self.apply_all_checkbox)

        # Buttons
        button_layout = QGridLayout()

        self.confirm_btn = QPushButton("Confirmar Grupo ✅")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self._on_confirm)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS.SUCCESS};
                color: white;
                font-weight: bold;
                padding: {SPACE.XS}px;
                border-radius: {DIM.RADIUS_SM}px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.SUCCESS_DARK};
            }}
            QPushButton:disabled {{
                background-color: {COLORS.TEXT_DISABLED};
            }}
        """)
        button_layout.addWidget(self.confirm_btn, 0, 0)

        self.exception_btn = QPushButton("Adicionar Exceção ⚙️")
        self.exception_btn.setEnabled(False)
        self.exception_btn.clicked.connect(self._on_exception)
        button_layout.addWidget(self.exception_btn, 0, 1)

        self.save_library_btn = QPushButton("Salvar na Biblioteca 💾")
        self.save_library_btn.setEnabled(False)
        self.save_library_btn.clicked.connect(self._on_save_library)
        button_layout.addWidget(self.save_library_btn, 1, 0, 1, 2)

        layout.addLayout(button_layout)
        layout.addStretch()

    def set_group(self, group: Optional[WindowGroup]) -> None:
        """Set current group and update UI."""
        self.current_group = group

        if not group:
            self.group_info_label.setText("Nenhum grupo selecionado")
            self.confirm_btn.setEnabled(False)
            self.exception_btn.setEnabled(False)
            self.save_library_btn.setEnabled(False)
            self.preview_widget.set_windows([])
            return

        # Update info
        status_text = {
            WindowStatus.NOT_CONFIGURED: "⚪ Não configurado",
            WindowStatus.CONFIGURED: "🟢 Configurado",
            WindowStatus.CONFIRMED: "✅ Confirmado"
        }

        self.group_info_label.setText(
            f"Grupo: {group.name}\n"
            f"Quantidade: {group.count} aberturas | "
            f"Status: {status_text.get(group.status, '⚪')}"
        )

        # Load existing config if available
        if group.config:
            self._load_config(group.config)

        # Update preview
        self.preview_widget.set_windows(group.windows)

        # Enable buttons
        self.confirm_btn.setEnabled(True)
        self.exception_btn.setEnabled(len(group.windows) > 0)
        self.save_library_btn.setEnabled(True)

    def _load_config(self, config: WindowConfig) -> None:
        """Load configuration into UI controls."""
        self.ok_threshold_spin.setValue(config.ok_threshold)
        self.partial_threshold_spin.setValue(config.partial_threshold)

        binarization_index = self.binarization_combo.findText(
            config.binarization_method.value.title()
        )
        if binarization_index >= 0:
            self.binarization_combo.setCurrentIndex(binarization_index)

        preprocess_index = self.preprocess_combo.findText(
            config.preprocess_method.value.title()
        )
        if preprocess_index >= 0:
            self.preprocess_combo.setCurrentIndex(preprocess_index)

    def get_config(self) -> Optional[WindowConfig]:
        """Get current configuration from UI."""
        # Validate thresholds
        if self.partial_threshold_spin.value() >= self.ok_threshold_spin.value():
            QMessageBox.warning(
                self,
                "Configuração Inválida",
                "Threshold PARTIAL deve ser menor que threshold OK"
            )
            return None

        # Get binarization method
        binarization_map = {
            "Otsu": BinarizationMethod.OTSU,
            "Adaptativo": BinarizationMethod.ADAPTIVE,
            "Fixed": BinarizationMethod.FIXED
        }

        # Get preprocess method
        preprocess_map = {
            "Blur": PreprocessMethod.BLUR,
            "Denoise": PreprocessMethod.DENOISE,
            "Median": PreprocessMethod.MEDIAN,
            "Nenhum": PreprocessMethod.NONE
        }

        return WindowConfig(
            ok_threshold=self.ok_threshold_spin.value(),
            partial_threshold=self.partial_threshold_spin.value(),
            binarization_method=binarization_map.get(
                self.binarization_combo.currentText(),
                BinarizationMethod.OTSU
            ),
            preprocess_method=preprocess_map.get(
                self.preprocess_combo.currentText(),
                PreprocessMethod.BLUR
            )
        )

    def _on_config_changed(self) -> None:
        """Handle configuration change."""
        config = self.get_config()
        if config:
            self.config_changed.emit(config)

    def _on_confirm(self) -> None:
        """Handle confirm button click."""
        if not self.current_group:
            return

        config = self.get_config()
        if not config:
            return

        apply_all = self.apply_all_checkbox.isChecked()
        self.current_group.apply_config_to_group(config, confirm=True)
        self.confirm_clicked.emit()

    def _on_exception(self) -> None:
        """Handle exception button click."""
        self.exception_clicked.emit()

    def _on_save_library(self) -> None:
        """Handle save to library button click."""
        if not self.current_group:
            return

        config = self.get_config()
        if not config:
            return

        self.library_save_clicked.emit(self.current_group.key, config)


# ============================================================================
# LIBRARY PANEL
# ============================================================================

class LibraryPanel(QWidget):
    """
    Panel for managing configuration library.

    Allows saving, loading, and managing reusable configurations.
    """

    config_loaded = pyqtSignal(str, object)  # Emitted when config loaded from library

    def __init__(self, parent=None):
        super().__init__(parent)
        self.library: WindowLibrary = WindowLibrary()
        self.library_path = Path("data/inspection_config_library.json")
        self._load_library()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("📚 Biblioteca de Configs")
        title.setStyleSheet(f"font-weight: bold; color: {COLORS.PRIMARY}; padding: {SPACE.XXS}px;")
        layout.addWidget(title)

        # Library list
        self.library_tree = QTreeWidget()
        self.library_tree.setHeaderLabel("Configurações Salvas")
        self.library_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.library_tree)

        # Buttons
        button_layout = QHBoxLayout()

        self.load_btn = QPushButton("Carregar no Grupo")
        self.load_btn.setEnabled(False)
        self.load_btn.clicked.connect(self._on_load)
        button_layout.addWidget(self.load_btn)

        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setToolTip("Recarregar biblioteca")
        self.refresh_btn.clicked.connect(self._load_library)
        button_layout.addWidget(self.refresh_btn)

        layout.addLayout(button_layout)

        # Info
        info_label = QLabel(
            "Dica: Configurações são aplicadas\n"
            "automaticamente baseadas no nome\n"
            "do grupo (dimensão + forma)."
        )
        info_label.setStyleSheet(f"color: {COLORS.ON_SURFACE}; {TYPO.BODY_SMALL}; padding: {SPACE.XXS}px;")
        layout.addWidget(info_label)

        # Update display
        self._update_library_display()

    def _load_library(self) -> None:
        """Load library from file."""
        try:
            if self.library_path.exists():
                self.library = WindowLibrary.load(self.library_path)
                logger.info(f"Loaded {len(self.library.configs)} library configs")
                self._update_library_display()
        except Exception as e:
            logger.error(f"Error loading library: {e}")

    def _save_library(self) -> None:
        """Save library to file."""
        try:
            self.library_path.parent.mkdir(parents=True, exist_ok=True)
            self.library.save(self.library_path)
        except Exception as e:
            logger.error(f"Error saving library: {e}")

    def add_config(self, key: str, config: WindowConfig) -> None:
        """Add configuration to library."""
        self.library.add_config(key, config)
        self._save_library()
        self._update_library_display()

    def _update_library_display(self) -> None:
        """Update library tree display."""
        self.library_tree.clear()

        for key, config in sorted(self.library.configs.items()):
            item = QTreeWidgetItem()
            item.setText(0, f"⚙️ {key}")
            item.setData(0, Qt.ItemDataRole.UserRole, key)

            # Add details as child
            details = QTreeWidgetItem()
            details.setText(0, str(config))
            item.addChild(details)

            self.library_tree.addTopLevelItem(item)

        self.library_tree.expandAll()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on library item."""
        key = item.data(0, Qt.ItemDataRole.UserRole)
        if key and key in self.library.configs:
            self._on_load()

    def _on_load(self) -> None:
        """Load selected configuration."""
        current_item = self.library_tree.currentItem()
        if not current_item:
            return

        key = current_item.data(0, Qt.ItemDataRole.UserRole)
        if key and key in self.library.configs:
            config = self.library.configs[key]
            self.config_loaded.emit(key, config)

    def suggest_config(self, group_key: str) -> Optional[WindowConfig]:
        """Suggest configuration for group."""
        return self.library.suggest_config(group_key)


# ============================================================================
# MAIN WIDGET
# ============================================================================

class InspectionWindowsWidget(QWidget):
    """
    Main widget for inspection windows configuration.

    Provides comprehensive UI for:
    - Loading windows from Gerber
    - Auto-grouping by dimensions
    - Configuring thresholds per group
    - Managing exceptions
    - Library management
    """

    # Signals for wizard integration
    validation_changed = pyqtSignal(bool)  # Emitted when validation status changes
    group_count_changed = pyqtSignal(int)  # Emitted when number of groups changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.gerber_objects: List[Any] = []  # GerberObject list
        self.windows: List[InspectionWindow] = []
        self.groups: List[WindowGroup] = []
        self.library = WindowLibrary()

        self.read_only_mode = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup UI layout."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # LEFT PANEL: Groups tree + library
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Groups section
        groups_group = QGroupBox("📦 Lista de Grupos")
        groups_layout = QVBoxLayout()

        # Groups tree
        self.groups_tree = QTreeWidget()
        self.groups_tree.setHeaderLabels(["Grupo", "Status", "Qtd"])
        self.groups_tree.setColumnWidth(0, 200)
        self.groups_tree.setColumnWidth(1, 100)
        self.groups_tree.setColumnWidth(2, 60)
        self.groups_tree.itemSelectionChanged.connect(self._on_group_selected)
        groups_layout.addWidget(self.groups_tree)

        # Tree controls
        tree_controls = QHBoxLayout()

        self.expand_all_btn = QPushButton("Expandir Todos")
        self.expand_all_btn.clicked.connect(self.groups_tree.expandAll)
        tree_controls.addWidget(self.expand_all_btn)

        self.collapse_all_btn = QPushButton("Recolher Todos")
        self.collapse_all_btn.clicked.connect(self.groups_tree.collapseAll)
        tree_controls.addWidget(self.collapse_all_btn)

        self.auto_group_btn = QPushButton("Auto-Agrupar")
        self.auto_group_btn.clicked.connect(self._auto_group)
        tree_controls.addWidget(self.auto_group_btn)

        groups_layout.addLayout(tree_controls)
        groups_group.setLayout(groups_layout)
        left_layout.addWidget(groups_group)

        # Library section
        self.library_panel = LibraryPanel()
        left_layout.addWidget(self.library_panel)

        # Add left panel to splitter
        splitter.addWidget(left_panel)

        # RIGHT PANEL: Configuration
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.config_panel = GroupConfigPanel()
        right_layout.addWidget(self.config_panel)

        # Add right panel to splitter
        splitter.addWidget(right_panel)

        # Set initial splitter sizes (40% left, 60% right)
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter)

    def _connect_signals(self):
        """Connect internal signals."""
        self.config_panel.config_changed.connect(self._on_config_changed)
        self.config_panel.confirm_clicked.connect(self._on_group_confirmed)
        self.config_panel.exception_clicked.connect(self._on_add_exception)
        self.config_panel.library_save_clicked.connect(self._on_save_to_library)
        self.library_panel.config_loaded.connect(self._on_library_config_loaded)

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def load_from_gerber(self, gerber_objects: List[Any]) -> None:
        """
        Load inspection windows from Gerber objects.

        Args:
            gerber_objects: List of GerberObject instances
        """
        self.gerber_objects = gerber_objects
        self.windows = [
            InspectionWindow.from_gerber_object(obj)
            for obj in gerber_objects
        ]

        logger.info(f"Loaded {len(self.windows)} windows from Gerber")

        # Auto-group on load
        self._auto_group()

    def set_read_only(self, read_only: bool) -> None:
        """Set read-only mode (for Base programs)."""
        self.read_only_mode = read_only

        # Disable controls
        self.config_panel.setEnabled(not read_only)
        self.auto_group_btn.setEnabled(not read_only)
        self.expand_all_btn.setEnabled(not read_only)
        self.collapse_all_btn.setEnabled(not read_only)

    def validate(self) -> bool:
        """
        Validate configuration.

        Returns:
            True if all groups have configuration
        """
        if not self.groups:
            return False

        return all(
            group.config is not None and group.config.validate()
            for group in self.groups
        )

    def get_configurations(self) -> Dict[int, WindowConfig]:
        """
        Get all window configurations.

        Returns:
            Dictionary mapping window ID to configuration
        """
        configs = {}

        for group in self.groups:
            for window in group.windows:
                if window.config:
                    configs[window.id] = window.config

        return configs

    def get_groups(self) -> List[WindowGroup]:
        """Get all groups."""
        return self.groups

    # ========================================================================
    # INTERNAL METHODS
    # ========================================================================

    def _auto_group(self) -> None:
        """Perform automatic grouping of windows."""
        if not self.windows:
            QMessageBox.warning(
                self,
                "Sem Janelas",
                "Carregue um arquivo Gerber primeiro."
            )
            return

        # Create groups
        self.groups = create_groups_from_windows(
            self.windows,
            criteria=GroupingCriteria.EXACT_DIMENSIONS
        )

        logger.info(f"Auto-grouped into {len(self.groups)} groups")

        # Apply library suggestions
        self._apply_library_suggestions()

        # Update display
        self._update_groups_tree()

        # Emit signals
        self.group_count_changed.emit(len(self.groups))
        self.validation_changed.emit(self.validate())

    def _apply_library_suggestions(self) -> None:
        """Apply library suggestions to groups."""
        for group in self.groups:
            suggested = self.library_panel.suggest_config(group.key)
            if suggested:
                group.config = suggested
                group.status = WindowStatus.CONFIGURED
                for window in group.windows:
                    if not window.is_exception:
                        window.config = suggested
                        window.status = WindowStatus.CONFIGURED

    def _update_groups_tree(self) -> None:
        """Update groups tree display."""
        self.groups_tree.clear()

        for group in self.groups:
            # Group item
            group_item = QTreeWidgetItem()
            group_item.setText(0, f"📦 {group.name}")
            group_item.setData(0, Qt.ItemDataRole.UserRole, group)

            # Status
            status_icons = {
                WindowStatus.NOT_CONFIGURED: "⚪",
                WindowStatus.CONFIGURED: "🟢",
                WindowStatus.CONFIRMED: "✅"
            }
            group_item.setText(1, status_icons.get(group.status, "⚪"))

            # Count
            group_item.setText(2, f"({group.count})")

            self.groups_tree.addTopLevelItem(group_item)

            # Standard windows sub-item
            if group.standard_count > 0:
                standard_item = QTreeWidgetItem()
                standard_item.setText(0, f"  └─ Padrão ({group.standard_count})")
                group_item.addChild(standard_item)

            # Exceptions sub-item
            if group.exception_count > 0:
                exception_item = QTreeWidgetItem()
                exception_item.setText(0, f"  └─ ⚙️ Exceções ({group.exception_count})")
                group_item.addChild(exception_item)

                # Add individual exception windows
                for window_id in group.exceptions:
                    window = group.get_window_by_id(window_id)
                    if window:
                        window_item = QTreeWidgetItem()
                        window_item.setText(0, f"     └─ ⚙️ ID={window.id}")
                        window_item.setData(0, Qt.ItemDataRole.UserRole, window)
                        exception_item.addChild(window_item)

        self.groups_tree.expandAll()

    def _on_group_selected(self) -> None:
        """Handle group selection in tree."""
        current_item = self.groups_tree.currentItem()
        if not current_item:
            return

        # Get group or window from item
        data = current_item.data(0, Qt.ItemDataRole.UserRole)

        if isinstance(data, WindowGroup):
            self.config_panel.set_group(data)
        elif isinstance(data, InspectionWindow):
            # If individual window selected, show its config
            # For now, just find its group
            for group in self.groups:
                if group.get_window_by_id(data.id):
                    self.config_panel.set_group(group)
                    break

    def _on_config_changed(self, config: WindowConfig) -> None:
        """Handle configuration change."""
        # Update current group temporarily (preview)
        current_item = self.groups_tree.currentItem()
        if current_item:
            data = current_item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(data, WindowGroup):
                # Apply to group temporarily (not confirmed)
                for window in data.windows:
                    if not window.is_exception:
                        window.config = config
                        window.status = WindowStatus.CONFIGURED

    def _on_group_confirmed(self) -> None:
        """Handle group confirmation."""
        self._update_groups_tree()
        self.validation_changed.emit(self.validate())

        # Show confirmation message
        QMessageBox.information(
            self,
            "Grupo Confirmado",
            "Configuração do grupo confirmada com sucesso."
        )

    def _on_add_exception(self) -> None:
        """Handle adding exception to group."""
        # This would open a dialog to select specific windows
        # For now, just show placeholder
        QMessageBox.information(
            self,
            "Adicionar Exceção",
            "Funcionalidade de exceções será implementada.\n"
            "Permitirá selecionar janelas específicas para configuração individual."
        )

    def _on_save_to_library(self, key: str, config: WindowConfig) -> None:
        """Handle save to library."""
        self.library_panel.add_config(key, config)

        QMessageBox.information(
            self,
            "Salvo na Biblioteca",
            f"Configuração salva como '{key}' na biblioteca global."
        )

    def _on_library_config_loaded(self, key: str, config: WindowConfig) -> None:
        """Handle configuration loaded from library."""
        # Apply to currently selected group
        current_item = self.groups_tree.currentItem()
        if current_item:
            data = current_item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(data, WindowGroup):
                data.config = config
                data.status = WindowStatus.CONFIGURED
                for window in data.windows:
                    if not window.is_exception:
                        window.config = config
                        window.status = WindowStatus.CONFIGURED

                self.config_panel.set_group(data)
                self._update_groups_tree()
                self.validation_changed.emit(self.validate())
