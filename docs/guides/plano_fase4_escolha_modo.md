# Plano de Implementação - FASE 4: Escolha de Modo

**Data:** 2026-01-08
**Versão:** 1.0
**Status:** 🚀 Pronto para Implementação
**Wireframe Referência:** `docs/wireframes/svg/04_escolha_modo.svg`

---

## 📋 VISÃO GERAL

### Objetivo

Criar dialog que permite ao usuário escolher o modo de operação para inspeção do stencil. O usuário pode selecionar entre medição de tensão, inspeção visual, ou ambos.

### Fluxo

```
TreeView (usuário seleciona programa)
    ↓
Usuário clica "Inspecionar Stencil"
    ↓
Dialog: Confirmação de Posicionamento (FASE 3) ✅
    ↓
Usuário verifica checklist e confirma
    ↓
Dialog: Escolha de Modo (FASE 4) ← VOCÊ AQUI
    ↓
Usuário seleciona modo (Tensão / Inspeção / Ambos)
    ↓
FASE 5: Execução (Tela de Progresso)
```

### Premissas

- FASE 3 (Posicionamento) está completa e validada
- Usuário já autenticado (FASE 1)
- Stencil já selecionado (FASE 2)
- Posicionamento confirmado (FASE 3)
- Wireframe `04_escolha_modo.svg` aprovado pelo cliente

---

## 🎨 COMPONENTES

### 1. Dialog Principal

**Arquivo:** `consumo_lib/dialogs/mode_selection_dialog.py`

**Funcionalidades:**
- Título claro: "Escolha o Modo de Inspeção"
- Subtítulo com código do stencil
- 3 cards de seleção (Tensão, Inspeção, Ambos)
- Tempo estimado para cada modo
- Descrição detalhada
- Botão Confirmar
- Botão Cancelar

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│           Escolha o Modo de Inspeção                    │
│                                                          │
│              Stencil: STENCIL-ABC-123                    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   TENSÃO     │  │  INSPEÇÃO    │  │    AMBOS     │  │
│  │              │  │              │  │              │  │
│  │   ⏱️ 10 min  │  │  ⏱️ 15 min   │  │  ⏱️ 25 min   │  │
│  │              │  │              │  │              │  │
│  │ Medir tensão │  │ Análise      │  │ Tensão +     │  │
│  │ superficial  │  │ visual das   │  │ Inspeção     │  │
│  │ em múltiplos │  │ aberturas    │  │ completos    │  │
│  │ pontos       │  │              │  │              │  │
│  │              │  │              │  │              │  │
│  │  [ Selecionar]│  │[ Selecionar] │  │[ Selecionar] │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│                   [Confirmar]  [Cancelar]               │
└─────────────────────────────────────────────────────────┘
```

### 2. Cards de Seleção

**Estrutura do Card:**
```python
class ModeCard(QWidget):
    """Card selecionável para escolha de modo"""

    def __init__(self, mode_type, title, description, time_estimate, icon, parent=None):
        """
        Args:
            mode_type: "tension", "inspection", ou "both"
            title: Título do modo
            description: Descrição detalhada
            time_estimate: Tempo estimado (ex: "10 min")
            icon: Emoji ou ícone (ex: "⏱️")
        """
```

**Estados Visuais:**
- **Normal:** Borda cinza, fundo branco
- **Hover:** Borda azul (#2196F3), fundo levemente azulado
- **Selected:** Borda azul espessa (3px), fundo #E3F2FD (azul claro)

### 3. Modos Disponíveis

#### MODO 1: Apenas Tensão
```python
{
    "mode": "tension",
    "title": "Apenas Tensão",
    "description": "Medir tensão superficial em múltiplos pontos da área do stencil",
    "time_estimate": "10 min",
    "icon": "⏱️",
    "details": [
        "Grid de medição: 5x5 pontos (padrão)",
        "Z-axis automático para contato",
        "Relatório com heatmap de tensão",
        "Classificação: OK/WARNING/NOK"
    ]
}
```

#### MODO 2: Apenas Inspeção
```python
{
    "mode": "inspection",
    "title": "Apenas Inspeção Visual",
    "description": "Análise visual das aberturas do stencil para detectar obstruções",
    "time_estimate": "15 min",
    "icon": "🔍",
    "details": [
        "Captura de imagem com backlight",
        "Comparação com arquivo Gerber",
        "Análise de obstruções parciais/bloqueios",
        "Classificação: OK/PARTIAL/BLOCKED"
    ]
}
```

#### MODO 3: Ambos (Completo)
```python
{
    "mode": "both",
    "title": "Ambos (Completo)",
    "description": "Tensão + Inspeção Visual para análise completa do stencil",
    "time_estimate": "25 min",
    "icon": "✅",
    "details": [
        "Tensão: Grid 5x5 com heatmap",
        "Inspeção: Análise visual completa",
        "Relatório integrado PDF",
        "Classificação consolidada"
    ]
}
```

### 4. Comportamento de Seleção

**Regras:**
1. Apenas 1 modo pode ser selecionado por vez (radio button behavior)
2. Card selecionado visualmente destacado
3. Botão "Confirmar" só habilitado quando modo selecionado
4. Card pode ser clicado em qualquer área (não apenas botão)
5. Esc no keyboard fecha dialog (cancel)
6. Enter no keyboard confirma seleção

---

## 💻 IMPLEMENTAÇÃO

### Estrutura de Arquivos

```
consumo_lib/dialogs/
├── __init__.py (atualizar)
└── mode_selection_dialog.py (NOVO)
```

### Código Completo

```python
"""
Dialog de Seleção de Modo de Inspeção

Permite usuário escolher entre medição de tensão, inspeção visual,
ou modo completo (ambos).
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QWidget, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class ModeCard(QWidget):
    """
    Card selecionável para modo de inspeção

    Sinais:
        selected: Emitido quando card é selecionado
                  Argumento: mode_type ("tension", "inspection", "both")
    """

    selected = pyqtSignal(str)

    def __init__(self, mode_type: str, title: str, description: str,
                 time_estimate: str, icon: str, parent=None):
        """
        Inicializa card de modo

        Args:
            mode_type: Tipo do modo ("tension", "inspection", "both")
            title: Título do modo
            description: Descrição detalhada
            time_estimate: Tempo estimado (ex: "10 min")
            icon: Emoji ou ícone
            parent: Widget pai
        """
        super().__init__(parent)
        self.mode_type = mode_type
        self.is_selected = False

        self.setup_ui(title, description, time_estimate, icon)

    def setup_ui(self, title: str, description: str,
                 time_estimate: str, icon: str):
        """Configura interface do card"""
        self.setFixedSize(200, 180)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Ícone + tempo
        header_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)

        time_label = QLabel(time_estimate)
        time_font = time_label.font()
        time_font.setBold(True)
        time_font.setPointSize(12)
        time_label.setFont(time_font)
        time_label.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(time_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Título
        title_label = QLabel(title)
        title_font = title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(13)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Descrição
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(desc_label)

        layout.addStretch()

        # Botão de seleção
        self.select_button = QPushButton("Selecionar")
        self.select_button.setMinimumHeight(35)
        self.select_button.clicked.connect(self.on_clicked)
        layout.addWidget(self.select_button)

        # Estilo inicial
        self.update_style()

    def update_style(self):
        """Atualiza estilo visual baseado no estado de seleção"""
        if self.is_selected:
            bg_color = "#E3F2FD"
            border_color = "#2196F3"
            border_width = "3px"
            btn_text = "✓ Selecionado"
            btn_bg = "#2196F3"
            btn_color = "white"
        else:
            bg_color = "white"
            border_color = "#E0E0E0"
            border_width = "2px"
            btn_text = "Selecionar"
            btn_bg = "#F5F5F5"
            btn_color = "#333333"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: {border_width} solid {border_color};
                border-radius: 8px;
            }}
            QWidget:hover {{
                background-color: {"#BBDEFB" if not self.is_selected else "#E3F2FD"};
                border: 2px solid #2196F3;
            }}
        """)

        self.select_button.setText(btn_text)
        self.select_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_color};
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: {"#1976D2" if self.is_selected else "#E0E0E0"};
            }}
        """)

    def on_clicked(self):
        """Handler: Card clicado"""
        self.select()

    def select(self):
        """Marca este card como selecionado"""
        if not self.is_selected:
            self.is_selected = True
            self.update_style()
            self.selected.emit(self.mode_type)

    def deselect(self):
        """Desmarca este card"""
        if self.is_selected:
            self.is_selected = False
            self.update_style()

    def mousePressEvent(self, event):
        """Handler: Clique no card (qualquer área)"""
        self.select()


class ModeSelectionDialog(QDialog):
    """
    Dialog de seleção de modo de inspeção

    Sinais:
        mode_selected: Emitido quando usuário seleciona modo
                      Argumento: dict com mode_type e dados do stencil
    """

    mode_selected = pyqtSignal(dict)

    # Configurações dos modos
    MODES = [
        {
            "mode": "tension",
            "title": "Apenas Tensão",
            "description": "Medir tensão superficial em múltiplos pontos",
            "time_estimate": "⏱️ 10 min",
            "icon": "⏱️"
        },
        {
            "mode": "inspection",
            "title": "Apenas Inspeção",
            "description": "Análise visual das aberturas do stencil",
            "time_estimate": "⏱️ 15 min",
            "icon": "🔍"
        },
        {
            "mode": "both",
            "title": "Ambos (Completo)",
            "description": "Tensão + Inspeção Visual completa",
            "time_estimate": "⏱️ 25 min",
            "icon": "✅"
        }
    ]

    def __init__(self, stencil_code: str, parent=None):
        """
        Inicializa dialog de seleção de modo

        Args:
            stencil_code: Código do stencil selecionado
            parent: Widget pai
        """
        super().__init__(parent)
        self.stencil_code = stencil_code
        self.selected_mode = None
        self.mode_cards = []

        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("Escolha o Modo de Inspeção")
        self.setModal(True)
        self.setFixedSize(700, 450)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Título principal
        title_label = QLabel("Escolha o Modo de Inspeção")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Subtítulo com código do stencil
        subtitle_label = QLabel(f"Stencil: {self.stencil_code}")
        subtitle_font = subtitle_label.font()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #666;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(10)

        # Container dos cards
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setSpacing(20)

        # Criar cards
        for mode_config in self.MODES:
            card = ModeCard(
                mode_type=mode_config["mode"],
                title=mode_config["title"],
                description=mode_config["description"],
                time_estimate=mode_config["time_estimate"],
                icon=mode_config["icon"],
                parent=self
            )
            card.selected.connect(self.on_mode_selected)
            cards_layout.addWidget(card)
            self.mode_cards.append(card)

        layout.addWidget(cards_container, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addSpacing(20)

        # Botões
        buttons_layout = QHBoxLayout()

        self.confirm_button = QPushButton("✓ Confirmar Seleção")
        self.confirm_button.setMinimumHeight(45)
        self.confirm_button.setEnabled(False)  # Desabilitado até selecionar
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """)
        self.confirm_button.clicked.connect(self.on_confirm_clicked)
        buttons_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("✗ Cancelar")
        self.cancel_button.setMinimumHeight(45)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #F5F5F5;
                color: #424242;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

    def on_mode_selected(self, mode_type: str):
        """
        Handler: Modo selecionado

        Args:
            mode_type: Tipo do modo selecionado
        """
        # Atualiza seleção (radio button behavior)
        self.selected_mode = mode_type

        for card in self.mode_cards:
            if card.mode_type == mode_type:
                # Garante que está selecionado
                if not card.is_selected:
                    card.select()
            else:
                # Desmarca outros cards
                card.deselect()

        # Habilita botão confirmar
        self.confirm_button.setEnabled(True)

        logger.info(f"Modo selecionado: {mode_type}")

    def on_confirm_clicked(self):
        """Handler: Botão Confirmar clicado"""
        if self.selected_mode:
            logger.info(f"Confirmação de modo: {self.selected_mode}")

            # Emite sinal com dados
            self.mode_selected.emit({
                "mode": self.selected_mode,
                "stencil_code": self.stencil_code
            })

            self.accept()

    def get_selected_mode(self) -> str:
        """
        Retorna modo selecionado

        Returns:
            Mode type ("tension", "inspection", "both") ou None
        """
        return self.selected_mode
```

---

## 🔗 INTEGRAÇÃO

### 1. Atualizar `__init__.py`

**Arquivo:** `consumo_lib/dialogs/__init__.py`

```python
# Mode selection dialogs (NOVO - FASE 4)
from .mode_selection_dialog import ModeSelectionDialog
__all__.append('ModeSelectionDialog')
```

### 2. Integrar no MainWindow

**Arquivo:** `consumo_lib/main_window.py`

**Modificar `_on_inspect_requested`:**

```python
def _on_inspect_requested(self, stencil: dict):
    """
    Handler: Solicitação de inspeção da TreeView

    Fluxo: TreeView → Posicionamento → Modo → Execução
    """
    logger.info(f"Solicitação de inspeção: {stencil.get('code', 'N/A')}")

    # FASE 3: Confirmar posicionamento
    if not self.show_positioning_confirmation(stencil):
        logger.info("Posicionamento cancelado pelo usuário")
        return

    # FASE 4: Escolher modo de inspeção
    if not self.show_mode_selection(stencil):
        logger.info("Seleção de modo cancelada pelo usuário")
        return

    # Modo selecionado - FASE 5 será implementada a seguir
    QMessageBox.information(
        self,
        "Modo Selecionado",
        f"Modo de inspeção selecionado com sucesso!\n\n"
        f"FASE 5 (Execução) será implementada a seguir.\n\n"
        f"Fluxo planejado:\n"
        f"1. ✅ Login (FASE 1)\n"
        f"2. ✅ TreeView (FASE 2)\n"
        f"3. ✅ Posicionamento (FASE 3)\n"
        f"4. ✅ Escolha de Modo (FASE 4)\n"
        f"5. ⏳ Execução (FASE 5 - próxima)\n"
    )

def show_mode_selection(self, stencil: dict) -> bool:
    """
    Exibe dialog de seleção de modo de inspeção

    Args:
        stencil: Dicionário com dados do stencil

    Returns:
        True se usuário selecionou modo, False se cancelou
    """
    from consumo_lib.dialogs.mode_selection_dialog import ModeSelectionDialog

    dialog = ModeSelectionDialog(stencil['code'], self)
    dialog.mode_selected.connect(self.on_mode_selected)
    result = dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        selected_mode = dialog.get_selected_mode()
        logger.info(f"Modo de inspeção selecionado: {selected_mode}")
        return True
    else:
        logger.info(f"Seleção de modo cancelada: {stencil['code']}")
        return False

def on_mode_selected(self, data: dict):
    """
    Handler: Modo de inspeção selecionado

    Args:
        data: Dict com "mode" e "stencil_code"
    """
    mode = data.get("mode")
    stencil_code = data.get("stencil_code")

    logger.info(f"Modo selecionado: {mode} para stencil {stencil_code}")

    # Armazena modo selecionado para uso na FASE 5
    self.selected_inspection_mode = mode
```

---

## ✅ CRITÉRIOS DE ACEITE

### Funcionalidades
- [ ] Dialog exibe após confirmação de posicionamento
- [ ] 3 cards visíveis (Tensão, Inspeção, Ambos)
- [ ] Tempo estimado exibido em cada card
- [ ] Cards selecionáveis por clique em qualquer área
- [ ] Apenas 1 card selecionado por vez
- [ ] Botão Confirmar habilitado apenas quando modo selecionado
- [ ] Botão Cancelar fecha dialog
- [ ] Dialog é modal (bloqueia aplicação)

### Layout
- [ ] 3 cards alinhados horizontalmente
- [ ] Espaçamento adequado entre cards
- [ ] Título e subtítulo centralizados
- [ ] Botões Confirmar/Cancelar centralizados
- [ ] Nada cortado/truncado

### Estados Visuais
- [ ] Card normal: borda cinza clara
- [ ] Card hover: borda azul
- [ ] Card selected: borda azul espessa + fundo azulado
- [ ] Botão "Selecionar" muda para "✓ Selecionado"

### Fluxo
- [ ] Confirmar → Emite sinal mode_selected, fecha dialog
- [ ] Cancelar → Fecha dialog sem emitir sinal
- [ ] Seleção obrigatória (não pode confirmar sem selecionar)

---

## 🧪 TESTES MANUAIS

### Teste 1: Fluxo Completo
```
1. Fazer login
2. Abrir aba "Programas"
3. Selecionar stencil (STENCIL-ABC-123)
4. Clicar "Inspecionar Stencil"
5. ✅ Confirmar posicionamento (FASE 3)
6. ✅ Dialog de modo exibe
```

### Teste 2: Verificar Conteúdo
```
1. Ver 3 cards: Tensão, Inspeção, Ambos
2. Ver tempos estimados: 10 min, 15 min, 25 min
3. Ver ícones: ⏱️, 🔍, ✅
4. Ver descrições em cada card
```

### Teste 3: Selecionar Modo
```
1. Clicar no card "Apenas Tensão"
2. ✅ Card fica destacado (azul)
3. ✅ Outros cards ficam normal
4. ✅ Botão "Confirmar" habilita
5. ✅ Texto muda para "✓ Selecionado"
```

### Teste 4: Trocar Seleção
```
1. Selecionar "Apenas Tensão"
2. Clicar em "Apenas Inspeção"
3. ✅ "Tensão" deseleciona
4. ✅ "Inspeção" seleciona
5. ✅ Apenas 1 card selecionado por vez
```

### Teste 5: Confirmar
```
1. Selecionar qualquer modo
2. Clicar "Confirmar Seleção"
3. ✅ Dialog fecha
4. ✅ MessageBox aparece "Modo Selecionado"
5. ✅ Log mostra modo selecionado
```

### Teste 6: Cancelar
```
1. Não selecionar nada (ou selecionar e depois cancelar)
2. Clicar "Cancelar"
3. ✅ Dialog fecha
4. ✅ Nenhuma mensagem de confirmação
```

### Teste 7: Hover nos Cards
```
1. Passar mouse sobre cada card
2. ✅ Fundo muda levemente (hover)
3. ✅ Borda fica azul
4. ✅ Cursor vira mãozinha (pointer)
```

---

## 📁 ARQUIVOS A CRIAR/MODIFICAR

### Criar (1 arquivo)
- `consumo_lib/dialogs/mode_selection_dialog.py`

### Modificar (2 arquivos)
- `consumo_lib/dialogs/__init__.py` (adicionar import)
- `consumo_lib/main_window.py` (adicionar método e conectar fluxo)

---

## ⏱️ ESTIMATIVA

- **Criação do dialog:** 45 min
- **Criação dos ModeCards:** 30 min
- **Integração no MainWindow:** 15 min
- **Testes e ajustes:** 30 min
- **Total:** 2 horas

---

## 🎯 PRÓXIMA FASE

Após validação desta FASE 4:

**FASE 5: Execução (Tela de Progresso)**
- Exibir progresso da execução em tempo real
- Barra de progresso
- Log de operações
- Possibilidade de cancelar
- Tratamento de erros

---

**Documento criado:** 2026-01-08
**Status:** 🚀 Pronto para implementação
**Wireframe:** `docs/wireframes/svg/04_escolha_modo.svg`
