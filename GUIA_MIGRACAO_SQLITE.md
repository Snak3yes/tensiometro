# 🗃️ Guia de Migração para SQLite e Histórico de Inspeções

> **Data:** 11/12/2024  
> **Versão:** 0.4.1

---

## 📋 Resumo das Novas Funcionalidades

### 1. Histórico de Inspeções Visuais

O sistema agora suporta o registro completo de inspeções visuais no histórico de cada stencil.

**Novo modelo de dados:** `InspectionRecord`

```python
@dataclass
class InspectionRecord:
    timestamp: str
    total_apertures: int
    ok_count: int
    partial_count: int
    blocked_count: int
    result: str  # "PASS" ou "FAIL"
    pass_rate: float
    gerber_file: str
    operator: str
    recipe_name: str
    report_path: str  # Caminho do PDF gerado
    defects: List[Dict]
    notes: str
```

**Métodos adicionados no `StencilTracker`:**

- `add_inspection_record(code, record)` - Salva registro de inspeção
- `get_inspection_history(code, limit)` - Obtém histórico de inspeções
- `get_combined_history(code, limit)` - Histórico combinado (tensão + inspeção)
- `get_inspection_stats(code)` - Estatísticas de inspeções visuais

### 2. Banco de Dados SQLite

Nova classe `StencilDatabase` para persistência otimizada.

**Vantagens:**

| JSON (Legado) | SQLite (Novo) |
|---------------|---------------|
| Arquivos por stencil | Arquivo único |
| Leitura lenta com muitos dados | Queries indexadas |
| Difícil consultas complexas | SQL completo |
| Backup manual | Backup simples |

---

## 🔄 Como Migrar de JSON para SQLite

### Opção 1: Via Linha de Comando

```bash
cd c:\Users\sense\PycharmProjects\Tensiometro
python -c "from aoi_lib import migrate_json_to_sqlite; migrate_json_to_sqlite()"
```

### Opção 2: No Código Python

```python
from aoi_lib.stencil_database import StencilDatabase, migrate_json_to_sqlite

# Migrar dados existentes
stats = migrate_json_to_sqlite()
print(f"Migrados: {stats['stencils']} stencils")
print(f"          {stats['tension_records']} registros de tensão")
print(f"          {stats['inspection_records']} registros de inspeção")

# Usar o banco SQLite
db = StencilDatabase()
stencils = db.list_stencils()
```

### Opção 3: Via Script Standalone

```bash
python aoi_lib/stencil_database.py migrate
```

---

## 📊 Usando o StencilDatabase

### Inicialização

```python
from aoi_lib import StencilDatabase

# Usa caminho padrão: data/stencils.db
db = StencilDatabase()

# Ou caminho customizado
db = StencilDatabase(db_path="C:/meus_dados/stencils.db")
```

### CRUD de Stencils

```python
# Criar stencil
stencil = db.create_stencil(
    code="STN-001",
    description="Stencil de teste",
    recipe_name="Receita A"
)

# Buscar stencil
stencil = db.get_stencil("STN-001")

# Listar todos
todos = db.list_stencils()
ativos = db.list_stencils(status="active")

# Busca por texto
resultados = db.search_stencils("teste")
```

### Registrar Medição de Tensão

```python
from aoi_lib import TensionRecord

record = TensionRecord.from_tension_data(
    tension_data=dados_medicao,  # Dicionário com measurements
    recipe_name="Receita A",
    operator="Operador 1"
)

db.add_tension_record("STN-001", record)
```

### Registrar Inspeção Visual

```python
from aoi_lib import InspectionRecord

record = InspectionRecord.from_inspection_result(
    result=resultado_inspecao,  # Dicionário do stencil_inspector
    gerber_file="projeto.gbr",
    recipe_name="Receita A",
    operator="Operador 1",
    report_path="reports/inspecao_001.pdf"
)

db.add_inspection_record("STN-001", record)
```

### Consultas Avançadas

```python
# Histórico combinado
historico = db.get_combined_history("STN-001", limit=50)
for item in historico:
    print(f"{item['type']}: {item['record'].result}")

# Estatísticas de inspeção
stats = db.get_inspection_stats("STN-001")
print(f"Taxa de aprovação: {stats['pass_rate']:.1f}%")

# Consulta por período
registros = db.get_tension_records_by_period(
    start_date="2024-12-01T00:00:00",
    end_date="2024-12-31T23:59:59"
)

# Estatísticas gerais do banco
db_stats = db.get_database_stats()
print(f"Total de stencils: {db_stats['total_stencils']}")
```

### Backup

```python
# Backup automático
backup_path = db.backup_database()
print(f"Backup criado: {backup_path}")

# Backup com caminho específico
db.backup_database("C:/backups/stencils_backup.db")
```

---

## 🖥️ Usando a UI de Histórico Completo

O novo diálogo `StencilFullHistoryDialog` oferece visualização em abas:

```python
from aoi_lib.stencil_tracker_ui import StencilFullHistoryDialog

# Abrir diálogo
dialog = StencilFullHistoryDialog(tracker, "STN-001", parent=self)
dialog.exec()
```

**Abas disponíveis:**

1. **📊 Timeline** - Histórico combinado em ordem cronológica
2. **📐 Medições de Tensão** - Histórico + análise de tendência
3. **🔍 Inspeções Visuais** - Histórico + estatísticas + acesso a relatórios

---

## 📁 Estrutura de Arquivos

```
data/
├── stencils/              # Dados JSON (legado)
│   └── {codigo}/
│       ├── info.json
│       └── history/
│           ├── *_tension.json
│           └── *_inspection.json
│
└── stencils.db            # Banco SQLite (novo)

aoi_lib/
├── stencil_tracker.py     # Modelos + persistência JSON
├── stencil_database.py    # Persistência SQLite
└── stencil_tracker_ui.py  # Widgets PyQt6
```

---

## ⚠️ Notas Importantes

1. **Compatibilidade**: Ambos os sistemas (JSON e SQLite) podem coexistir
2. **Migração**: A migração não remove os dados JSON originais
3. **Backup**: Antes de migrar, os dados JSON são mantidos como backup
4. **Performance**: SQLite é recomendado para mais de 50 stencils

---

## 🎯 Checklist de Migração

- [ ] Fazer backup da pasta `data/stencils/`
- [ ] Executar migração: `migrate_json_to_sqlite()`
- [ ] Verificar estatísticas da migração
- [ ] Testar consultas no banco SQLite
- [ ] Atualizar código para usar `StencilDatabase` em vez de `StencilTracker`
- [ ] (Opcional) Manter JSON como backup ou remover após validação
