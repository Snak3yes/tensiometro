# Plano de Implementação - FASE 1 & 2: Login e TreeView

**Data:** 2026-01-08
**Versão:** 1.0
**Status:** 🚀 Pronto para Implementação
**Fases:** FASE 1 (Login) + FASE 2 (TreeView)

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Estrutura de Arquivos](#estrutura-de-arquivos)
3. [FASE 1: Login (Autenticação)](#fase-1-login)
4. [FASE 2: TreeView (Nova Aba)](#fase-2-treeview)
5. [Ordem de Implementação](#ordem-de-implementação)
6. [Checklist Completo](#checklist-completo)
7. [Critérios de Aceite](#critérios-de-aceite)
8. [Testes Manuais](#testes-manuais)

---

## VISÃO GERAL

### Objetivo

Implementar as duas primeiras telas da interface do operador:
1. **LoginDialog** - Autenticação de usuário
2. **TreeViewTab** - Nova aba principal com lista de programas

### Escopo

**INCLUI:**
- Sistema de login simples (usuário/senha)
- Controle de acesso por perfil (Operador/Engenharia)
- TreeView com lista de programas
- Busca incremental
- Filtros básicos
- Painel de detalhes do stencil
- Status do hardware

**NÃO INCLUI:**
- Criptografia de senha (hash simples)
- Recuperação de senha
- Multi-idioma
- Edição de programas (apenas visualização)

### Premissas

1. **Backend:** `aoi_lib/` já tem lógica de negócio
2. **GUI Framework:** PyQt6 já instalado
3. **Dados:** Arquivos JSON em `data/stencils/`
4. **Hardware:** PLC, Tensiômetro, Câmera com controllers existentes

---

## ESTRUTURA DE ARQUIVOS

### Nova Estrutura Modular

```
consumo_lib/
├── main_window.py                 # ✅ Já existe (646 linhas)
│   └── ADICIONAR: Nova aba para TreeView
│
├── tabs/                          # ✅ Já existe
│   ├── __init__.py
│   ├── cnc_control_tab.py         # ✅ Já existe
│   ├── tension_tab.py             # ✅ Já existe
│   ├── inspection_tab.py          # ✅ Já existe
│   ├── tracking_tab.py            # ✅ Já existe
│   └── tree_view_tab.py           # ⭐ NOVA - FASE 2
│
├── widgets/                       # ✅ Já existe
│   ├── __init__.py
│   ├── camera_preview_widget.py   # ✅ Já existe
│   └── NOVOS WIDGETS:
│       ├── search_line_edit.py    # ⭐ NOVO - Busca incremental
│       ├── status_badge.py        # ⭐ NOVO - Badge de status
│       ├── hardware_status_bar.py # ⭐ NOVO - Barra de status hardware
│       └── defect_list_widget.py  # ⭐ NOVO - Lista de defeitos (futuro)
│
├── dialogs/                       # ✅ Já existe
│   ├── __init__.py
│   └── NOVOS DIALOGS:
│       ├── login_dialog.py        # ⭐ NOVO - FASE 1
│       ├── confirm_positioning_dialog.py  # ⭐ NOVO - FASE 3
│       └── mode_selection_dialog.py       # ⭐ NOVO - FASE 4
│
├── controllers/                   # ✅ Já existe
│   └── auth_controller.py         # ⭐ NOVO - Controle de autenticação
│
└── managers/                      # ✅ Já existe
    └── user_manager.py            # ⭐ NOVO - Gerenciamento de usuários

aoi_lib/
├── auth/                          # ⭐ NOVO MÓDULO
│   ├── __init__.py
│   ├── user.py                    # ⭐ NOVO - Modelo User
│   ├── auth_service.py            # ⭐ NOVO - Serviço de autenticação
│   └── user_database.py           # ⭐ NOVO - Persistência de usuários
│
└── config/
    └── users.json                 # ⭐ NOVO - Base de usuários

data/
└── users/
    └── users.json                 # ⭐ NOVO - Usuários do sistema
```

---

## FASE 1: LOGIN (AUTENTICAÇÃO)

### 1.1 Criar Modelo de Usuário

**Arquivo:** `aoi_lib/auth/user.py`

```python
from dataclasses import dataclass
from enum import Enum
from typing import List

class UserRole(Enum):
    OPERATOR = "operator"
    ENGINEERING = "engineering"
    ADMIN = "admin"

@dataclass
class User:
    username: str
    full_name: str
    role: UserRole
    is_active: bool = True

    def can_edit_programs(self) -> bool:
        return self.role in [UserRole.ENGINEERING, UserRole.ADMIN]

    def can_execute_programs(self) -> bool:
        return True  # Todos podem executar

    def can_view_history(self) -> bool:
        return True  # Todos podem ver histórico

# Permissões detalhadas
PERMISSIONS = {
    UserRole.OPERATOR: {
        "execute_programs": True,
        "edit_programs": False,
        "create_programs": False,
        "edit_system_config": False,
        "view_history": True,
        "generate_reports": True,
    },
    UserRole.ENGINEERING: {
        "execute_programs": True,
        "edit_programs": True,
        "create_programs": True,
        "edit_system_config": True,
        "view_history": True,
        "generate_reports": True,
    },
    UserRole.ADMIN: {
        "execute_programs": True,
        "edit_programs": True,
        "create_programs": True,
        "edit_system_config": True,
        "view_history": True,
        "generate_reports": True,
        "manage_users": True,
    }
}
```

### 1.2 Criar Serviço de Autenticação

**Arquivo:** `aoi_lib/auth/auth_service.py`

```python
import hashlib
import json
from pathlib import Path
from typing import Optional
from .user import User, UserRole

class AuthService:
    def __init__(self, users_file: Path = None):
        self.users_file = users_file or Path("data/users/users.json")
        self.current_user: Optional[User] = None
        self._users = {}
        self._load_users()

    def _load_users(self):
        """Carrega usuários do arquivo JSON"""
        if not self.users_file.exists():
            self._create_default_users()

        with open(self.users_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for username, user_data in data['users'].items():
                self._users[username] = {
                    'password_hash': user_data['password_hash'],
                    'full_name': user_data['full_name'],
                    'role': UserRole(user_data['role']),
                    'is_active': user_data.get('is_active', True)
                }

    def _create_default_users(self):
        """Cria usuários padrão se arquivo não existir"""
        self.users_file.parent.mkdir(parents=True, exist_ok=True)

        default_users = {
            "operator": {
                "password_hash": self._hash_password("operator123"),
                "full_name": "Operador Padrão",
                "role": "operator",
                "is_active": True
            },
            "eng": {
                "password_hash": self._hash_password("eng123"),
                "full_name": "Engenheiro de Processo",
                "role": "engineering",
                "is_active": True
            },
            "admin": {
                "password_hash": self._hash_password("admin123"),
                "full_name": "Administrador",
                "role": "admin",
                "is_active": True
            }
        }

        data = {"users": default_users}
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _hash_password(self, password: str) -> str:
        """Hash simples de senha (SHA-256)"""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate(self, username: str, password: str) -> bool:
        """Autentica usuário"""
        if username not in self._users:
            return False

        user_data = self._users[username]
        password_hash = self._hash_password(password)

        if user_data['password_hash'] != password_hash:
            return False

        if not user_data['is_active']:
            return False

        # Cria objeto User e define como atual
        self.current_user = User(
            username=username,
            full_name=user_data['full_name'],
            role=user_data['role'],
            is_active=user_data['is_active']
        )

        return True

    def logout(self):
        """Logout do usuário atual"""
        self.current_user = None

    def is_authenticated(self) -> bool:
        """Verifica se há usuário autenticado"""
        return self.current_user is not None

    def get_current_user(self) -> Optional[User]:
        """Retorna usuário autenticado"""
        return self.current_user
```

### 1.3 Criar Dialog de Login

**Arquivo:** `consumo_lib/dialogs/login_dialog.py`

```python
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from aoi_lib.auth.auth_service import AuthService

class LoginDialog(QDialog):
    """Dialog de login do sistema"""

    login_successful = pyqtSignal()  # Sinal emitido ao fazer login

    def __init__(self, auth_service: AuthService, parent=None):
        super().__init__(parent)
        self.auth_service = auth_service
        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("TENSIO METRO - Login")
        self.setModal(True)
        self.setFixedSize(450, 350)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Logo/Título
        title_label = QLabel("TENSIO METRO")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Sistema de Inspeção de Stencils")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(20)

        # Campo de usuário
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuário")
        self.username_input.setMinimumHeight(40)
        layout.addWidget(QLabel("Usuário:"))
        layout.addWidget(self.username_input)

        # Campo de senha
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        layout.addWidget(QLabel("Senha:"))
        layout.addWidget(self.password_input)

        layout.addSpacing(10)

        # Botões
        buttons_layout = QHBoxLayout()

        self.login_button = QPushButton("Entrar")
        self.login_button.setMinimumHeight(45)
        self.login_button.clicked.connect(self.on_login_clicked)
        buttons_layout.addWidget(self.login_button)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setMinimumHeight(45)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

        # Versão
        version_label = QLabel("Versão 0.4.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #888;")
        layout.addWidget(version_label)

        # Conexões
        self.password_input.returnPressed.connect(self.on_login_clicked)

        # Focus inicial
        self.username_input.setFocus()

    def on_login_clicked(self):
        """Processa clique no botão Entrar"""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self,
                "Campo Vazio",
                "Por favor, preencha todos os campos.",
                QMessageBox.StandardButton.Ok
            )
            return

        if self.auth_service.authenticate(username, password):
            # Login bem-sucedido
            self.login_successful.emit()
            self.accept()
        else:
            # Login falhou
            QMessageBox.critical(
                self,
                "Erro de Autenticação",
                "Usuário ou senha incorretos.",
                QMessageBox.StandardButton.Ok
            )
            self.password_input.clear()
            self.password_input.setFocus()

    def show_error(self, message: str):
        """Exibe mensagem de erro"""
        QMessageBox.critical(self, "Erro", message)
```

### 1.4 Integrar Login no MainWindow

**Arquivo:** `consumo_lib/main_window.py`

**Adicionar no __init__:**

```python
from aoi_lib.auth.auth_service import AuthService
from consumo_lib.dialogs.login_dialog import LoginDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Inicializa serviço de autenticação
        self.auth_service = AuthService()

        # Exibe dialog de login MODAL
        self.show_login_dialog()

        # Só continua se login foi bem-sucedido
        if not self.auth_service.is_authenticated():
            # Usuário cancelou o login
            self.close()
            return

        # Continua com inicialização normal...
        self.setup_ui()

    def show_login_dialog(self):
        """Exibe dialog de login"""
        login_dialog = LoginDialog(self.auth_service, self)
        result = login_dialog.exec()

        if result != QDialog.DialogCode.Accepted:
            # Usuário cancelou ou fechou o dialog
            return False

        return True
```

---

## FASE 2: TREEVIEW (NOVA ABA)

### 2.1 Criar Widget de Busca Incremental

**Arquivo:** `consumo_lib/widgets/search_line_edit.py`

```python
from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import QTimer, pyqtSignal

class SearchLineEdit(QLineEdit):
    """Campo de busca com debounce"""

    searchPerformed = pyqtSignal(str)  # Emitido após debounce

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("🔍 Buscar programas...")
        self.setMinimumWidth(300)

        # Timer para debounce
        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._perform_search)

        # Conecta mudança de texto ao timer
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self, text: str):
        """Reinicia timer debounce quando texto muda"""
        self.debounce_timer.stop()
        if len(text) >= 2:  # Mínimo 2 caracteres
            self.debounce_timer.start(300)  # 300ms debounce

    def _perform_search(self):
        """Emite sinal de busca"""
        search_term = self.text().strip()
        if search_term:
            self.searchPerformed.emit(search_term)

    def clear_search(self):
        """Limpa busca"""
        self.clear()
        self.searchPerformed.emit("")
```

### 2.2 Criar Widget de Status Badge

**Arquivo:** `consumo_lib/widgets/status_badge.py`

```python
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class StatusBadge(QLabel):
    """Badge colorido para status"""

    # Cores por status
    COLORS = {
        "approved_auto": "#4CAF50",    # Verde vibrante
        "approved_user": "#CDDC39",    # Verde-amarelo
        "rejected": "#F44336",         # Vermelho
        "pending": "#9E9E9E",          # Cinza
        "in_progress": "#2196F3",      # Azul
    }

    LABELS = {
        "approved_auto": "A-AUTO",
        "approved_user": "A-USER",
        "rejected": "REPROV",
        "pending": "PENDENTE",
        "in_progress": "EM ANDAMENTO",
    }

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        self.set_status(status)

    def set_status(self, status: str):
        """Define status e atualiza aparência"""
        self.setText(self.LABELS.get(status, status.upper()))

        # Aplica estilo
        color = self.COLORS.get(status, "#999")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)

        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
```

### 2.3 Criar Widget de Barra de Status Hardware

**Arquivo:** `consumo_lib/widgets/hardware_status_bar.py`

```python
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal

class HardwareStatusBar(QWidget):
    """Barra de status do hardware"""

    status_clicked = pyqtSignal(str)  # Emitido ao clicar em status

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Configura interface"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Status PLC
        self.plc_label = QLabel("🔴 CLP: Desconectado")
        self.plc_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.plc_label.mousePressEvent = lambda e: self.status_clicked.emit("PLC")
        layout.addWidget(self.plc_label)

        # Status Tensiômetro
        self.tensio_label = QLabel("🔴 Tensiômetro: Desconectado")
        self.tensio_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tensio_label.mousePressEvent = lambda e: self.status_clicked.emit("TENSIO")
        layout.addWidget(self.tensio_label)

        # Status Câmera
        self.camera_label = QLabel("🔴 Câmera: Desconectada")
        self.camera_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.camera_label.mousePressEvent = lambda e: self.status_clicked.emit("CAMERA")
        layout.addWidget(self.camera_label)

        layout.addStretch()

    def update_plc_status(self, connected: bool):
        """Atualiza status PLC"""
        if connected:
            self.plc_label.setText("✅ CLP: Conectado")
        else:
            self.plc_label.setText("🔴 CLP: Desconectado")

    def update_tensio_status(self, connected: bool):
        """Atualiza status Tensiômetro"""
        if connected:
            self.tensio_label.setText("✅ Tensiômetro: Conectado")
        else:
            self.tensio_label.setText("🔴 Tensiômetro: Desconectado")

    def update_camera_status(self, connected: bool):
        """Atualiza status Câmera"""
        if connected:
            self.camera_label.setText("✅ Câmera: Conectada")
        else:
            self.camera_label.setText("🔴 Câmera: Desconectada")
```

### 2.4 Criar Aba TreeView

**Arquivo:** `consumo_lib/tabs/tree_view_tab.py`

```python
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLabel, QPushButton,
    QComboBox, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal

from consumo_lib.widgets.search_line_edit import SearchLineEdit
from consumo_lib.widgets.status_badge import StatusBadge
from consumo_lib.widgets.hardware_status_bar import HardwareStatusBar

class TreeViewTab(QWidget):
    """Aba principal com lista de programas"""

    program_selected = pyqtSignal(dict)  # Emitido ao selecionar programa
    inspect_requested = pyqtSignal(dict)  # Emitido ao clicar "Inspecionar"

    def __init__(self, stencil_manager, parent=None):
        super().__init__(parent)
        self.stencil_manager = stencil_manager
        self.current_stencils = []
        self.setup_ui()
        self.load_stencils()

    def setup_ui(self):
        """Configura interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Barra superior (busca + filtros + botões)
        top_bar = self.create_top_bar()
        layout.addWidget(top_bar)

        # Splitter horizontal (lista | detalhes)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # TreeView (esquerda)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Código", "Descrição", "Status", "Última Medição"])
        self.tree_widget.setColumnWidth(0, 150)
        self.tree_widget.setColumnWidth(1, 250)
        self.tree_widget.setColumnWidth(2, 100)
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        splitter.addWidget(self.tree_widget)

        # Painel de detalhes (direita)
        details_panel = self.create_details_panel()
        splitter.addWidget(details_panel)

        # Proporção do splitter (60% | 40%)
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)

        layout.addWidget(splitter, 1)  # Ocupa todo espaço restante

        # Barra de status do hardware
        self.hw_status_bar = HardwareStatusBar()
        layout.addWidget(self.hw_status_bar)

    def create_top_bar(self) -> QWidget:
        """Cria barra superior"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Busca
        self.search_input = SearchLineEdit()
        self.search_input.searchPerformed.connect(self.filter_stencils)
        layout.addWidget(self.search_input)

        # Filtro de período
        layout.addWidget(QLabel("Período:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Últimas 10",
            "7 dias",
            "30 dias",
            "60 dias",
            "90 dias",
            "180 dias",
            "365 dias"
        ])
        self.period_combo.currentTextChanged.connect(self.filter_stencils)
        layout.addWidget(self.period_combo)

        # Filtro de status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Todos",
            "A-AUTO",
            "A-USER",
            "REPROV",
            "Pendentes"
        ])
        self.status_combo.currentTextChanged.connect(self.filter_stencils)
        layout.addWidget(self.status_combo)

        layout.addStretch()

        # Botão código de barras
        self.barcode_button = QPushButton("📷 Escanear Código")
        self.barcode_button.setMinimumHeight(35)
        layout.addWidget(self.barcode_button)

        return widget

    def create_details_panel(self) -> QWidget:
        """Cria painel de detalhes do stencil"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)

        # Título
        title_label = QLabel("Detalhes do Stencil")
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(14)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Scroll area para detalhes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        # Placeholder (será preenchido ao selecionar item)
        self.details_placeholder = QLabel("Selecione um stencil para ver detalhes")
        self.details_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_placeholder.setStyleSheet("color: #888; padding: 40px;")
        details_layout.addWidget(self.details_placeholder)

        scroll.setWidget(details_widget)
        layout.addWidget(scroll, 1)

        # Botão inspecionar
        self.inspect_button = QPushButton("🔍 Inspecionar Stencil")
        self.inspect_button.setMinimumHeight(45)
        self.inspect_button.setEnabled(False)
        self.inspect_button.clicked.connect(self.on_inspect_clicked)
        layout.addWidget(self.inspect_button)

        return panel

    def load_stencils(self):
        """Carrega lista de stencils"""
        # TODO: Carregar do stencil_manager
        # Por enquanto, dados de exemplo
        self.current_stencils = [
            {
                "code": "STENCIL-ABC-123",
                "description": "Stencil Principal - Linha 1",
                "status": "approved_auto",
                "last_measurement": "15/12/2025 14:30"
            },
            {
                "code": "STENCIL-XYZ-456",
                "description": "Stencil Secundário - Linha 2",
                "status": "approved_user",
                "last_measurement": "14/12/2025 09:15"
            }
        ]

        self.populate_tree()

    def populate_tree(self, filtered_stencils=None):
        """Popula TreeView com stencils"""
        self.tree_widget.clear()

        stencils = filtered_stencils or self.current_stencils

        for stencil in stencils:
            item = QTreeWidgetItem()
            item.setText(0, stencil["code"])
            item.setText(1, stencil["description"])
            item.setText(3, stencil.get("last_measurement", "-"))

            # Badge de status
            status_badge = StatusBadge(stencil["status"])
            self.tree_widget.setItemWidget(item, 2, status_badge)

            # Armazena dados completos no item
            item.setData(0, Qt.ItemDataRole.UserRole, stencil)

            self.tree_widget.addTopLevelItem(item)

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handler: Item clicado"""
        stencil_data = item.data(0, Qt.ItemDataRole.UserRole)
        self.show_details(stencil_data)
        self.program_selected.emit(stencil_data)
        self.inspect_button.setEnabled(True)

    def show_details(self, stencil: dict):
        """Exibe detalhes do stencil"""
        # TODO: Implementar painel de detalhes completo
        self.details_placeholder.setText(
            f"Código: {stencil['code']}\n\n"
            f"{stencil['description']}\n\n"
            f"[Painel de detalhes completo será implementado aqui]"
        )

    def filter_stencils(self, search_term=""):
        """Filtra stencils por busca e filtros"""
        filtered = self.current_stencils

        # Filtro de busca
        if search_term:
            search_lower = search_term.lower()
            filtered = [
                s for s in filtered
                if search_term in s["code"].lower() or
                   search_term in s["description"].lower()
            ]

        # TODO: Adicionar filtros de período e status

        self.populate_tree(filtered)

    def on_inspect_clicked(self):
        """Handler: Botão Inspecionar clicado"""
        # TODO: Obter stencil selecionado e emitir sinal
        pass
```

### 2.5 Integrar TreeView no MainWindow

**Adicionar em `consumo_lib/main_window.py`:**

```python
from consumo_lib.tabs.tree_view_tab import TreeViewTab
from aoi_lib.stencil_tracker import StencilTracker

class MainWindow(QMainWindow):
    def __init__(self):
        # ... código existente ...

        # Inicializa StencilManager
        self.stencil_tracker = StencilTracker()

        # Cria aba TreeView
        self.tree_view_tab = TreeViewTab(self.stencil_tracker)
        self.tree_view_tab.inspect_requested.connect(self.on_inspect_requested)

        # Adiciona ao tab widget (se existir)
        # ou cria novo tab widget
        self.tabs.addTab(self.tree_view_tab, "📋 Programas")
        self.tabs.setCurrentWidget(self.tree_view_tab)

    def on_inspect_requested(self, stencil: dict):
        """Handler: Solicitação de inspeção"""
        # TODO: Exibir dialog de confirmação de posicionamento
        pass
```

---

## ORDEM DE IMPLEMENTAÇÃO

### Sequência Recomendada (12-16 horas)

#### PASSO 1: Fundamentos de Autenticação (3h)
1. ✅ Criar `aoi_lib/auth/user.py` (30 min)
2. ✅ Criar `aoi_lib/auth/auth_service.py` (1h)
3. ✅ Criar `data/users/users.json` padrão (30 min)
4. ✅ Testar autenticação no Python REPL (1h)

#### PASSO 2: Dialog de Login (2h)
1. ✅ Criar `consumo_lib/dialogs/login_dialog.py` (1.5h)
2. ✅ Integrar no `main_window.py` (30 min)

#### PASSO 3: Widgets Reutilizáveis (2h)
1. ✅ Criar `search_line_edit.py` (30 min)
2. ✅ Criar `status_badge.py` (30 min)
3. ✅ Criar `hardware_status_bar.py` (1h)

#### PASSO 4: TreeView Tab (4-5h)
1. ✅ Criar estrutura básica `tree_view_tab.py` (1h)
2. ✅ Implementar TreeView com dados de exemplo (1.5h)
3. ✅ Implementar painel de detalhes básico (1h)
4. ✅ Implementar filtros (busca) (1h)
5. ✅ Conectar sinais (slots) (30 min)

#### PASSO 5: Integração e Testes (2-3h)
1. ✅ Integrar no MainWindow (1h)
2. ✅ Testar fluxo completo (1h)
3. ✅ Ajustes finais e polimento (1h)

#### PASSO 6: Documentação (1h)
1. ✅ Atualizar README.md (30 min)
2. ✅ Criar instruções de uso (30 min)

---

## CHECKLIST COMPLETO

### FASE 1: Login

#### Backend (aoi_lib/auth/)
- [ ] Criar diretório `aoi_lib/auth/`
- [ ] Criar `aoi_lib/auth/__init__.py`
- [ ] Criar `aoi_lib/auth/user.py` com `UserRole` e `User`
- [ ] Criar `aoi_lib/auth/auth_service.py`
- [ ] Implementar `_hash_password()` (SHA-256)
- [ ] Implementar `_create_default_users()`
- [ ] Implementar `authenticate()`
- [ ] Implementar `logout()`
- [ ] Criar `data/users/users.json` com usuários padrão
- [ ] Testar autenticação no REPL

#### Frontend (consumo_lib/dialogs/)
- [ ] Criar `consumo_lib/dialogs/__init__.py`
- [ ] Criar `consumo_lib/dialogs/login_dialog.py`
- [ ] Implementar layout do dialog
- [ ] Implementar validação de campos vazios
- [ ] Implementar chamada ao auth_service
- [ ] Implementar feedback de erro
- [ ] Emitir sinal `login_successful`
- [ ] Integrar no `main_window.py`
- [ ] Testar login com usuário correto
- [ ] Testar login com usuário incorreto
- [ ] Testar cancelamento do dialog

### FASE 2: TreeView

#### Widgets (consumo_lib/widgets/)
- [ ] Criar `consumo_lib/widgets/search_line_edit.py`
- [ ] Implementar debounce de 300ms
- [ ] Testar busca incremental
- [ ] Criar `consumo_lib/widgets/status_badge.py`
- [ ] Definir cores para 3 status
- [ ] Testar badges
- [ ] Criar `consumo_lib/widgets/hardware_status_bar.py`
- [ ] Implementar labels de status
- [ ] Adicionar cursor pointer
- [ ] Testar clique nos labels

#### Tab Principal (consumo_lib/tabs/)
- [ ] Criar `consumo_lib/tabs/tree_view_tab.py`
- [ ] Implementar `create_top_bar()`
- [ ] Implementar `create_details_panel()`
- [ ] Implementar `populate_tree()`
- [ ] Implementar `on_item_clicked()`
- [ ] Implementar `filter_stencils()`
- [ ] Adicionar dados de exemplo
- [ ] Conectar sinais e slots
- [ ] Testar seleção de itens
- [ ] Testar filtros

#### Integração (main_window.py)
- [ ] Importar `TreeViewTab`
- [ ] Criar instância da aba
- [ ] Adicionar ao tab widget
- [ ] Conectar sinal `inspect_requested`
- [ ] Testar navegação entre abas
- [ ] Testar integração com hardware

### Testes Manuais
- [ ] Testar login com operador
- [ ] Testar login com engenharia
- [ ] Testar senha incorreta
- [ ] Testar campo vazio
- [ ] Testar busca na TreeView
- [ ] Testar filtro de período
- [ ] Testar filtro de status
- [ ] Testar seleção de stencil
- [ ] Testar botão inspecionar
- [ ] Testar status do hardware

---

## CRITÉRIOS DE ACEITE

### FASE 1: Login

**Funcionalidades:**
- [✅] Dialog exibe ao iniciar aplicação
- [✅] Modal (não permite acesso sem login)
- [✅] Campos: Usuário e Senha
- [✅] Botão: Entrar e Cancelar
- [✅] Validação: Campos vazios
- [✅] Autenticação: Usuário/senha corretos
- [✅] Erro: Usuário/senha incorretos
- [✅] Enter no senha dispara login
- [✅] Usuários padrão criados automaticamente
- [✅] Perfil armazenado na sessão

**Usuários Padrão:**
```
operator / operator123  → Operador
eng / eng123            → Engenharia
admin / admin123        → Administrador
```

### FASE 2: TreeView

**Funcionalidades:**
- [✅] Nova aba "Programas" visível
- [✅] TreeView populated com dados
- [✅] Colunas: Código, Descrição, Status, Última Medição
- [✅] Badges de status coloridos
- [✅] Busca incremental (debounce 300ms)
- [✅] Filtro de período (dropdown)
- [✅] Filtro de status (dropdown)
- [✅] Painel de detalhes (direita)
- [✅] Botão "Inspecionar Stencil"
- [✅] Barra de status do hardware

**Status Badges:**
- [✅] A-AUTO: Verde (#4CAF50)
- [✅] A-USER: Verde-amarelo (#CDDC39)
- [✅] REPROV: Vermelho (#F44336)

**Hardware Status:**
- [✅] PLC: Conectado/Desconectado
- [✅] Tensiômetro: Conectado/Desconectado
- [✅] Câmera: Conectada/Desconectada
- [✅] Clicável (abre config)

**Dados de Exemplo:**
- [✅] 2-3 stencils de exemplo
- [✅] Status variados
- [✅] Datas diferentes

---

## TESTES MANUAIS

### Teste 1: Login Bem-Sucedido

```
1. Iniciar aplicação
2. Dialog de login exibe
3. Digitar "operator" em usuário
4. Digitar "operator123" em senha
5. Clicar "Entrar"
6. ✅ Dialog fecha
7. ✅ MainWindow exibe com aba "Programas"
8. ✅ Barra de título mostra usuário logado
```

### Teste 2: Login Mal-Sucedido

```
1. Iniciar aplicação
2. Digitar "operator" em usuário
3. Digitar "senha_errada" em senha
4. Clicar "Entrar"
5. ✅ Mensagem de erro exibe
6. ✅ Campo senha limpa
7. ✅ Focus volta para senha
8. ✅ Dialog permanece aberto
```

### Teste 3: Cancelar Login

```
1. Iniciar aplicação
2. Clicar "Cancelar" ou fechar dialog
3. ✅ Aplicação fecha
```

### Teste 4: Busca na TreeView

```
1. Fazer login
2. Abrir aba "Programas"
3. TreeView mostra stencils
4. Digitar "ABC" na busca
5. ✅ TreeView filtra (apenas ABC-123 visível)
6. Limpar busca
7. ✅ TreeView mostra todos novamente
```

### Teste 5: Seleção de Stencil

```
1. Abrir aba "Programas"
2. Clicar em stencil da lista
3. ✅ Painel de detalhes atualiza
4. ✅ Botão "Inspecionar" habilita
5. ✅ Status selecionado visual
```

### Teste 6: Filtros

```
1. Abrir aba "Programas"
2. Mudar filtro de período
3. ✅ TreeView atualiza (quando implementado)
4. Mudar filtro de status
5. ✅ TreeView atualiza (quando implementado)
```

### Teste 7: Status do Hardware

```
1. Abrir aba "Programas"
2. Ver barra de status na parte inferior
3. ✅ PLC mostra "Conectado" ou "Desconectado"
4. ✅ Tensiômetro mostra "Conectado" ou "Desconectado"
5. ✅ Câmera mostra "Conectada" ou "Desconectada"
6. Clicar em status
7. ✅ (Futuro) Abre dialog de configuração
```

---

## REFERÊNCIAS

- **Wireframes:** `docs/wireframes/svg/01_login_dialog.svg`, `02_tela_inicial_treeview.svg`
- **Fluxo:** `docs/guides/fluxo_usuario_operador.md`
- **Plano Geral:** `docs/guides/plano_implementacao_interface.md`
- **Auth:** `aoi_lib/auth/` (novo módulo)

---

**Próximos Passos:**

Após completar FASE 1 e FASE 2:
- ✅ FASE 3: Dialog de Confirmação de Posicionamento
- ✅ FASE 4: Dialog de Escolha de Modo
- ✅ FASE 5: Tela de Execução

**Documento criado:** 2026-01-08
**Status:** 🚀 Pronto para implementação
**Estimativa:** 12-16 horas de desenvolvimento
