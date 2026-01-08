# Plano de Implementação - FASE 5: Execução (Tela de Progresso)

**Data:** 2026-01-08
**Versão:** 1.0
**Status:** 🚀 Pronto para Implementação

---

## 📋 VISÃO GERAL

### Objetivo

Criar tela de progresso que exibe o status da execução da inspeção em tempo real, mostrando o andamento das operações, permitindo cancelamento e exibindo logs detalhados.

### Fluxo

```
TreeView (usuário seleciona programa)
    ↓
Usuário clica "Inspecionar Stencil"
    ↓
Dialog: Confirmação de Posicionamento (FASE 3) ✅
    ↓
Usuário confirma posicionamento
    ↓
Dialog: Escolha de Modo (FASE 4) ✅
    ↓
Usuário seleciona modo (Tensão/Inspeção/Ambos)
    ↓
Dialog: Execução em Progresso (FASE 5) ← VOCÊ AQUI
    ↓
    - Exibe progresso em tempo real
    - Mostra etapa atual
    - Log de operações
    - Possibilidade de cancelar
    ↓
FASE 6: Análise Visual / Julgamento Humano
```

### Premissas

- FASE 4 (Escolha de Modo) está completa e funcionando
- Modo selecionado está armazenado em `self.selected_inspection_mode`
- Sistema de log já está configurado
- QThread para operações em background (padrão PyQt6)

---

## 🎨 COMPONENTES

### 1. Dialog de Progresso

**Arquivo:** `consumo_lib/dialogs/inspection_progress_dialog.py`

**Funcionalidades:**
- Título dinâmico baseado no modo selecionado
- Barra de progresso circular ou linear
- Label de status (etapa atual)
- Área de log (scrollable)
- Botão "Cancelar" (habilitado durante execução)
- Botão "Fechar" (habilitado após conclusão)
- Atualização em tempo real via sinais

**Layout:**
```
┌─────────────────────────────────────────────────────────┐
│  Execução: Apenas Tensão                                 │
│  Stencil: STENCIL-ABC-123                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ████████████████████░░░░░░░░  60%                      │
│                                                          │
│  Status: Medindo ponto 15 de 25                          │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Log de Operações                              │   │
│  │                                                 │   │
│  │ ✓ Iniciando medição de tensão...              │   │
│  │ ✓ Movendo CNC para posição (100, 150, 0)       │   │
│  │ ✓ Medindo tensão: 32.5 N/cm                   │   │
│  │ ✓ Movendo CNC para posição (120, 150, 0)       │   │
│  │ → Medindo tensão...                            │   │
│  │   Aguardando Z-axis...                         │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│                  [Cancelar Execução]                    │
└─────────────────────────────────────────────────────────┘
```

### 2. Etapas da Execução

**Modo TENSÃO:**
```python
STEPS_TENSION = [
    "Iniciando medição de tensão",
    "Movendo CNC para posição inicial",
    "Descendo Z-axis para contato",
    "Medindo tensão no ponto",
    "Retornando Z-axis",
    "Calculando média de tensão",
    "Gerando heatmap de resultados",
    "Finalizando medição"
]
```

**Modo INSPEÇÃO:**
```python
STEPS_INSPECTION = [
    "Iniciando inspeção visual",
    "Carregando arquivo Gerber",
    "Posicionando backlight",
    "Capturando imagem do stencil",
    "Processando imagem",
    "Renderizando máscaras Gerber",
    "Analisando aberturas",
    "Classificando resultados",
    "Gerando relatório visual",
    "Finalizando inspeção"
]
```

**Modo AMBOS:**
```python
STEPS_BOTH = STEPS_TENSION + [
    "Iniciando inspeção visual",
    ...
]  # Combina ambos
```

### 3. Atualização de Progresso

**Sinais emitidos pelo Worker:**
```python
class InspectionWorker(QThread):
    # Sinais de progresso
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    step_changed = pyqtSignal(str)  # step_description
    log_message = pyqtSignal(str)  # log_text
    measurement_complete = pyqtSignal(dict)  # results
    execution_complete = pyqtSignal(bool, str)  # success, message
```

### 4. Formatação de Logs

**Tipos de mensagem:**
```python
LOG_TYPES = {
    "INFO": "✓",
    "PROGRESS": "→",
    "WARNING": "⚠",
    "ERROR": "✗",
    "SUCCESS": "✅"
}

# Exemplos:
"✓ Iniciando medição de tensão..."
"→ Medindo tensão..."
"⚠ Tensão abaixo do esperado"
"✗ Erro de comunicação com PLC"
"✅ Medição concluída com sucesso"
```

---

## 💻 IMPLEMENTAÇÃO

### Estrutura de Arquivos

```
consumo_lib/
├── dialogs/
│   ├── __init__.py (atualizar)
│   └── inspection_progress_dialog.py (NOVO)
└── threads/
    ├── inspection_worker.py (NOVO - Worker thread)
    └── __init__.py (atualizar)
```

### Código Completo

#### 1. InspectionProgressDialog

```python
"""
Dialog de Progresso de Inspeção

Exibe progresso em tempo real da execução de inspeção,
com barra de progresso, logs detalhados e controle de cancelamento.
"""

import logging
from datetime import datetime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QTextCursor

logger = logging.getLogger(__name__)


class InspectionProgressDialog(QDialog):
    """
    Dialog de progresso de inspeção

    Sinais:
        execution_cancelled: Emitido quando usuário cancela
        execution_completed: Emitido quando execução termina
    """

    execution_cancelled = pyqtSignal()
    execution_completed = pyqtSignal(dict)

    def __init__(self, stencil_code: str, mode: str, parent=None):
        """
        Inicializa dialog de progresso

        Args:
            stencil_code: Código do stencil
            mode: Modo de inspeção ("tension", "inspection", "both")
            parent: Widget pai
        """
        super().__init__(parent)
        self.stencil_code = stencil_code
        self.mode = mode
        self.is_running = False
        self.is_complete = False

        self.setup_ui()

    def setup_ui(self):
        """Configura interface do dialog"""
        self.setWindowTitle("Execução de Inspeção")
        self.setModal(True)
        self.setFixedSize(700, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Título
        mode_title = self._get_mode_title()
        title_label = QLabel(f"Execução: {mode_title}")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #111827;")
        layout.addWidget(title_label)

        # Subtítulo
        subtitle_label = QLabel(f"Stencil: {self.stencil_code}")
        subtitle_font = subtitle_label.font()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: #6B7280;")
        layout.addWidget(subtitle_label)

        layout.addSpacing(10)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E5E7EB;
                border-radius: 6px;
                text-align: center;
                font-size: 12px;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Label de status
        self.status_label = QLabel("Preparando execução...")
        self.status_label.setStyleSheet("color: #374151; font-size: 13px; font-weight: 500;")
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        # Área de log
        log_group = QLabel("Log de Operações")
        log_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        log_group.setStyleSheet("color: #374151;")
        layout.addWidget(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(250)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                color: #1F2937;
            }
        """)
        layout.addWidget(self.log_text)

        layout.addSpacing(10)

        # Botões
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.cancel_button = QPushButton("Cancelar Execução")
        self.cancel_button.setMinimumWidth(160)
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
            QPushButton:disabled {
                background-color: #E5E7EB;
                color: #9CA3AF;
            }
        """)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        buttons_layout.addWidget(self.cancel_button)

        self.close_button = QPushButton("Fechar")
        self.close_button.setMinimumWidth(120)
        self.close_button.setMinimumHeight(40)
        self.close_button.hide()  # Inicialmente oculto
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        self.close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.close_button)

        layout.addLayout(buttons_layout)

    def _get_mode_title(self) -> str:
        """Retorna título legível do modo"""
        titles = {
            "tension": "Medição de Tensão",
            "inspection": "Inspeção Visual",
            "both": "Inspeção Completa (Tensão + Visual)"
        }
        return titles.get(self.mode, "Inspeção")

    def start_execution(self, worker: QThread):
        """
        Inicia execução com worker thread

        Args:
            worker: QThread com lógica de execução
        """
        self.is_running = True
        self.worker = worker

        # Conecta sinais
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.step_changed.connect(self.on_step_changed)
        self.worker.log_message.connect(self.add_log)
        self.worker.execution_complete.connect(self.on_execution_complete)

        # Inicia worker
        self.worker.start()

        self.add_log("✓ Iniciando execução...")

    def on_progress_updated(self, current: int, total: int, message: str):
        """
        Handler: Progresso atualizado

        Args:
            current: Valor atual
            total: Valor total
            message: Mensagem de progresso
        """
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(percentage)
        self.status_label.setText(f"{message} ({current}/{total})")

    def on_step_changed(self, step_description: str):
        """
        Handler: Etapa mudou

        Args:
            step_description: Descrição da etapa atual
        """
        self.add_log(f"→ {step_description}")

    def add_log(self, message: str):
        """
        Adiciona mensagem ao log

        Args:
            message: Mensagem para adicionar
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"

        self.log_text.append(log_line)
        self.log_text.moveCursor(QTextCursor.End)

        logger.info(f"Progress: {message}")

    def on_execution_complete(self, success: bool, message: str):
        """
        Handler: Execução completada

        Args:
            success: True se sucesso, False se erro
            message: Mensagem de resultado
        """
        self.is_running = False
        self.is_complete = True

        # Desabilita botão cancelar
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()

        # Mostra botão fechar
        self.close_button.show()

        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("Execução concluída com sucesso!")
            self.add_log(f"✅ {message}")
        else:
            self.status_label.setText("Execução concluída com erros")
            self.add_log(f"✗ {message}")

    def on_cancel_clicked(self):
        """Handler: Botão Cancelar clicado"""
        if self.is_running and hasattr(self, 'worker'):
            self.add_log("⚠ Cancelando execução...")
            self.worker.terminate()
            self.worker.wait(3000)  # Aguarda até 3 segundos

            self.is_running = False
            self.execution_cancelled.emit()
            self.reject()

    def get_results(self) -> dict:
        """
        Retorna resultados da execução

        Returns:
            Dict com resultados (se disponível)
        """
        if hasattr(self, 'worker') and hasattr(self.worker, 'results'):
            return self.worker.results
        return {}
```

#### 2. InspectionWorker (Esqueleto)

```python
"""
Worker Thread para Execução de Inspeção

Executa inspeção em background thread para não bloquear UI.
"""

import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class InspectionWorker(QThread):
    """
    Worker thread para execução de inspeção

    Sinais:
        progress_updated: Emitido com (current, total, message)
        step_changed: Emitido com step_description
        log_message: Emitido com log_text
        execution_complete: Emitido com (success, message)
    """

    progress_updated = pyqtSignal(int, int, str)
    step_changed = pyqtSignal(str)
    log_message = pyqtSignal(str)
    execution_complete = pyqtSignal(bool, string)

    def __init__(self, stencil_code: str, mode: str, parent=None):
        """
        Inicializa worker

        Args:
            stencil_code: Código do stencil
            mode: Modo de inspeção
            parent: Objeto pai
        """
        super().__init__(parent)
        self.stencil_code = stencil_code
        self.mode = mode
        self.results = {}
        self._is_cancelled = False

    def run(self):
        """Executa inspeção (método principal)"""
        try:
            self.log_message.emit(f"Iniciando inspeção do stencil {self.stencil_code}")

            if self.mode == "tension":
                self._run_tension_inspection()
            elif self.mode == "inspection":
                self._run_visual_inspection()
            elif self.mode == "both":
                self._run_both_inspections()

            self.execution_complete.emit(True, "Inspeção concluída com sucesso")

        except Exception as e:
            logger.error(f"Erro na execução: {e}")
            self.execution_complete.emit(False, f"Erro: {str(e)}")

    def _run_tension_inspection(self):
        """Executa medição de tensão"""
        # TODO: Implementar medição real de tensão
        # Por enquanto, simula progresso
        steps = 8
        for i in range(steps):
            if self._is_cancelled:
                return

            self.step_changed.emit(f"Medindo ponto {i+1} de {steps}")
            self.progress_updated.emit(i+1, steps, f"Ponto {i+1}")
            self.msleep(500)  # Simula trabalho

        self.results = {
            "mode": "tension",
            "tension_avg": 32.5,
            "points_measured": steps
        }

    def _run_visual_inspection(self):
        """Executa inspeção visual"""
        # TODO: Implementar inspeção visual real
        steps = 10
        for i in range(steps):
            if self._is_cancelled:
                return

            self.step_changed.emit(f"Processando abertura {i+1} de {steps}")
            self.progress_updated.emit(i+1, steps, f"Abertura {i+1}")
            self.msleep(300)

        self.results = {
            "mode": "inspection",
            "apertures_analyzed": steps,
            "classification": "OK"
        }

    def _run_both_inspections(self):
        """Executa ambas as inspeções"""
        self._run_tension_inspection()
        if not self._is_cancelled:
            self._run_visual_inspection()

    def cancel(self):
        """Solicita cancelamento"""
        self._is_cancelled = True
```

---

## 🔗 INTEGRAÇÃO

### 1. Atualizar `__init__.py`

**Arquivo:** `consumo_lib/dialogs/__init__.py`

```python
# Progress dialogs (NOVO - FASE 5)
from .inspection_progress_dialog import InspectionProgressDialog
__all__.append('InspectionProgressDialog')
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

    # FASE 5: Executar inspeção
    self.run_inspection(stencil)

def run_inspection(self, stencil: dict):
    """
    Executa inspeção com tela de progresso

    Args:
        stencil: Dicionário com dados do stencil
    """
    from consumo_lib.dialogs import InspectionProgressDialog
    from consumo_lib.threads import InspectionWorker

    mode = getattr(self, 'selected_inspection_mode', 'tension')

    # Cria dialog de progresso
    progress_dialog = InspectionProgressDialog(
        stencil['code'],
        mode,
        self
    )

    # Cria worker thread
    worker = InspectionWorker(
        stencil['code'],
        mode,
        self
    )

    # Conecta sinais
    worker.execution_complete.connect(
        lambda success, msg: self.on_inspection_complete(success, msg, stencil)
    )

    # Inicia execução
    progress_dialog.start_execution(worker)

    # Mostra dialog
    progress_dialog.exec()

def on_inspection_complete(self, success: bool, message: str, stencil: dict):
    """
    Handler: Inspeção completada

    Args:
        success: True se sucesso
        message: Mensagem de resultado
        stencil: Dados do stencil
    """
    if success:
        logger.info(f"Inspeção concluída: {stencil['code']} - {message}")
        QMessageBox.information(
            self,
            "Inspeção Concluída",
            f"Inspeção do stencil {stencil['code']} concluída com sucesso!\n\n"
            f"{message}\n\n"
            f"FASE 6 (Análise Visual) será implementada a seguir."
        )
    else:
        logger.error(f"Inspeção falhou: {stencil['code']} - {message}")
        QMessageBox.warning(
            self,
            "Erro na Inspeção",
            f"A inspeção não pôde ser concluída:\n\n{message}"
        )
```

---

## ✅ CRITÉRIOS DE ACEITE

### Funcionalidades
- [ ] Dialog exibe após seleção de modo
- [ ] Barra de progresso funcional (0-100%)
- [ ] Status label atualiza em tempo real
- [ ] Log de operações exibe com timestamps
- [ ] Botão "Cancelar" interrompe execução
- [ ] Botão "Fechar" aparece após conclusão
- [ ] Worker thread não bloqueia UI

### Logs
- [ ] Logs com timestamps [HH:MM:SS]
- [ ] Ícones para cada tipo (✓ → ⚠ ✗ ✅)
- [ ] Log scroll automático para última mensagem
- [ ] Área de log scrollable manualmente

### Estados
- [ ] Em execução: Barra avançando, logs aparecendo
- [ ] Completo: Barra em 100%, botão Fechar visível
- [ ] Cancelado: Dialog fecha, execução para

---

## 🧪 TESTES MANUAIS

### Teste 1: Fluxo Completo até FASE 5
```
1. Login → Programas → Selecionar stencil
2. Confirmar posicionamento
3. Selecionar modo "Apenas Tensão"
4. ✅ Dialog de progresso exibe
5. ✅ Barra avança de 0 a 100%
6. ✅ Logs aparecem em tempo real
7. ✅ Status atualiza
```

### Teste 2: Cancelamento
```
1. Iniciar execução
2. Aguardar alguns segundos
3. Clicar "Cancelar Execução"
4. ✅ Execução para
5. ✅ Dialog fecha
6. ✅ Log "Cancelando execução..." aparece
```

### Teste 3: Conclusão Normal
```
1. Aguardar execução completar
2. ✅ Barra chega em 100%
3. ✅ Status "Execução concluída"
4. ✅ Botão "Cancelar" desaparece
5. ✅ Botão "Fechar" aparece
6. ✅ Clicar "Fechar" fecha dialog
```

### Teste 4: Logs Detalhados
```
1. Verificar timestamps em todas as mensagens
2. Verificar ícones (✓ → ⚠ ✗ ✅)
3. Verificar scroll automático
4. Verificar scroll manual funcional
```

### Teste 5: Diferentes Modos
```
1. Testar modo "Tension"
2. Testar modo "Inspection"
3. Testar modo "Both"
4. ✅ Cada modo mostra steps apropriados
5. ✅ Título atualiza corretamente
```

---

## 📁 ARQUIVOS A CRIAR/MODIFICAR

### Criar (2 arquivos)
- `consumo_lib/dialogs/inspection_progress_dialog.py`
- `consumo_lib/threads/inspection_worker.py`

### Modificar (3 arquivos)
- `consumo_lib/dialogs/__init__.py` (adicionar import)
- `consumo_lib/threads/__init__.py` (adicionar import)
- `consumo_lib/main_window.py` (adicionar métodos)

---

## ⏱️ ESTIMATIVA

- **Criação do dialog:** 45 min
- **Criação do worker:** 30 min
- **Integração no MainWindow:** 20 min
- **Testes e ajustes:** 25 min
- **Total:** 2 horas

---

## 🎯 PRÓXIMA FASE

Após validação desta FASE 5:

**FASE 6: Análise Visual / Julgamento Humano**
- Exibir resultados da inspeção
- Interface para julgamento manual (se necessário)
- Salvar resultados no histórico
- Gerar PDF preliminar

---

**Documento criado:** 2026-01-08
**Status:** 🚀 Pronto para implementação
