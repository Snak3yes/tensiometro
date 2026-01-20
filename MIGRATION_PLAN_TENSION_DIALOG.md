# PLANO DE MIGRAÇÃO: TensionMeasurementDialog
**Arquivo:** `consumo_lib/dialogs/tension/tension_measurement_dialog.py`
**Status:** NÃO MIGRADO (10 violações)
**Prioridade:** ALTA (diálogo crítico de medição)

---

## 📊 VIOLAÇÕES DETECTADAS

### Resumo
```yaml
cores_hex_6_digitos: 2   (#4CAF50, #f44336)
cores_hex_3_digitos: 2   (#FFF implícito em "white")
chamadas_setstylesheet: 6
total_violacoes: 10
```

### Detalhamento por Linha

| Linha | Tipo | Violação | Cor/String | Substituição |
|-------|------|----------|------------|--------------|
| 110 | STYLE | `color: gray;` | gray | `COLORS.DISABLED` |
| 194 | STYLE | `font-size: 14px; font-weight: bold;` | 14px, bold | `TYPO.BODY_MEDIUM + bold=True` |
| 205 | HEX6+STYLE | `background-color: #4CAF50;` | #4CAF50 | `COLORS.PRIMARY` |
| 205 | HEX3+STYLE | `color: white;` | white | `COLORS.ON_PRIMARY` |
| 205 | STYLE | `font-weight: bold; padding: 10px;` | bold, 10px | `TYPO.BODY_LARGE + bold=True` |
| 211 | HEX6+STYLE | `background-color: #f44336;` | #f44336 | `COLORS.ERROR` |
| 211 | HEX3+STYLE | `color: white;` | white | `COLORS.ON_ERROR` |
| 211 | STYLE | `font-weight: bold; padding: 10px;` | bold, 10px | `TYPO.BODY_LARGE + bold=True` |
| 259 | STYLE | `color: green;` | green | `COLORS.SUCCESS` |
| 265 | STYLE | `color: gray;` | gray | `COLORS.DISABLED` |

---

## 🔧 PASSO A PASSO DE MIGRAÇÃO

### Passo 1: Adicionar Imports do Design System

**Local:** Após linha 22 (após imports do PyQt6)

**Adicionar:**
```python
# Design System
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton
```

### Passo 2: Migrar Linha 110 - Status Label

**Antes:**
```python
self.conn_status_label = QLabel("Status: Desconectado")
self.conn_status_label.setStyleSheet("color: gray;")
conn_layout.addWidget(self.conn_status_label, 1, 0, 1, 5)
```

**Depois:**
```python
self.conn_status_label = QLabel("Status: Desconectado")
self.conn_status_label.setStyleSheet(f"color: {COLORS.DISABLED};")
conn_layout.addWidget(self.conn_status_label, 1, 0, 1, 5)
```

### Passo 3: Migrar Linha 194 - Current Value Label

**Antes:**
```python
self.current_value_label = QLabel("Última leitura: --")
self.current_value_label.setStyleSheet("font-size: 14px; font-weight: bold;")
progress_layout.addWidget(self.current_value_label)
```

**Depois:**
```python
self.current_value_label = QLabel("Última leitura: --")
self.current_value_label.setFont(TYPO.get_font(TYPO.BODY_MEDIUM, bold=True))
progress_layout.addWidget(self.current_value_label)
```

### Passo 4: Migrar Linha 205 - Start Button (OPÇÃO A: Manual)

**Antes:**
```python
self.start_btn = QPushButton("▶ Iniciar Medição")
self.start_btn.setEnabled(False)
self.start_btn.clicked.connect(self._on_start)
self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
btn_layout.addWidget(self.start_btn)
```

**Depois:**
```python
self.start_btn = QPushButton("▶ Iniciar Medição")
self.start_btn.setEnabled(False)
self.start_btn.clicked.connect(self._on_start)
self.start_btn.setStyleSheet(
    f"background-color: {COLORS.PRIMARY}; "
    f"color: {COLORS.ON_PRIMARY}; "
    f"font-weight: bold; "
    f"padding: {SPACE.MD}px;"
)
self.start_btn.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
self.start_btn.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
btn_layout.addWidget(self.start_btn)
```

### Passo 4: Migrar Linha 205 - Start Button (OPÇÃO B: StandardButton)

**Antes:**
```python
self.start_btn = QPushButton("▶ Iniciar Medição")
self.start_btn.setEnabled(False)
self.start_btn.clicked.connect(self._on_start)
self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
btn_layout.addWidget(self.start_btn)
```

**Depois:**
```python
self.start_btn = StandardButton("▶ Iniciar Medição", variant="primary")
self.start_btn.setEnabled(False)
self.start_btn.clicked.connect(self._on_start)
btn_layout.addWidget(self.start_btn)
```

**Recomendação:** Usar **OPÇÃO B** (StandardButton) para máxima conformidade com Design System.

### Passo 5: Migrar Linha 211 - Stop Button (OPÇÃO A: Manual)

**Antes:**
```python
self.stop_btn = QPushButton("⏹ Parar")
self.stop_btn.setEnabled(False)
self.stop_btn.clicked.connect(self._on_stop)
self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
btn_layout.addWidget(self.stop_btn)
```

**Depois:**
```python
self.stop_btn = QPushButton("⏹ Parar")
self.stop_btn.setEnabled(False)
self.stop_btn.clicked.connect(self._on_stop)
self.stop_btn.setStyleSheet(
    f"background-color: {COLORS.ERROR}; "
    f"color: {COLORS.ON_ERROR}; "
    f"font-weight: bold; "
    f"padding: {SPACE.MD}px;"
)
self.stop_btn.setFont(TYPO.get_font(TYPO.BODY_LARGE, bold=True))
self.stop_btn.setMinimumHeight(DIM.BUTTON_HEIGHT_MD)
btn_layout.addWidget(self.stop_btn)
```

### Passo 5: Migrar Linha 211 - Stop Button (OPÇÃO B: StandardButton)

**Antes:**
```python
self.stop_btn = QPushButton("⏹ Parar")
self.stop_btn.setEnabled(False)
self.stop_btn.clicked.connect(self._on_stop)
self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 10px;")
btn_layout.addWidget(self.stop_btn)
```

**Depois:**
```python
self.stop_btn = StandardButton("⏹ Parar", variant="danger")
self.stop_btn.setEnabled(False)
self.stop_btn.clicked.connect(self._on_stop)
btn_layout.addWidget(self.stop_btn)
```

**Recomendação:** Usar **OPÇÃO B** (StandardButton) para máxima conformidade.

**NOTA:** `StandardButton` suporta `variant="danger"` que mapeia para `COLORS.ERROR`.

### Passo 6: Migrar Linha 259 - Connected Status

**Antes:**
```python
self.conn_status_label.setText("Status: ✅ Conectado")
self.conn_status_label.setStyleSheet("color: green;")
```

**Depois:**
```python
self.conn_status_label.setText("Status: ✅ Conectado")
self.conn_status_label.setStyleSheet(f"color: {COLORS.SUCCESS};")
```

### Passo 7: Migrar Linha 265 - Disconnected Status

**Antes:**
```python
self.conn_status_label.setText("Status: Desconectado")
self.conn_status_label.setStyleSheet("color: gray;")
```

**Depois:**
```python
self.conn_status_label.setText("Status: Desconectado")
self.conn_status_label.setStyleSheet(f"color: {COLORS.DISABLED};")
```

---

## ✅ VALIDAÇÃO

### Checklist de Migração

- [ ] Import adicionado: `from consumo_lib.ui import COLORS, TYPO, SPACE, DIM`
- [ ] Import adicionado: `from consumo_lib.ui.widget_standards import StandardButton`
- [ ] Linha 110 migrada: `color: gray` → `COLORS.DISABLED`
- [ ] Linha 194 migrada: `font-size: 14px` → `TYPO.BODY_MEDIUM`
- [ ] Linha 205 migrada: `#4CAF50` → `COLORS.PRIMARY` + `StandardButton`
- [ ] Linha 211 migrada: `#f44336` → `COLORS.ERROR` + `StandardButton`
- [ ] Linha 259 migrada: `color: green` → `COLORS.SUCCESS`
- [ ] Linha 265 migrada: `color: gray` → `COLORS.DISABLED`
- [ ] Teste visual executado (verificar que não mudou nada)
- [ ] Teste funcional executado (medição de tensão funcionando)

### Testes Automatizados

```bash
# Executar testes unitários do diálogo
pytest tests/unit/test_tension_measurement_dialog.py -v

# Executar testes de integração
pytest tests/integration/test_tension_measurement_integration.py -v
```

---

## 📋 CÓDIGO COMPLETO MIGRADO

### Seção de Imports (Linhas 11-30)

```python
import logging
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox,
    QProgressBar, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QDoubleValidator, QIntValidator

# Design System
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM
from consumo_lib.ui.widget_standards import StandardButton

# Import refactored modules
from aoi_lib.tensiometer import (
    MeasurementOrchestrator,
    TensiometerSerialManager,
    ValidationError
)

logger = logging.getLogger(__name__)
```

### Seção de Criação de UI (Linhas 108-218)

```python
# Status label
self.conn_status_label = QLabel("Status: Desconectado")
self.conn_status_label.setStyleSheet(f"color: {COLORS.DISABLED};")
conn_layout.addWidget(self.conn_status_label, 1, 0, 1, 5)

# ... (código intermediário omitido) ...

self.current_value_label = QLabel("Última leitura: --")
self.current_value_label.setFont(TYPO.get_font(TYPO.BODY_MEDIUM, bold=True))
progress_layout.addWidget(self.current_value_label)

# ... (código intermediário omitido) ...

# ==================== CONTROL BUTTONS ====================
btn_layout = QHBoxLayout()

self.start_btn = StandardButton("▶ Iniciar Medição", variant="primary")
self.start_btn.setEnabled(False)
self.start_btn.clicked.connect(self._on_start)
btn_layout.addWidget(self.start_btn)

self.stop_btn = StandardButton("⏹ Parar", variant="danger")
self.stop_btn.setEnabled(False)
self.stop_btn.clicked.connect(self._on_stop)
btn_layout.addWidget(self.stop_btn)

self.close_btn = QPushButton("Fechar")
self.close_btn.clicked.connect(self.close)
btn_layout.addWidget(self.close_btn)

main_layout.addLayout(btn_layout)
```

### Seção de Handlers (Linhas 254-268)

```python
def _update_connection_ui(self, connected: bool):
    """Update UI based on connection state."""
    if connected:
        self.connect_btn.setText("🔌 Desconectar")
        self.conn_status_label.setText("Status: ✅ Conectado")
        self.conn_status_label.setStyleSheet(f"color: {COLORS.SUCCESS};")
        self.test_btn.setEnabled(True)
        self.start_btn.setEnabled(True)
    else:
        self.connect_btn.setText("🔗 Conectar")
        self.conn_status_label.setText("Status: Desconectado")
        self.conn_status_label.setStyleSheet(f"color: {COLORS.DISABLED};")
        self.test_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
```

---

## 🎯 BENEFÍCIOS DA MIGRAÇÃO

### Antes
```yaml
Manutenibilidade: BAIXA
  - Cores hardcoded em 2 lugares (#4CAF50, #f44336)
  - Tamanhos de fontes hardcoded (14px)
  - Dificuldade para mudar tema globalmente

Type-Safety: NENHUMA
  - Strings podem ter typos (#4CAF50 vs #4CAF500)
  - Sem validação em tempo de desenvolvimento

Consistência: BAIXA
  - Pode divergir de outros diálogos
  - Design inconsistente na aplicação
```

### Depois
```yaml
Manutenibilidade: ALTA
  - Single source of truth (COLORS, TYPO)
  - Mudanças em um lugar afetam toda aplicação
  - Refatoração facilitada

Type-Safety: ALTA
  - Constantes validadas em tempo de import
  - Erros de execução se token não existir

Consistência: ALTA
  - Garantia de conformidade com Design System
  - Visual consistente em toda aplicação
```

---

## 📚 REFERÊNCIAS

- **Guia de Migração:** `docs/design_system/MIGRATION.md`
- **Tokens:** `docs/design_system/TOKENS.md`
- **Componentes:** `docs/design_system/COMPONENTS.md`
- **Exemplo de migração:** `consumo_lib/widgets/status_badge.py` (commit 1f34c30)
- **Exemplo de migração:** `consumo_lib/widgets/movement_control.py` (commit 122ed8d)

---

**Plano criado em:** 2026-01-20
**Estimativa de esforço:** 30 minutos
**Complexidade:** BAIXA (refatoração simples)
**Risco:** BAIXO (apenas UI, sem lógica de negócio)
