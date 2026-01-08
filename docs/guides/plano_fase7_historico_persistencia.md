# Plano de Implementação - FASE 7: Histórico e Persistência

**Data:** 2026-01-08
**Versão:** 1.0
**Status:** 🚀 Pronto para Implementação

---

## 📋 VISÃO GERAL

### Objetivo

Implementar sistema completo de salvamento e recuperação de inspeções, permitindo que o usuário visualize histórico de medições anteriores, filtre por diversos critérios e exporte dados.

### Fluxo

```
TreeView → Posicionamento (FASE 3) ✅
    ↓
Modo de Inspeção (FASE 4) ✅
    ↓
Execução em Progresso (FASE 5) ✅
    ↓
Resultados da Inspeção (FASE 6) ✅
    ↓
    [Clicar "Salvar no Histórico"] ← IMPLEMENTAR AGORA
    ↓
    - Salvar inspeção no StencilTracker
    - Atualizar TreeView com nova medição
    ↓
Histórico (FASE 7) ← VOCÊ AQUI
    - Visualizar inspeções anteriores
    - Filtrar por data, tipo, classificação
    - Exportar dados
    ↓
FASE 8: Melhorias e Refinamentos (futura)
```

### Premissas

- FASE 6 completa e funcionando
- StencilTracker disponível em `aoi_lib/stencil_tracker.py`
- Estrutura de dados TensionRecord e InspectionRecord existentes
- Sistema de autenticação permite identificar usuário que realizou inspeção

---

## 🎨 COMPONENTES

### 1. Sistema de Salvamento

#### 1.1. Adaptação do StencilTracker

**Arquivo:** `aoi_lib/stencil_tracker.py` (já existe)

**O que precisa fazer:**
- Verificar se os métodos `add_tension_record()` e `add_inspection_record()` existem
- Adaptar os dados do InspectionWorker para o formato esperado pelo StencilTracker
- Criar método `add_inspection_complete()` que salve ambos os tipos (modo "both")

**Estrutura de Dados Esperada:**

```python
# TensionRecord (já existe em aoi_lib/stencil_tracker.py)
@dataclass
class TensionRecord:
    timestamp: str
    grid_size: str
    measurements: List[float]  # Lista completa de medições
    tension_avg: float
    tension_min: float
    tension_max: float
    tension_std: float
    classification: str  # "OK", "WARNING", "NOK"
    operator: str  # Nome do usuário que realizou

# InspectionRecord (já existe em aoi_lib/stencil_tracker.py)
@dataclass
class InspectionRecord:
    timestamp: str
    gerber_file: str
    image_path: str
    results: dict  # Dicionário com resultados
    classification: str
    operator: str
```

#### 1.2. Handler de Salvamento

**Arquivo:** `consumo_lib/main_window.py`

**Novo método:**

```python
def save_inspection_to_history(self, stencil: dict, results: dict, mode: str):
    """
    Salva inspeção no histórico do stencil

    Args:
        stencil: Dicionário com dados do stencil
        results: Resultados da inspeção
        mode: Modo executado ("tension", "inspection", "both")
    """
    from datetime import datetime
    from aoi_lib import StencilTracker, TensionRecord, InspectionRecord

    user = self.auth_service.get_current_user()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    tracker = StencilTracker()

    if mode in ["tension", "both"]:
        # Salvar registro de tensão
        tension_record = TensionRecord(
            timestamp=timestamp,
            grid_size=results.get('grid_size', '5x5'),
            measurements=[],  # Lista vazia por enquanto (simulação)
            tension_avg=results.get('tension_avg', 0.0),
            tension_min=results.get('tension_min', 0.0),
            tension_max=results.get('tension_max', 0.0),
            tension_std=results.get('tension_std', 0.0),
            classification=results.get('classification', 'UNKNOWN'),
            operator=user.username
        )

        tracker.add_tension_record(stencil['code'], tension_record)
        logger.info(f"Registro de tensão salvo: {stencil['code']}")

    if mode in ["inspection", "both"]:
        # Salvar registro de inspeção visual
        if mode == "both":
            inspection_results = results.get('inspection_results', {})
        else:
            inspection_results = results

        inspection_record = InspectionRecord(
            timestamp=timestamp,
            gerber_file="",  # Vazio por enquanto (simulação)
            image_path="",  # Vazio por enquanto
            results=inspection_results,
            classification=inspection_results.get('classification', 'UNKNOWN'),
            operator=user.username
        )

        tracker.add_inspection_record(stencil['code'], inspection_record)
        logger.info(f"Registro de inspeção salvo: {stencil['code']}")

    QMessageBox.information(
        self,
        "Salvo com Sucesso",
        f"Inspeção do stencil {stencil['code']} foi salva no histórico!\n\n"
        f"Modo: {self._get_mode_title(mode)}\n"
        f"Operador: {user.username}\n"
        f"Data/Hora: {timestamp}"
    )
```

### 2. Dialog de Histórico

**Arquivo:** `consumo_lib/dialogs/inspection_history_dialog.py`

**Funcionalidades:**
- Lista de todas as inspeções do stencil selecionado
- Filtros por tipo (Tensão/Inspeção/Ambos)
- Filtros por classificação (OK/WARNING/NOK)
- Filtros por período (data inicial e data final)
- Busca por nome do operador
- Tabela com dados principais (data, tipo, classificação, operador)
- Botão para ver detalhes de uma inspeção específica
- Botão para exportar para CSV

**Layout:**

```
┌────────────────────────────────────────────────────────────────────────┐
│  Histórico de Inspeções                                            │
│                                                                  [X] │
│                                                                      │
│  Stencil: STENCIL-ABC-123                                           │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  FILTROS                                                         │ │
│  │                                                                  │ │
│  │  Tipo: [Todos ▼]  Classificação: [Todas ▼]                      │ │
│  │  Data Inicial: [__/__/____]  Data Final: [__/__/____]            │ │
│  │  Operador: [Digite para filtrar...            ]                  │ │
│  │                                                                  │ │
│  │           [Aplicar Filtros]  [Limpar Filtros]  [Exportar CSV]   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  INSPEÇÕES (15 registros)                                        │ │
│  │                                                                  │ │
│  │  ┌────┬────────────────────┬───────────┬──────────────┬─────────┐ │ │
│  │  │ ID │ Data/Hora          │ Tipo      │ Classificação│ Operador│ │ │
│  │  ├────┼────────────────────┼───────────┼──────────────┼─────────┤ │ │
│  │  │ 15 │ 08/01/2026 17:45   │ Tensão    │ ✅ OK        │ joao    │ │ │
│  │  │ 14 │ 08/01/2026 16:30   │ Ambos     │ ✅ OK        │ maria   │ │ │
│  │  │ 13 │ 08/01/2026 15:15   │ Inspeção  │ ⚠️ WARNING   │ joao    │ │ │
│  │  │ 12 │ 07/01/2026 14:00   │ Tensão    │ ❌ NOK       │ joao    │ │ │
│  │  │ ...│                    │           │              │         │ │ │
│  │  └────┴────────────────────┴───────────┴──────────────┴─────────┘ │ │
│  │                            [Ver Detalhes]  [Fechar]            │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

### 3. Visualização de Detalhes

**Arquivo:** `consumo_lib/dialogs/inspection_details_dialog.py`

**Funcionalidades:**
- Exibir todos os dados de uma inspeção específica
- Mostrar métricas completas (mesmo formato do InspectionResultsDialog)
- Permitir editar observações
- Botão para gerar PDF individual
- Botão para excluir registro (se usuário for ADMIN)

**Layout:**

```
┌────────────────────────────────────────────────────────────────────────┐
│  Detalhes da Inspeção #15                                           │
│                                                                  [X] │
│                                                                      │
│  Data/Hora: 08/01/2026 17:45:30                                     │
│  Operador: joao                                                      │
│  Tipo: Medição de Tensão                                             │
│  Classificação: ✅ APROVADO                                          │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  DADOS DA INSPEÇÃO                                               │ │
│  │                                                                  │ │
│  │  Tensão Média: 32.5 N/cm                                        │ │
│  │  Grid: 5x5                                                       │ │
│  │  Menor Valor: 30.2 N/cm                                         │ │
│  │  Maior Valor: 34.8 N/cm                                         │ │
│  │  Desvio Padrão: 1.45 N/cm                                       │ │
│  │                                                                  │ │
│  │  Observações:                                                    │ │
│  │  ┌────────────────────────────────────────────────────────────┐ │ │
│  │  │ Medição realizada rotineiramente. Todos os pontos dentro   │ │ │
│  │  │ da faixa aceitável.                                        │ │ │
│  │  └────────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│                 [Editar Observações]  [Gerar PDF]  [Excluir]  [Fechar]│
└────────────────────────────────────────────────────────────────────────┘
```

### 4. Integração com TreeView

**Modificação necessária em `consumo_lib/tabs/tree_view_tab.py`:**

**Adicionar botão "Ver Histórico":**

```python
# No método _create_stencil_list()
history_button = QPushButton("📋 Histórico")
history_button.setMinimumHeight(40)
history_button.setStyleSheet("""
    QPushButton {
        background-color: #8B5CF6;
        color: white;
        font-size: 13px;
        font-weight: 600;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
    }
    QPushButton:hover {
        background-color: #7C3AED;
    }
""")
history_button.clicked.connect(self.show_history)
layout.addWidget(history_button)
```

**Novo método `show_history()`:**

```python
def show_history(self):
    """Exibe dialog de histórico do stencil selecionado"""
    selected = self.stencil_list.currentItem()
    if not selected:
        QMessageBox.warning(self, "Aviso", "Selecione um stencil primeiro.")
        return

    stencil_code = selected.text()
    self.parent().show_inspection_history(stencil_code)
```

---

## 💻 IMPLEMENTAÇÃO

### Estrutura de Arquivos

```
consumo_lib/dialogs/
├── __init__.py (atualizar)
├── inspection_history_dialog.py (NOVO)
└── inspection_details_dialog.py (NOVO)

consumo_lib/tabs/
└── tree_view_tab.py (modificar - adicionar botão histórico)

consumo_lib/main_window.py (modificar - adicionar métodos de salvamento)

aoi_lib/stencil_tracker.py (verificar - possivelmente adaptar)
```

### Implementação por Ordem de Prioridade

#### 1. Sistema de Salvamento (Prioridade ALTA)

**Arquivo:** `consumo_lib/main_window.py`

**Modificar `InspectionResultsDialog.on_save_clicked()`:**

Em vez de mostrar placeholder, chamar método real de salvamento:

```python
# No InspectionResultsDialog
def on_save_clicked(self):
    """Handler: Botão Salvar clicado"""
    from consumo_lib.main_window import MainWindow

    parent_window = self.parent()
    if isinstance(parent_window, MainWindow):
        success = parent_window.save_inspection_to_history(
            {'code': self.stencil_code},
            self.results,
            self.mode
        )
        if success:
            self.accept()  # Fecha o dialog após salvar
```

#### 2. Dialog de Histórico (Prioridade ALTA)

**Criar arquivo completo** seguindo layout acima.

**Principais componentes:**
- QTableWidget para listar inspeções
- QComboBox para filtros (tipo, classificação)
- QDateTimeEdit para filtros de data
- QLineEdit para busca por operador
- Botões: Aplicar Filtros, Limpar Filtros, Exportar CSV, Ver Detalhes

#### 3. Visualização de Detalhes (Prioridade MÉDIA)

**Criar arquivo completo** seguindo layout acima.

**Principais componentes:**
- QLabel para todos os campos (data, operador, tipo, classificação)
- QTextEdit para observações (editável)
- Botões: Editar Observações, Gerar PDF, Excluir (só admin), Fechar

#### 4. Integração TreeView (Prioridade MÉDIA)

**Modificar `tree_view_tab.py`:**
- Adicionar botão "📋 Histórico" ao lado do botão "Inspecionar"
- Implementar `show_history()` para chamar dialog

#### 5. Exportação CSV (Prioridade BAIXA)

**Função simples para exportar tabela:**

```python
def export_to_csv(self, table_widget: QTableWidget, filename: str):
    """Exporta tabela para CSV"""
    import csv

    rows = table_widget.rowCount()
    cols = table_widget.columnCount()

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        headers = []
        for col in range(cols):
            headers.append(table_widget.horizontalHeaderItem(col).text())
        writer.writerow(headers)

        # Data
        for row in range(rows):
            data = []
            for col in range(cols):
                item = table_widget.item(row, col)
                data.append(item.text() if item else "")
            writer.writerow(data)

    QMessageBox.information(self, "Exportar", f"Dados exportados para {filename}")
```

---

## 🔗 INTEGRAÇÃO

### 1. Atualizar `__init__.py`

**Arquivo:** `consumo_lib/dialogs/__init__.py`

```python
# History dialogs (NOVO - FASE 7)
from .inspection_history_dialog import InspectionHistoryDialog
from .inspection_details_dialog import InspectionDetailsDialog
__all__.append('InspectionHistoryDialog')
__all__.append('InspectionDetailsDialog')
```

### 2. Adicionar no MainWindow

**Arquivo:** `consumo_lib/main_window.py`

```python
def show_inspection_history(self, stencil_code: str):
    """
    Exibe dialog de histórico do stencil

    Args:
        stencil_code: Código do stencil
    """
    from consumo_lib.dialogs import InspectionHistoryDialog

    dialog = InspectionHistoryDialog(stencil_code, self)
    dialog.exec()

def save_inspection_to_history(self, stencil: dict, results: dict, mode: str) -> bool:
    """
    Salva inspeção no histórico do stencil

    Args:
        stencil: Dicionário com dados do stencil
        results: Resultados da inspeção
        mode: Modo executado

    Returns:
        True se salvou com sucesso, False caso contrário
    """
    # Implementação completa (mostrada acima)
    pass
```

---

## ✅ CRITÉRIOS DE ACEITE

### Funcionalidades de Salvamento
- [ ] Botão "Salvar no Histórico" salva dados reais no StencilTracker
- [ ] Registro inclui: timestamp, operador, classificação, métricas
- [ ] Modo "both" salva tanto TensionRecord quanto InspectionRecord
- [ ] TreeView atualiza automaticamente após salvamento
- [ ] Mensagem de confirmação exibe dados salvos

### Funcionalidades de Histórico
- [ ] Dialog lista todas as inspeções do stencil
- [ ] Filtros por tipo funcionam (Tensão/Inspeção/Ambos/Todos)
- [ ] Filtros por classificação funcionam (OK/WARNING/NOK/Todas)
- [ ] Filtro por período funciona (data inicial/final)
- [ ] Busca por operador funciona
- [ ] Botão "Ver Detalhes" exibe dados completos

### Visualização de Detalhes
- [ ] Exibe todos os dados da inspeção selecionada
- [ ] Campo de observações é editável
- [ ] Botão "Gerar PDF" mostra placeholder (FASE 8)
- [ ] Botão "Excluir" só aparece para ADMIN
- [ ] Exclusão pede confirmação

### Exportação
- [ ] Exportar CSV gera arquivo com dados da tabela
- [ ] Arquivo CSV abre corretamente no Excel
- [ ] Nomes de colunas são legíveis

### Visual
- [ ] Layout organizado e legível
- [ ] Tabela tem scroll se houver muitos registros
- [ ] Cores de classificação visíveis na tabela
- [ ] Nada cortado/truncado

---

## 🧪 TESTES MANUAIS

### Teste 1: Salvamento
```
1. Selecionar stencil STENCIL-ABC-123
2. Executar inspeção (qualquer modo)
3. Clicar "Salvar no Histórico"
4. ✅ Mensagem confirma salvamento
5. ✅ Abrir histórico do stencil
6. ✅ Nova inspeção aparece na lista
```

### Teste 2: Filtros
```
1. Abrir histórico com 15+ registros
2. Filtrar por tipo: "Tensão"
3. ✅ Só aparecem registros de tensão
4. Filtrar por classificação: "OK"
5. ✅ Só aparecem registros OK
6. Limpar filtros
7. ✅ Todos os registros reaparecem
```

### Teste 3: Busca
```
1. Digitar "joao" no campo Operador
2. ✅ Só aparecem registros do joao
3. Limpar busca
4. ✅ Todos os registros reaparecem
```

### Teste 4: Detalhes
```
1. Selecionar registro na tabela
2. Clicar "Ver Detalhes"
3. ✅ Dialog exibe todos os dados
4. Editar observações
5. ✅ Observações são salvas
```

### Teste 5: Exportar
```
1. Aplicar filtros (ex: só OK)
2. Clicar "Exportar CSV"
3. ✅ Arquivo é salvo
4. Abrir no Excel
5. ✅ Dados correspondem aos filtros aplicados
```

### Teste 6: Exclusão (ADMIN)
```
1. Login como admin
2. Abrir detalhes de uma inspeção
3. Clicar "Excluir"
4. ✅ Confirmação é pedida
5. Confirmar exclusão
6. ✅ Registro é removido do histórico
```

---

## 📁 ARQUIVOS A CRIAR/MODIFICAR

### Criar (2 arquivos)
- `consumo_lib/dialogs/inspection_history_dialog.py`
- `consumo_lib/dialogs/inspection_details_dialog.py`

### Modificar (3 arquivos)
- `consumo_lib/dialogs/__init__.py` (adicionar imports)
- `consumo_lib/main_window.py` (adicionar salvamento e método show_history)
- `consumo_lib/tabs/tree_view_tab.py` (adicionar botão histórico)

### Verificar (1 arquivo)
- `aoi_lib/stencil_tracker.py` (verificar se métodos existem)

---

## ⏱️ ESTIMATIVA

- **Sistema de salvamento:** 45 min
- **Dialog de histórico:** 2 horas
- **Dialog de detalhes:** 1 hora
- **Integração TreeView:** 30 min
- **Exportação CSV:** 30 min
- **Testes e ajustes:** 1 hora
- **Total:** 5 horas

---

## 🎯 PRÓXIMA FASE

Após validação desta FASE 7:

**FASE 8: Melhorias e Refinamentos Finais**
- Geração real de PDF com dados da inspeção
- Heatmap real de tensão (cores no grid)
- Gráficos de tendência histórica
- Melhorias visuais baseadas em feedback do usuário
- Otimizações de performance
- Documentação final do sistema

---

**Documento criado:** 2026-01-08
**Status:** 🚀 Pronto para implementação
