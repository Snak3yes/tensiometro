# Plano de Implementação - FASE 3: Confirmação de Posicionamento

**Data:** 2026-01-08
**Versão:** 1.0
**Status:** 🚀 Pronto para Implementação
**Wireframe Referência:** `docs/wireframes/svg/03_confirmacao_posicionamento.svg`

---

## 📋 VISÃO GERAL

### Objetivo

Criar dialog que confirma se o stencil está posicionado corretamente antes de iniciar a medição/inspeção. Esta é uma etapa crítica de segurança.

### Fluxo

```
TreeView (usuário seleciona programa)
    ↓
Usuário clica "Inspecionar Stencil"
    ↓
Dialog: Confirmação de Posicionamento
    ↓
Usuário verifica checklist e confirma
    ↓
FASE 4: Escolha de Modo
```

### Premissas

- Wireframe `03_confirmacao_posicionamento.svg` aprovado pelo cliente
- Fluxo documentado em `fluxo_usuario_operador.md`
- Usuário já autenticado (FASE 1 completa)
- Stencil já selecionado na TreeView (FASE 2 completa)

---

## 🎨 COMPONENTES

### 1. Dialog Principal

**Arquivo:** `consumo_lib/dialogs/confirm_positioning_dialog.py`

**Funcionalidades:**
- Ícone grande do stencil
- Código do stencil selecionado
- Checklist de verificação (5 itens)
- Aviso sobre Emergency Stop
- Botões: Confirmar / Cancelar

**Layout:**
```
┌─────────────────────────────────────────┐
│      Confirmação de Posicionamento      │
├─────────────────────────────────────────┤
│                                         │
│          [Ícone Stencil]               │
│                                         │
│    STENCIL-ABC-123                     │
│                                         │
│  Verifique antes de continuar:        │
│                                         │
│  ☐ Stencil fixado na mesa             │
│  ☐ Área de trabalho limpa              │
│  ☐ CNC zerada (posição 0,0)           │
│  ☐ Emergency Stop acessível            │
│  ☐ Backlight ligado                    │
│                                         │
│  ⚠️  Emergency Stop deve estar acessível! │
│                                         │
│        [Confirmar]  [Cancelar]          │
└─────────────────────────────────────────┘
```

### 2. Estados do Checklist

**Estado inicial:** Todos os itens desmarcados (☐)

**Usuário pode:**
- Marcar/desmarcar itens clicando neles
- Não é obrigatório marcar todos (sistema confia no operador)
- Checkbox é apenas lembrete, não bloqueia confirmação

### 3. Aviso Emergency Stop

**Texto de destaque:**
```
⚠️  Emergency Stop deve estar acessível!
```

**Estilo:**
- Cor laranja/amarela (#FF9800)
- Negrito
- Ícone de warning

---

## 💻 IMPLEMENTAÇÃO

### Código Completo

```python
"""
Dialog de Confirmação de Posicionamento do Stencil

Exibe checklist de segurança antes de iniciar medição/inspeção.
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

logger = logging.getLogger(__name__)


class ConfirmPositioningDialog(QDialog):
    """
    Dialog de confirmação de posicionamento do stencil

    Sinais:
        position_confirmed: Emitido quando usuário confirma posicionamento
    """

    position_confirmed = pyqtSignal()

    # Checklist items
    CHECKLIST_ITEMS = [
        "Stencil fixado na mesa",
        "Área de trabalho limpa",
        "CNC zerada (posição 0,0)",
        "Emergency Stop acessível",
        "Backlight ligado (se inspeção visual)"
    ]

    def __init__(self, stencil_code: str, parent=None):
        """
        Inicializa dialog de confirmação

        Args:
            stencil_code: Código do stencil selecionado
            parent: Widget pai
        """
        super().__init__(parent)
        self.stencil_code = stencil_code
        self.checklist_states = [False] * len(self.CHECKLIST_ITEMS)
        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("Confirmação de Posicionamento")
        self.setModal(True)
        self.setFixedSize(550, 600)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # Título
        title_label = QLabel("Confirmação de Posicionamento")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        layout.addSpacing(20)

        # Ícone do stencil (placeholder)
        icon_container = QLabel()
        icon_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_container.setFixedSize(120, 120)
        icon_container.setStyleSheet("""
            QLabel {
                background-color: #E3F2FD;
                border: 2px solid #1976D2;
                border-radius: 60px;
                font-size: 48px;
            }
        """)
        icon_container.setText("📋")
        layout.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Código do stencil
        code_label = QLabel(self.stencil_code)
        code_font = code_label.font()
        code_font.setPointSize(20)
        code_font.setBold(True)
        code_label.setFont(code_font)
        code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(code_label)

        layout.addSpacing(20)

        # Instruções
        instruction_label = QLabel("Verifique antes de continuar:")
        instruction_font = instruction_label.font()
        instruction_font.setPointSize(12)
        instruction_font.setBold(True)
        instruction_label.setFont(instruction_font)
        layout.addWidget(instruction_label)

        # Checklist
        self.checkboxes = []
        for i, item_text in enumerate(self.CHECKLIST_ITEMS):
            checkbox = QCheckBox(item_text)
            checkbox.stateChanged.connect(
                lambda state, index=i: self._on_checkbox_changed(index, state)
            )
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)

        layout.addSpacing(20)

        # Aviso Emergency Stop
        warning_label = QLabel(
            "⚠️  Emergency Stop deve estar acessível em caso de emergência!"
        )
        warning_label.setStyleSheet("""
            QLabel {
                background-color: #FFF3E0;
                color: #E65100;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(warning_label)

        layout.addSpacing(20)

        # Botões
        buttons_layout = QHBoxLayout()

        self.confirm_button = QPushButton("✓ Confirmar")
        self.confirm_button.setMinimumHeight(50)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        self.confirm_button.clicked.connect(self.on_confirm_clicked)
        buttons_layout.addWidget(self.confirm_button)

        self.cancel_button = QPushButton("✗ Cancelar")
        self.cancel_button.setMinimumHeight(50)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        layout.addLayout(buttons_layout)

    def _on_checkbox_changed(self, index: int, state):
        """
        Handler: Checkbox mudou de estado

        Args:
            index: Índice do checkbox
            state: Novo estado (Qt.CheckState)
        """
        self.checklist_states[index] = (state == Qt.CheckState.Checked.value)

    def on_confirm_clicked(self):
        """Handler: Botão Confirmar clicado"""
        # Log dos itens marcados
        marked_items = [
            self.CHECKLIST_ITEMS[i]
            for i, checked in enumerate(self.checklist_states)
            if checked
        ]

        logger.info(f"Checklist marcados: {marked_items}")

        # Não bloqueia mesmo se não marcaram tudo
        # Sistema confia no operador
        self.position_confirmed.emit()
        self.accept()

    def get_checklist_state(self) -> dict:
        """
        Retorna estado atual do checklist

        Returns:
            Dicionário com itens e seus estados (True/False)
        """
        return {
            item: checked
            for item, checked in zip(self.CHECKLIST_ITEMS, self.checklist_states)
        }
```

---

## 🔗 INTEGRAÇÃO

### 1. Integração no MainWindow

**Arquivo:** `consumo_lib/main_window.py`

**Adicionar método:**

```python
def show_positioning_confirmation(self, stencil: dict) -> bool:
    """
    Exibe dialog de confirmação de posicionamento

    Args:
        stencil: Dicionário com dados do stencil

    Returns:
        True se usuário confirmou, False se cancelou
    """
    from consumo_lib.dialogs.confirm_positioning_dialog import ConfirmPositioningDialog

    dialog = ConfirmPositioningDialog(stencil['code'], self)
    result = dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        checklist_state = dialog.get_checklist_state()
        logger.info(f"Posicionamento confirmado: {stencil['code']}")
        logger.info(f"Checklist: {checklist_state}")
        return True
    else:
        logger.info(f"Posicionamento cancelado: {stencil['code']}")
        return False
```

### 2. Conectar Fluxo

**Modificar handler `_on_inspect_requested`:**

```python
def _on_inspect_requested(self, stencil: dict):
    """
    Handler: Solicitação de inspeção da TreeView

    Fluxo: TreeView → Posicionamento → Modo → Execução
    """
    logger.info(f"Solicitação de inspeção: {stencil.get('code', 'N/A')}")

    # FASE 3: Confirmar posicionamento
    if not self.show_positioning_confirmation(stencil):
        # Usuário cancelou
        return

    # FASE 4: Escolha de modo (próximo passo)
    # TODO: Chamar dialog de escolha de modo
    QMessageBox.information(
        self,
        "Posicionamento Confirmado",
        f"Posicionamento do stencil {stencil.get('code')} confirmado!\n\n"
        f"FASE 4 (Escolha de Modo) será implementada a seguir.\n\n"
        f"Estágio atual: FASE 3 concluída ✅"
    )
```

---

## ✅ CRITÉRIOS DE ACEITE

### Funcionalidades
- [ ] Dialog exibe ao clicar "Inspecionar Stencil"
- [ ] Código do stencil exibido corretamente
- [ ] 5 itens de checklist visíveis
- [ ] Checkboxes funcionam (marcar/desmarcar)
- [ ] Aviso Emergency Stop destacado (cor laranja)
- [ ] Botão Confirmar funciona
- [ ] Botão Cancelar fecha dialog
- [ ] Dialog é modal (bloqueia aplicação)

### Layout
- [ ] Ícone do stencil visível
- [ ] Espaçamento adequado entre elementos
- [ ] Checklist alinhado
- [ ] Botões centralizados
- [ ] Nada cortado/truncado

### Fluxo
- [ ] Confirmar → Emite sinal, fecha dialog
- [ ] Cancelar → Fecha dialog sem emitir sinal
- [ ] Checklist opcional (não bloqueia confirmação)

---

## 🧪 TESTES MANUAIS

### Teste 1: Fluxo Completo
```
1. Fazer login
2. Abrir aba "Programas"
3. Selecionar stencil (STENCIL-ABC-123)
4. Clicar "Inspecionar Stencil"
5. ✅ Dialog de posicionamento exibe
```

### Teste 2: Verificar Conteúdo
```
1. Ver código do stencil no dialog
2. Ver 5 itens do checklist
3. Ver aviso Emergency Stop
4. Ver botões Confirmar/Cancelar
```

### Teste 3: Marcar Checklist
```
1. Marcar 3 itens
2. Desmarcar 1 item
3. Verificar estados alternam
```

### Teste 4: Confirmar
```
1. Marcar alguns itens (ou nenhum)
2. Clicar "Confirmar"
3. ✅ Dialog fecha
4. ✅ MessageBox aparece "Posicionamento Confirmado"
```

### Teste 5: Cancelar
```
1. Clicar "Cancelar"
2. ✅ Dialog fecha
3. ✅ Nenhuma mensagem de confirmação
```

---

## 📁 ARQUIVOS A CRIAR/MODIFICAR

### Criar (1 arquivo)
- `consumo_lib/dialogs/confirm_positioning_dialog.py`

### Modificar (2 arquivos)
- `consumo_lib/dialogs/__init__.py` (adicionar import)
- `consumo_lib/main_window.py` (adicionar método e conectar fluxo)

---

## ⏱️ ESTIMATIVA

- **Criação do dialog:** 30 min
- **Integração no MainWindow:** 15 min
- **Testes e ajustes:** 15 min
- **Total:** 1 hora

---

## 🎯 PRÓXIMA FASE

Após validação desta FASE 3:

**FASE 4: Escolha de Modo**
- Dialog com 3 cards:
  - Apenas Tensão
  - Apenas Inspeção Visual
  - Ambos (Completo)
- Indicador de tempo estimado
- Botões de seleção

---

**Documento criado:** 2026-01-08
**Status:** 🚀 Pronto para implementação
**Wireframe:** `docs/wireframes/svg/03_confirmacao_posicionamento.svg`
