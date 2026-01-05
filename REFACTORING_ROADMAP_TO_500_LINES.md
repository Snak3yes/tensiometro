# REFACTORING ROADMAP - META: 500 LINHAS

**Data:** 2026-01-05
**Status Atual:** 1.359 linhas
**Meta:** ~500 linhas
**Redução Necessária:** ~859 linhas (-63.2%)

## 📊 Situação Atual

### Análise do main_window.py (1.359 linhas)

| Seção | Linhas | % do Total |
|-------|--------|------------|
| Imports e constantes | ~116 | 8.5% |
| `__init__` | ~307 | 22.6% |
| `setup_ui()` | ~222 | 16.3% |
| `setup_menu()` | ~13 | 1.0% |
| Métodos de delegação (show_*) | ~54 | 4.0% |
| Métodos de conexão (CNC/Camera) | ~130 | 9.6% |
| Métodos de sequência | ~150 | 11.0% |
| Métodos de posição | ~80 | 5.9% |
| Métodos de G-code | ~60 | 4.4% |
| Outros métodos | ~227 | 16.7% |

### Principais Blocos Identificados

1. **`setup_ui()`** - 222 linhas 🔴 MAIOR BLOCO
2. **`__init__`** - 307 linhas 🔴 SEGUNDO MAIOR
3. Métodos de conexão - 130 linhas
4. Métodos de sequência - 150 linhas
5. Métodos de posição - 80 linhas
6. Métodos de G-code - 60 linhas

## 🎯 Estratégia de Refatoração

### FASE 5: UIBuilder (PRIORIDADE ALTA)
**Objetivo:** Extrair `setup_ui()` para classe dedicada
**Impacto estimado:** -200 a -220 linhas

**O que será movido:**
- Criação de widgets de conexão (PLC, CNC, Camera)
- Criação de splitter e painéis
- Criação de abas e widgets especializados
- Configuração de layouts

**Arquivo novo:** `consumo_lib/ui_builders.py`
- Classe `MainUIBuilder`
- Método `build_ui(main_window)` → retorna widgets criados

**Benefício:** `setup_ui()` reduzido de 222 → ~20 linhas

### FASE 6: ConnectionManager (PRIORIDADE ALTA)
**Objetivo:** Centralizar lógica de conexão (CNC/Camera)
**Impacto estimado:** -120 a -150 linhas

**O que será movido:**
- `connect_cnc()` - ~90 linhas
- `connect_camera()` - ~15 linhas
- `test_camera()` - ~10 linhas
- `refresh_ports()` - ~10 linhas
- `_apply_plc_ui_settings()` - ~15 linhas

**Arquivo novo:** `consumo_lib/managers/connection_manager.py` (já existe, expandido)
- Métodos de conexão já existem
- Adicionar lógica de GRBL/PLC que está no main_window

**Benefício:** Remove ~130 linhas de lógica de conexão do main_window

### FASE 7: SequenceRunner (PRIORIDADE MÉDIA)
**Objetivo:** Extrair lógica de execução de sequências
**Impacto estimado:** -100 a -130 linhas

**O que será movido:**
- `run_sequence()` - ~40 linhas
- `on_sequence_image_captured()` - ~20 linhas
- `on_sequence_completed()` - ~10 linhas
- `on_sequence_error()` - ~10 linhas
- `stop_sequence()` - ~10 linhas
- `create_sequence_from_registry()` - ~50 linhas

**Arquivo novo:** `consumo_lib/services/sequence_runner.py`
- Classe `SequenceExecutionService`
- Gerencia toda a lógica de execução de sequências

**Benefício:** Remove ~150 linhas de lógica de sequência

### FASE 8: PositionHelper (PRIORIDADE MÉDIA)
**Objetivo:** Extrair métodos auxiliares de posição
**Impacto estimado:** -70 a -90 linhas

**O que será movido:**
- `update_position_display()` - ~20 linhas
- `add_current_position()` - ~10 linhas
- `remove_position()` - ~10 linhas
- `on_position_selected()` - ~10 linhas
- `on_image_captured()` - ~20 linhas

**Arquivo novo:** `consumo_lib/helpers/position_helper.py`
- Classe `PositionHelper`
- Métodos auxiliares para gerenciamento de posições

**Benefício:** Remove ~80 linhas de lógica de posição

### FASE 9: GCodeManager (PRIORIDADE BAIXA)
**Objetivo:** Mover lógica de G-code para manager dedicado
**Impacto estimado:** -50 a -60 linhas

**O que será movido:**
- `save_gcode()` - ~30 linhas
- `load_gcode()` - ~20 linhas
- `save_program()` - ~10 linhas
- `load_program()` - ~10 linhas

**Arquivo existente:** `aoi_lib/gcode_manager.py` (expandido)
- Já existe GCodeManager
- Mover métodos do main_window para lá

**Benefício:** Remove ~60 linhas de lógica de G-code

### FASE 10: Micro-otimizações (PRIORIDADE BAIXA)
**Objetivo:** Remover/mover métodos pequenos restantes
**Impacto estimado:** -50 a -80 linhas

**O que será movido:**
- Métodos stub de delegação (show_*) para um mixins
- Métodos apply_recipe_* (agora redundantes)
- Outros métodos pequenos

**Benefício:** Limpeza final dos métodos restantes

## 📊 Projeção de Redução por Fase

| Fase | Handler | Redução Est. | Acumulado |
|------|---------|--------------|-----------|
| FASE 5 | UIBuilder | -210 | 1.359 → 1.149 |
| FASE 6 | ConnectionManager | -135 | 1.149 → 1.014 |
| FASE 7 | SequenceRunner | -130 | 1.014 → 884 |
| FASE 8 | PositionHelper | -85 | 884 → 799 |
| FASE 9 | GCodeManager | -55 | 799 → 744 |
| FASE 10 | Micro-otimizações | -70 | 744 → **674** |

**Resultado estimado:** 1.359 → 674 linhas (-685 linhas, -50.4%)

**Para atingir 500 linhas:** Será necessário refatorar também `__init__` (-174 linhas extras)

## 🚀 Estratégia Adicional para __init__

### Opção A: Extrair SetupCoordinator
**Objetivo:** Mover lógica de criação de controllers para coordinator
**Impacto:** -150 a -200 linhas

```python
class SetupCoordinator:
    """Coordena criação de todos os controllers e managers."""

    def __init__(self, main_window, controller, config):
        self.main_window = main_window
        self.controller = controller
        self.config = config

    def create_all_managers(self):
        """Cria todos os managers (recipe, stencil, report, inspection)."""
        pass

    def create_all_coordinators(self):
        """Cria todos os coordinators (connection, inspection, tension)."""
        pass

    def create_all_controllers(self):
        """Cria todos os controllers."""
        pass
```

### Opção B: Dividir __init__ em métodos privados
**Objetivo:** Organizar __init__ em métodos menores
**Impacto:** Mantém linhas, mas melhora organização

```python
def __init__(self):
    self._init_config()
    self._init_controllers()
    self._init_managers()
    self._init_coordinators()
    self._init_handlers()
    self._setup_ui()
```

## 🎯 Plano Recomendado (Meta: 500 linhas)

### SESSÃO 23: FASE 5 - UIBuilder
- Criar `consumo_lib/ui_builders.py`
- Extrair `setup_ui()` (222 linhas)
- Reduzir para ~20 linhas

### SESSÃO 24: FASE 6 - ConnectionManager
- Expandir `consumo_lib/managers/connection_manager.py`
- Mover lógica de conexão (130 linhas)

### SESSÃO 25: FASE 7 - SequenceRunner
- Criar `consumo_lib/services/sequence_runner.py`
- Mover lógica de sequência (150 linhas)

### SESSÃO 26: FASE 8 - PositionHelper
- Criar `consumo_lib/helpers/position_helper.py`
- Mover lógica de posição (80 linhas)

### SESSÃO 27: FASE 9+10 - Finalização
- Mover G-code (60 linhas)
- Micro-otimizações (70 linhas)
- Refatorar __init__ (SetupCoordinator)

## 📈 Progresso Esperado

```
ATUAL:        1.359 linhas
Após FASE 5:  ~1.149 linhas (-210)
Após FASE 6:  ~1.014 linhas (-135)
Após FASE 7:  ~884 linhas (-130)
Após FASE 8:  ~799 linhas (-85)
Após FASE 9:  ~744 linhas (-55)
Após FASE 10: ~674 linhas (-70)
Após __init__: ~500-550 linhas (SetupCoordinator)

META: ~500 linhas ✅
```

## 🎉 Próximos Passos

1. ✅ **Iniciar FASE 5** - Criar UIBuilder
2. Continuar com FASES 6-10 em ordem
3. Após FASE 10, refatorar __init__ com SetupCoordinator
4. Validar aplicação após cada fase
5. Atingir meta de ~500 linhas!

---

**Data:** 2026-01-05
**Status:** 📋 PLANEJAMENTO COMPLETO
**Próxima Ação:** Iniciar FASE 5 - UIBuilder
