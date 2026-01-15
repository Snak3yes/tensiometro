# Domínios Identificados: stencil_database.py (Task 2.1.2)

**Arquivo:** `aoi_lib/stencil_database.py`
**Data:** 2026-01-15
**Status:** Domínios identificados e documentados

---

## Visão Geral

Foram identificados **3 domínios principais** que serão separados em repositórios independentes:

1. **Stencil Domain** - Gerenciamento de stencils
2. **Tension Domain** - Medições de tensão superficial
3. **Inspection Domain** - Inspeções visuais de aberturas

Cada domínio terá seu próprio Repository Pattern com interface ABC e implementação SQLite.

---

## 1. Stencil Domain

### Responsabilidade
Gerenciar cadastro e metadados de stencils (dados mestres).

### Entidade Principal
```python
@dataclass
class Stencil:
    code: str                    # Identificador único
    description: str             # Descrição textual
    recipe_name: str             # Receita de produção
    created_at: str              # ISO format timestamp
    last_inspection: str         # ISO format timestamp
    inspection_count: int        # Total de inspeções
    status: str                  # 'active', 'retired', 'warning'
    notes: str                   # Observações
```

### Operações (7 métodos)

#### Métodos CRUD Básicos
1. **`exists(code: str) -> bool`**
   - Verifica se stencil existe no banco
   - SELECT count FROM stencils WHERE code = ?

2. **`get(code: str) -> Optional[Stencil]`**
   - Obtém um stencil pelo código
   - SELECT * FROM stencils WHERE code = ?

3. **`create(code: str, description: str, recipe_name: str) -> Stencil`**
   - Cria novo stencil
   - INSERT INTO stencils (...)
   - Levanta `ValueError` se já existe

4. **`update(stencil: Stencil) -> None`**
   - Atualiza dados de stencil existente
   - UPDATE stencils SET ... WHERE code = ?
   - Levanta `ValueError` se não existe

5. **`delete(code: str) -> bool`**
   - Remove stencil (CASCADE para registros filhos)
   - DELETE FROM stencils WHERE code = ?

#### Métodos de Listagem
6. **`list(status: str = None) -> List[Stencil]`**
   - Lista stencils por status
   - SELECT * FROM stencils WHERE status = ? ORDER BY last_inspection DESC

7. **`search(query: str, status: str = None) -> List[Stencil]`**
   - Busca por código ou descrição (LIKE)
   - SELECT * FROM stencils WHERE code LIKE ? OR description LIKE ?

#### Métodos Adicionais
8. **`get_by_recipe(recipe_name: str) -> List[Stencil]`**
   - Lista stencils por receita
   - SELECT * FROM stencils WHERE recipe_name = ?

### Tabela SQLite
```sql
CREATE TABLE stencils (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    description TEXT DEFAULT '',
    recipe_name TEXT,
    created_at TEXT NOT NULL,
    last_inspection TEXT,
    inspection_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    notes TEXT DEFAULT '',
    updated_at TEXT NOT NULL
);
```

### Interface ABC Proposta
```python
class StencilRepository(ABC):
    """Repository para CRUD de stencils."""

    @abstractmethod
    def exists(self, code: str) -> bool:
        """Verifica se stencil existe."""
        pass

    @abstractmethod
    def get(self, code: str) -> Optional[Stencil]:
        """Obtém stencil pelo código."""
        pass

    @abstractmethod
    def create(self, code: str, description: str = "",
               recipe_name: str = None) -> Stencil:
        """Cria novo stencil."""
        pass

    @abstractmethod
    def update(self, stencil: Stencil) -> None:
        """Atualiza stencil existente."""
        pass

    @abstractmethod
    def delete(self, code: str) -> bool:
        """Remove stencil."""
        pass

    @abstractmethod
    def list(self, status: str = None) -> List[Stencil]:
        """Lista stencils por status."""
        pass

    @abstractmethod
    def search(self, query: str, status: str = None) -> List[Stencil]:
        """Busca stencils por código/descrição."""
        pass

    @abstractmethod
    def get_by_recipe(self, recipe_name: str) -> List[Stencil]:
        """Lista stencils por receita."""
        pass
```

### Arquivos
- **Interface:** `aoi_lib/database/repositories/stencil_repository.py`
- **Implementação:** `aoi_lib/database/repositories/sqlite_stencil_repository.py`

---

## 2. Tension Domain

### Responsabilidade
Gerenciar histórico de medições de tensão superficial dos stencils.

### Entidade Principal
```python
@dataclass
class TensionRecord:
    timestamp: str              # ISO format timestamp
    measurements: List[Dict]    # Grid de medições (NxN)
    average_tension: float      # Média em N/cm
    min_tension: float          # Menor valor
    max_tension: float          # Maior valor
    result: str                 # 'OK', 'WARNING', 'NOK'
    ok_count: int               # Pontos OK
    warning_count: int          # Pontos WARNING
    nok_count: int              # Pontos NOK
    operator: str               # Operador responsável
    recipe_name: str            # Receita usada
```

### Operações (4 métodos)

#### Métodos CRUD
1. **`add(code: str, record: TensionRecord) -> None`**
   - Adiciona registro de tensão
   - INSERT INTO tension_records (...)
   - Atualiza stencils.last_inspection e inspection_count
   - Atualiza stencils.status se result = 'NOK'

2. **`get_history(code: str, limit: int = 50) -> List[TensionRecord]`**
   - Obtém histórico de medições
   - SELECT * FROM tension_records WHERE stencil_id = ? ORDER BY timestamp DESC LIMIT ?

#### Métodos de Consulta
3. **`get_by_period(start_date: str, end_date: str, code: str = None) -> List[Dict]`**
   - Obtém registros por período
   - SELECT tr.*, s.code FROM tension_records tr JOIN stencils s ON ...
   - WHERE tr.timestamp >= ? AND tr.timestamp <= ?

4. **`get_latest(code: str) -> Optional[TensionRecord]`**
   - Obtém medição mais recente
   - SELECT * FROM tension_records WHERE stencil_id = ? ORDER BY timestamp DESC LIMIT 1

### Tabela SQLite
```sql
CREATE TABLE tension_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stencil_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    average_tension REAL DEFAULT 0,
    min_tension REAL DEFAULT 0,
    max_tension REAL DEFAULT 0,
    result TEXT DEFAULT 'OK',
    ok_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,
    nok_count INTEGER DEFAULT 0,
    operator TEXT,
    recipe_name TEXT,
    measurements_json TEXT,
    FOREIGN KEY (stencil_id) REFERENCES stencils(id) ON DELETE CASCADE
);
```

### Interface ABC Proposta
```python
class TensionRepository(ABC):
    """Repository para registros de tensão."""

    @abstractmethod
    def add(self, code: str, record: TensionRecord) -> None:
        """Adiciona registro de tensão."""
        pass

    @abstractmethod
    def get_history(self, code: str, limit: int = 50) -> List[TensionRecord]:
        """Obtém histórico de medições."""
        pass

    @abstractmethod
    def get_by_period(self, start_date: str, end_date: str,
                      code: str = None) -> List[Dict]:
        """Obtém registros por período."""
        pass

    @abstractmethod
    def get_latest(self, code: str) -> Optional[TensionRecord]:
        """Obtém medição mais recente."""
        pass
```

### Arquivos
- **Interface:** `aoi_lib/database/repositories/tension_repository.py`
- **Implementação:** `aoi_lib/database/repositories/sqlite_tension_repository.py`

---

## 3. Inspection Domain

### Responsabilidade
Gerenciar histórico de inspeções visuais de aberturas dos stencils.

### Entidade Principal
```python
@dataclass
class InspectionRecord:
    timestamp: str              # ISO format timestamp
    total_apertures: int        # Total de aberturas inspecionadas
    ok_count: int               # Aberturas OK (>90% limpas)
    partial_count: int          # Aberturas PARCIAL (70-90%)
    blocked_count: int          # Aberturas BLOCKED (<70%)
    result: str                 # 'PASS', 'FAIL'
    pass_rate: float            # Taxa de aprovação (%)
    gerber_file: str            # Arquivo Gerber usado
    operator: str               # Operador responsável
    recipe_name: str            # Receita usada
    report_path: str            # Caminho do PDF gerado
    defects: List[Dict]         # Lista de defeitos encontrados
    notes: str                  # Observações
```

### Operações (5 métodos)

#### Métodos CRUD
1. **`add(code: str, record: InspectionRecord) -> None`**
   - Adiciona registro de inspeção
   - INSERT INTO inspection_records (...)
   - Atualiza stencils.last_inspection e inspection_count
   - Atualiza stencils.status se result = 'FAIL'

2. **`get_history(code: str, limit: int = 50) -> List[InspectionRecord]`**
   - Obtém histórico de inspeções
   - SELECT * FROM inspection_records WHERE stencil_id = ? ORDER BY timestamp DESC LIMIT ?

#### Métodos de Consulta
3. **`get_by_period(start_date: str, end_date: str, code: str = None) -> List[Dict]`**
   - Obtém registros por período
   - SELECT ir.*, s.code FROM inspection_records ir JOIN stencils s ON ...
   - WHERE ir.timestamp >= ? AND ir.timestamp <= ?

4. **`get_stats(code: str) -> Dict[str, Any]`**
   - Calcula estatísticas de inspeção
   - total_inspections, pass_count, fail_count, pass_rate, avg_pass_rate, last_result

5. **`get_combined_history(code: str, limit: int = 50) -> List[Dict]`**
   - Combina tensão + inspeção em timeline única
   - SELECT ... FROM tension_records UNION SELECT ... FROM inspection_records

### Tabela SQLite
```sql
CREATE TABLE inspection_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stencil_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    total_apertures INTEGER DEFAULT 0,
    ok_count INTEGER DEFAULT 0,
    partial_count INTEGER DEFAULT 0,
    blocked_count INTEGER DEFAULT 0,
    result TEXT DEFAULT 'PASS',
    pass_rate REAL DEFAULT 100.0,
    gerber_file TEXT,
    operator TEXT,
    recipe_name TEXT,
    report_path TEXT,
    defects_json TEXT,
    notes TEXT DEFAULT '',
    FOREIGN KEY (stencil_id) REFERENCES stencils(id) ON DELETE CASCADE
);
```

### Interface ABC Proposta
```python
class InspectionRepository(ABC):
    """Repository para registros de inspeção."""

    @abstractmethod
    def add(self, code: str, record: InspectionRecord) -> None:
        """Adiciona registro de inspeção."""
        pass

    @abstractmethod
    def get_history(self, code: str, limit: int = 50) -> List[InspectionRecord]:
        """Obtém histórico de inspeções."""
        pass

    @abstractmethod
    def get_by_period(self, start_date: str, end_date: str,
                      code: str = None) -> List[Dict]:
        """Obtém registros por período."""
        pass

    @abstractmethod
    def get_stats(self, code: str) -> Dict[str, Any]:
        """Calcula estatísticas de inspeção."""
        pass

    @abstractmethod
    def get_combined_history(self, code: str, limit: int = 50) -> List[Dict]:
        """Obtém timeline combinada (tensão + inspeção)."""
        pass
```

### Arquivos
- **Interface:** `aoi_lib/database/repositories/inspection_repository.py`
- **Implementação:** `aoi_lib/database/repositories/sqlite_inspection_repository.py`

---

## 4. Relacionamentos Entre Domínios

### Diagrama ER

```
┌─────────────┐
│  Stencils   │
│             │
│ - id (PK)   │◄──────┐
│ - code      │       │
│ - desc      │       │ 1:N
│ - status    │       │
│ - ...       │       │
└─────────────┘       │
                      │
        ┌─────────────┴─────────────────┐
        │                               │
        │ 1:N                           │ 1:N
        ▼                               ▼
┌─────────────────┐           ┌──────────────────┐
│ tension_records │           │inspection_records│
│                 │           │                  │
│ - id (PK)       │           │ - id (PK)        │
│ - stencil_id FK│           │ - stencil_id FK  │
│ - timestamp     │           │ - timestamp      │
│ - avg_tension   │           │ - result         │
│ - ...           │           │ - ...            │
└─────────────────┘           └──────────────────┘
```

### Chaves Estrangeiras

- **tension_records.stencil_id** → **stencils.id** (ON DELETE CASCADE)
- **inspection_records.stencil_id** → **stencils.id** (ON DELETE CASCADE)

### Integridade Referencial

Ao deletar um stencil:
- Todos os `tension_records` relacionados são deletados automaticamente
- Todos os `inspection_records` relacionados são deletados automaticamente
- Isso é garantido pela cláusula `ON DELETE CASCADE` do SQLite

---

## 5. Serviços Cross-Domain

### TrendAnalysisService
**Responsabilidade:** Analisar tendências de degradação de tensão.

**Dependências:**
- `TensionRepository` (para obter histórico)

**Métodos:**
- `analyze(code: str, warning_low: float = None) -> TrendAnalysis`
- `check_alert(code: str, warning_low: float = None) -> Optional[str]`

**Nota:** Este NÃO é um repositório, é um **service** que usa `TensionRepository`.

### DatabaseStatsService
**Responsabilidade:** Calcular estatísticas gerais do banco.

**Dependências:**
- `StencilRepository` (contagem de stencils)
- `TensionRepository` (contagem de registros)
- `InspectionRepository` (contagem de registros)

**Métodos:**
- `get_stats() -> Dict[str, Any]` - total_stencils, total_tension_records, etc.

---

## 6. Migração e Backup

### JsonToSqliteMigrator
**Responsabilidade:** Migrar dados JSON para SQLite.

**Dependências:**
- `StencilRepository`
- `TensionRepository`
- `InspectionRepository`

**Métodos:**
- `migrate(json_dir: str) -> Dict[str, int]` - retorna contagem de registros migrados

### DatabaseBackupService
**Responsabilidade:** Criar backups do banco SQLite.

**Métodos:**
- `backup(backup_path: str = None) -> str` - retorna caminho do backup criado

---

## 7. Fachada para Backward Compatibility

### StencilDatabase (Refatorado)
**Responsabilidade:** Manter backward compatibility com código existente.

**Estrutura:**
```python
class StencilDatabase:
    """Fachada para backward compatibility."""

    def __init__(self, db_path: str = None):
        # Injeta dependências
        self.connection = SqliteConnection(db_path)
        self.stencil_repo = SqliteStencilRepository(self.connection)
        self.tension_repo = SqliteTensionRepository(self.connection)
        self.inspection_repo = SqliteInspectionRepository(self.connection)

    # Delega métodos para repositórios apropriados
    def stencil_exists(self, code: str) -> bool:
        return self.stencil_repo.exists(code)

    def get_stencil(self, code: str) -> Optional[Stencil]:
        return self.stencil_repo.get(code)

    # ... (todos os 21 métodos públicos originais mantidos)
```

**Benefícios:**
- ✅ Zero breaking changes
- ✅ Código existente continua funcionando
- ✅ Adiciona deprecation warnings suavemente
- ✅ Reduz de 915 → <300 linhas (apenas delegações)

---

## 8. Estrutura de Diretórios Proposta

```
aoi_lib/
├── database/
│   ├── __init__.py
│   ├── connection.py                      # DatabaseConnection (ABC)
│   ├── sqlite_connection.py               # SqliteConnection
│   └── repositories/
│       ├── __init__.py
│       ├── base_repository.py             # Repository base (ABC)
│       ├── stencil_repository.py          # StencilRepository (ABC)
│       ├── tension_repository.py          # TensionRepository (ABC)
│       ├── inspection_repository.py       # InspectionRepository (ABC)
│       ├── sqlite_stencil_repository.py   # SqliteStencilRepository
│       ├── sqlite_tension_repository.py   # SqliteTensionRepository
│       └── sqlite_inspection_repository.py # SqliteInspectionRepository
├── services/
│   ├── trend_analysis_service.py          # TrendAnalysisService
│   └── database_stats_service.py          # DatabaseStatsService
├── migrators/
│   ├── json_to_sqlite_migrator.py         # JsonToSqliteMigrator
│   └── database_backup_service.py         # DatabaseBackupService
└── stencil_database.py                    # FACHADA (backward compat)
```

---

## 9. Próximos Passos

### Task 2.1.3 - Criar DatabaseConnection
- Extrair lógica de conexão SQLite
- Criar abstração `DatabaseConnection` (ABC)
- Implementar `SqliteConnection`

### Task 2.1.4 - Criar Interfaces de Repositórios
- Criar 3 interfaces ABC (Stencil, Tension, Inspection)
- Definir contratos com métodos abstratos
- Documentar responsabilidade de cada repositório

### Task 2.1.5 - Implementar Repositórios Concretos
- Implementar `SqliteStencilRepository` (7 métodos)
- Implementar `SqliteTensionRepository` (4 métodos)
- Implementar `SqliteInspectionRepository` (5 métodos)

### Task 2.1.6 - Criar Migrador
- Extrair lógica de `migrate_from_json()`
- Criar `JsonToSqliteMigrator` (injeta repositórios)
- Implementar validação e rollback

### Task 2.1.7 - Refatorar StencilDatabase
- Transformar em fachada (delegação pura)
- Manter todos os 21 métodos públicos
- Reduzir de 915 → <300 linhas

---

## 10. Conclusão

**Domínios identificados:** 3
- ✅ **Stencil Domain** - CRUD de stencils (7 métodos)
- ✅ **Tension Domain** - Medições de tensão (4 métodos)
- ✅ **Inspection Domain** - Inspeções visuais (5 métodos)

**Total de métodos nos repositórios:** 16 (vs 21 na classe monolítica)

**Redução de responsabilidade:**
- Antes: 1 classe com 7 responsabilidades
- Depois: 3 classes + 2 services + 1 migrator = 6 classes focadas

**Cada classe <10 métodos:** ✅ (meta atingida)

---

*Documentação gerada em: 2026-01-15*
*Task: 2.1.2 - Identificar domínios (Stencil, Tension, Inspection)*
