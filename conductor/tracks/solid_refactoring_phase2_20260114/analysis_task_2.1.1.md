# Análise: stencil_database.py (Task 2.1.1)

**Arquivo:** `aoi_lib/stencil_database.py`
**Linhas:** 915
**Métodos públicos:** 21
**Data:** 2026-01-15
**Status:** Análise Completa

---

## 1. Visão Geral

`StencilDatabase` é uma classe monolítica que gerencia toda a persistência SQLite do sistema, incluindo:
- CRUD de stencils
- Histórico de medições de tensão
- Histórico de inspeções visuais
- Análise de tendências
- Migração de dados JSON
- Backup de banco de dados

**Problema principal:** Violação massiva do **Single Responsibility Principle (SRP)** - a classe faz coisas demais.

---

## 2. Categorização de Métodos Públicos

### 2.1 Gerenciamento de Conexão (3 métodos)
- `_get_connection()` - Context manager para conexão SQLite
- `_init_database()` - Inicializa schema e tabelas
- `_get_stencil_id()` - Helper para obter ID interno

### 2.2 CRUD de Stencils (6 métodos)
- `stencil_exists(code: str) -> bool`
- `get_stencil(code: str) -> Optional[Stencil]`
- `create_stencil(code: str, ...) -> Stencil`
- `update_stencil(stencil: Stencil) -> None`
- `list_stencils(status: str = None) -> List[Stencil]`
- `delete_stencil(code: str) -> bool`

### 2.3 Histórico de Tensão (2 métodos)
- `add_tension_record(code: str, record: TensionRecord) -> None`
- `get_tension_history(code: str, limit: int = 50) -> List[TensionRecord]`

### 2.4 Histórico de Inspeção (4 métodos)
- `add_inspection_record(code: str, record: InspectionRecord) -> None`
- `get_inspection_history(code: str, limit: int = 50) -> List[InspectionRecord]`
- `get_combined_history(code: str, limit: int = 50) -> List[Dict]`
- `get_inspection_stats(code: str) -> Dict[str, Any]`

### 2.5 Análise de Tendências (2 métodos)
- `get_trend_analysis(code: str, warning_low: float = None) -> TrendAnalysis`
- `check_degradation_alert(code: str, warning_low: float = None) -> Optional[str]`

### 2.6 Consultas Avançadas (4 métodos)
- `search_stencils(query: str, status: str = None) -> List[Stencil]`
- `get_stencils_by_recipe(recipe_name: str) -> List[Stencil]`
- `get_tension_records_by_period(start_date, end_date, code) -> List[Dict]`
- `get_inspection_records_by_period(start_date, end_date, code) -> List[Dict]`
- `get_database_stats() -> Dict[str, Any]`

### 2.7 Migração e Backup (2 métodos)
- `migrate_from_json(json_dir: str) -> Dict[str, int]`
- `backup_database(backup_path: str = None) -> str`

**Total de métodos públicos:** 21 (confirmado)
**Total de métodos privados:** 3

---

## 3. Análise de Violações SOLID

### 3.1 Single Responsibility Principle (SRP) - ❌ CRÍTICO

**Violação severa:** A classe tem 7 responsabilidades distintas:

1. **Gerenciamento de conexão** (métodos `_get_connection`, `_init_database`)
2. **CRUD de stencils** (6 métodos)
3. **Persistência de tensão** (2 métodos)
4. **Persistência de inspeção** (4 métodos)
5. **Análise de dados** (2 métodos: `get_trend_analysis`, `get_inspection_stats`)
6. **Consultas complexas** (5 métodos: search, filters, stats)
7. **Migração de dados** (2 métodos: `migrate_from_json`, `backup_database`)

**Impacto:**
- Difícil de testar (muitos casos de teste necessários)
- Difícil de manter (mudanças em uma área afetam outras)
- Baixa coesão (métodos não relacionados na mesma classe)

### 3.2 Open/Closed Principle (OCP) - ⚠️ MÉDIO

**Problema:** Para adicionar um novo tipo de registro ou consulta, é necessário modificar a classe `StencilDatabase`.

**Exemplo:**
```python
# Adicionar novo tipo de registro exigiria modificar StencilDatabase
def add_new_record_type(self, code: str, record: NewRecordType):
    # Teria que adicionar método aqui
    pass
```

**Solução:** Repository Pattern permite extensão sem modificação.

### 3.3 Liskov Substitution Principle (LSP) - N/A

Não aplicável - não há herança.

### 3.4 Interface Segregation Principle (ISP) - ⚠️ MÉDIO

**Problema:** 21 métodos públicos é uma interface muito grande. Clientes que precisam apenas de um tipo de operação (ex: apenas tensão) ainda dependem de todos os outros métodos.

**Exemplo:**
```python
# Cliente que só precisa de tensão ainda depende de toda a classe
db = StencilDatabase()  # Depende de 21 métodos
db.add_tension_record(code, record)  # Usa apenas 1 método
```

**Solução:** Interfaces segregadas por domínio:
- `StencilRepository` (6 métodos)
- `TensionRepository` (2 métodos)
- `InspectionRepository` (4 métodos)

### 3.5 Dependency Inversion Principle (DIP) - ❌ ALTO

**Problema:** Depende diretamente de `sqlite3` (implementação concreta), não de uma abstração.

**Código atual:**
```python
import sqlite3  # Dependência concreta

class StencilDatabase:
    def _get_connection(self):
        conn = sqlite3.connect(str(self.db_path))  # Acoplamento forte
```

**Solução:** Injetar abstração de conexão:
```python
from abc import ABC, abstractmethod

class DatabaseConnection(ABC):
    @abstractmethod
    def connect(self):
        pass

class SqliteConnection(DatabaseConnection):
    def connect(self):
        return sqlite3.connect(...)

class StencilDatabase:
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
```

---

## 4. Complexidade Ciclomática

### Métodos com complexidade mais alta:

1. **`migrate_from_json()`** (linhas 765-855)
   - **Complexidade estimada:** 8-10
   - **Motivo:** Múltiplos loops, try/except aninhados, lógica de migração complexa
   - **Linhas:** 91

2. **`get_trend_analysis()`** (linhas 540-593)
   - **Complexidade estimada:** 6-8
   - **Motivo:** Múltiplos if/else, cálculos de tendência, lógica de alerta
   - **Linhas:** 54

3. **`get_tension_records_by_period()`** (linhas 664-696)
   - **Complexidade estimada:** 4-5
   - **Motivo:** Query condicional based em `code` parameter
   - **Linhas:** 33

**Média de complexidade:** ~3-4 por método (aceitável, mas há room para melhorias)

---

## 5. Dependências

### Dependências Externas
```python
import sqlite3      # Banco de dados (implementação concreta)
import json         # Serialização
import logging      # Logging
import shutil       # Backup/cópia de arquivos
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
```

### Dependências Internas
```python
from .stencil_tracker import (
    Stencil,
    TensionRecord,
    InspectionRecord,
    TrendAnalysis
)
```

**Problema:** Acoplamento forte com `sqlite3` (viola DIP).

---

## 6. Oportunidades de Refatoração

### 6.1 Repository Pattern (Principal)

**Separação em 3 repositórios:**

#### 1. StencilRepository
```python
class StencilRepository(ABC):
    """Interface para CRUD de stencils."""

    @abstractmethod
    def exists(self, code: str) -> bool: ...

    @abstractmethod
    def get(self, code: str) -> Optional[Stencil]: ...

    @abstractmethod
    def create(self, code: str, **kwargs) -> Stencil: ...

    @abstractmethod
    def update(self, stencil: Stencil) -> None: ...

    @abstractmethod
    def list(self, status: str = None) -> List[Stencil]: ...

    @abstractmethod
    def delete(self, code: str) -> bool: ...

    @abstractmethod
    def search(self, query: str, status: str = None) -> List[Stencil]: ...

    @abstractmethod
    def get_by_recipe(self, recipe_name: str) -> List[Stencil]: ...
```

#### 2. TensionRepository
```python
class TensionRepository(ABC):
    """Interface para registros de tensão."""

    @abstractmethod
    def add(self, code: str, record: TensionRecord) -> None: ...

    @abstractmethod
    def get_history(self, code: str, limit: int = 50) -> List[TensionRecord]: ...

    @abstractmethod
    def get_by_period(self, start: str, end: str, code: str = None) -> List[Dict]: ...
```

#### 3. InspectionRepository
```python
class InspectionRepository(ABC):
    """Interface para registros de inspeção."""

    @abstractmethod
    def add(self, code: str, record: InspectionRecord) -> None: ...

    @abstractmethod
    def get_history(self, code: str, limit: int = 50) -> List[InspectionRecord]: ...

    @abstractmethod
    def get_by_period(self, start: str, end: str, code: str = None) -> List[Dict]: ...

    @abstractmethod
    def get_stats(self, code: str) -> Dict[str, Any]: ...

    @abstractmethod
    def get_combined_history(self, code: str, limit: int = 50) -> List[Dict]: ...
```

### 6.2 Database Connection Abstraction

```python
class DatabaseConnection(ABC):
    """Abstração para conexão de banco de dados."""

    @abstractmethod
    @contextmanager
    def get_connection(self):
        """Retorna context manager para conexão."""
        pass

    @abstractmethod
    def init_schema(self, schema_sql: str) -> None:
        """Inicializa schema do banco."""
        pass
```

### 6.3 Service Layer para Análise

Mover lógica de análise para services separados:

```python
# aoi_lib/services/trend_analysis_service.py
class TrendAnalysisService:
    """Service para análise de tendências de tensão."""

    def __init__(self, tension_repo: TensionRepository):
        self.tension_repo = tension_repo

    def analyze(self, code: str, warning_low: float = None) -> TrendAnalysis:
        """Analisa tendência de degradação."""
        history = self.tension_repo.get_history(code, limit=20)
        # ... lógica de análise ...
```

### 6.4 Separar Migração

```python
# aoi_lib/database/migrators/json_to_sqlite_migrator.py
class JsonToSqliteMigrator:
    """Migrador de dados JSON para SQLite."""

    def __init__(self, stencil_repo: StencilRepository,
                 tension_repo: TensionRepository,
                 inspection_repo: InspectionRepository):
        self.stencil_repo = stencil_repo
        self.tension_repo = tension_repo
        self.inspection_repo = inspection_repo

    def migrate(self, json_dir: str) -> Dict[str, int]:
        """Executa migração."""
        # ... lógica de migração ...
```

---

## 7. Métricas Atuais vs Meta

| Métrica | Atual | Meta (Fase 2) | Status |
|---------|-------|---------------|--------|
| Linhas de código | 915 | <300 (fachada) | ❌ |
| Métodos públicos | 21 | <10 por classe | ❌ |
| Responsabilidades | 7 | 1 por classe | ❌ |
| Complexidade média | 3-4 | <3 | ⚠️ |
| Acoplamento | Alto (sqlite3) | Baixo (ABC) | ❌ |

---

## 8. Plano de Refatoração Proposto

### Fase 2.1 - Infraestrutura
1. Criar `aoi_lib/database/connection.py` - Abstração de conexão
2. Criar `aoi_lib/database/repositories/` - Interfaces ABC
3. Implementar `SqliteStencilRepository`
4. Implementar `SqliteTensionRepository`
5. Implementar `SqliteInspectionRepository`

### Fase 2.2 - Services
1. Criar `aoi_lib/services/trend_analysis_service.py`
2. Criar `aoi_lib/services/database_stats_service.py`

### Fase 2.3 - Migração
1. Criar `aoi_lib/database/migrators/json_to_sqlite_migrator.py`
2. Mover lógica de `migrate_from_json()` para o migrator

### Fase 2.4 - Fachada (Backward Compatibility)
1. Refatorar `StencilDatabase` para ser uma fachada
2. Delegar chamadas para repositórios apropriados
3. Manter todos os 21 métodos públicos (deprecation warnings)
4. Reduzir de 915 → <300 linhas

---

## 9. Riscos e Mitigações

### Risco 1: Breaking Changes
**Descrição:** Mudar `StencilDatabase` pode quebrar código existente.
**Mitigação:**
- Manter fachada com métodos existentes
- Adicionar deprecation warnings
- Fornecer guia de migração
- Testes de integração abrangentes

### Risco 2: Performance
**Descrição:** Múltiplas conexões podem ser mais lentas.
**Mitigação:**
- Reutilizar mesma conexão via injeção
- Connection pooling se necessário
- Benchmarks antes/depois

### Risco 3: Complexidade de Migração
**Descrição:** Migração de dados JSON pode falhar.
**Mitigação:**
- Testes de migração com dados reais
- Rollback automático em caso de erro
- Validação de dados após migração
- Backup automático antes de migrar

---

## 10. Conclusão

**Problemas identificados:**
1. ❌ **SRP crítico:** 7 responsabilidades em uma classe
2. ❌ **ISP médio:** Interface muito grande (21 métodos)
3. ❌ **DIP alto:** Acoplamento forte com sqlite3
4. ⚠️ **OCP médio:** Difícil estender sem modificar

**Recomendação:** Aplicar Repository Pattern conforme planejado na Fase 2.

**Benefícios esperados:**
- ✅ Separação clara de responsabilidades (SRP)
- ✅ Interfaces pequenas e coesas (ISP)
- ✅ Baixo acoplamento (DIP)
- ✅ Fácil testar (cada repositório independente)
- ✅ Fácil estender (adicionar novos repositórios)

---

*Análise gerada em: 2026-01-15*
*Task: 2.1.1 - Análise do arquivo stencil_database.py*
