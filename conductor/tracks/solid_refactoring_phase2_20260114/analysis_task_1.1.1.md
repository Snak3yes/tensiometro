# Análise: GerberMacroViewer (mainwindow.py)

**Data:** 2026-01-14
**Tarefa:** 1.1.1 - Análise do arquivo atual
**Arquivo:** `aoi_lib/gerber_core/gui/mainwindow.py`
**Linhas:** 1,384

## Resumo Executivo

A classe `GerberMacroViewer` viola significativamente o **Single Responsibility Principle (SRP)**, misturando múltiplas responsabilidades que deveriam estar em classes separadas.

## Estrutura do Arquivo

### Classes Identificadas
1. **WidthHeightDialog** (linhas 38-259) - 221 linhas
   - Dialog auxiliar para edição de dimensões
   - ✅ **OK** - Responsabilidade única (UI)

2. **GerberMacroViewer** (linhas 261-1384) - 1,123 linhas
   - ❌ **CRÍTICO** - Múltiplas responsabilidades misturadas

## Responsabilidades Identificadas

### 1. **UI/Interface** (12 métodos)
```python
- _build_ui()                    # Constrói interface
- on_new_project()               # Criar projeto
- on_import_gbr()                # Importar Gerber
- on_save(), on_save_as()        # Salvar projeto
- on_export_gbr(), on_export_dxf()  # Exportar arquivos
- on_export_png()                # Exportar imagem
- on_reset_view()                # Resetar visualização
- on_choose_aperture_color()     # Configurar cores
- on_choose_background_color()
- on_choose_selection_color()
- _feature_not_implemented()     # Placeholder
```

### 2. **Lógica de Negócio** (7 métodos)
```python
- on_edit_object()               # Edição individual (189 linhas)
- on_edit_many_objects()         # Edição em grupo (255 linhas)
- on_delete_object()             # Exclusão
- on_delete_many_objects()       # Exclusão em grupo
- _move_object()                 # Movimentação
- _move_objects()                # Movimentação em grupo
- on_render_full_layer()         # Renderização (12+ complexidade)
```

### 3. **Manipulação de Dados** (8 métodos)
```python
- on_open_file()                 # Parsing de arquivos (10+ complexidade)
- _clear_preview()               # Limpeza de estado
# + 5 atributos de estado:
- self.gerber_lines
- self.gerber_cfg
- self.macros
- self.apertures_by_dcode
- self._full_layer_objects
- self._full_layer_polys_mm
```

## Complexidade dos Métodos Críticos

| Método | Complexidade | Linhas | Problema |
|--------|-------------|--------|----------|
| `on_edit_many_objects()` | **46** | 255 | if/elif chain por tipo de objeto |
| `on_edit_object()` | **27** | 189 | if/elif chain por tipo de objeto |
| `on_render_full_layer()` | 12 | ~100 | Múltiplos try/catch, validações |
| `on_open_file()` | 10 | ~80 | Leitura, parsing, validação |

## Violações SOLID Identificadas

### ❌ SRP (Single Responsibility Principle)
- **Violação Crítica:** 1 classe com 3 responsabilidades principais
- **Impacto:** Dificulta testes, manutenção e extensão

### ❌ OCP (Open/Closed Principle)
- **Violação Alta:** `on_edit_many_objects()` tem 46 de complexidade
- **Problema:** Adicionar novo tipo de objeto requer modificar método

### ❌ ISP (Interface Segregation Principle)
- **Violação Média:** 27 métodos públicos (muitos para clientes)
- **Problema:** Clients dependem de métodos que não usam

## Plano de Refatoração Proposto

### Fase 1: Extrair Model (Dados)
**Arquivo Novo:** `aoi_lib/gerber_core/models/gerber_model.py`

**Responsabilidades:**
- Armazenar dados (gerber_lines, gerber_cfg, apertures, macros)
- Validar objetos e índices
- Transformações geométricas (escala, translação)
- Métodos: `validate_objects()`, `transform_object()`, `get_statistics()`

**Benefícios:**
- Separação clara de dados
- Testabilidade sem PyQt6
- Reutilização em outros contextos

### Fase 2: Extrair Controller (Lógica)
**Arquivo Novo:** `aoi_lib/gerber_core/controllers/gerber_controller.py`

**Responsabilidades:**
- Orquestrar fluxos (import, export, edit)
- Coordenar Model ↔ View
- Gerenciar transações
- Métodos: `import_gerber()`, `export_gerber()`, `edit_objects()`

**Benefícios:**
- Lógica de negócio testável
- Desacoplamento de UI
- Reutilização de lógica

### Fase 3: Extrair Commands (Ações)
**Arquivo Novo:** `aoi_lib/gerber_core/commands/edit_commands.py`

**Responsabilidades:**
- Comandos específicos por tipo
- Undo/Redo se aplicável
- Padrão Command

**Classes:**
```python
class EditObjectCommand(ABC):
    @abstractmethod
    def execute(self): pass

class EditCircleCommand(EditObjectCommand):
    def execute(self): # Edita círculo

class EditRectangleCommand(EditObjectCommand):
    def execute(self): # Edita retângulo

# ... outros comandos
```

**Benefícios:**
- Elimina if/elif chains (complexidade 46 → <15)
- Fácil adicionar novos tipos (OCP compliant)
- Undo/Redo nativo

### Fase 4: Refatorar MainWindow (UI)
**Arquivo:** `aoi_lib/gerber_core/gui/mainwindow.py` (manter)

**Responsabilidades (apenas UI):**
- Construir interface
- Tratar eventos de usuário
- Delegar para Controller
- Exibir estado do Model

**Redução Esperada:**
- Linhas: 1,123 → <500
- Métodos públicos: 27 → <15
- Complexidade: 46 → <15

## Métricas Atuais vs. Meta

| Métrica | Atual | Meta | Status |
|---------|-------|------|--------|
| Linhas | 1,384 | <500 | 🔴 Crítico |
| Classes | 2 | 4+ | 🟡 OK |
| Métodos públicos | 27 | <15 | 🔴 Crítico |
| Complexidade máxima | 46 | <15 | 🔴 Crítico |
| Responsabilidades | 3 | 1 | 🔴 Crítico |

## Próximos Passos

1. ✅ **Tarefa 1.1.1** - Análise completa (ESTA TAREFA)
2. ⏳ **Tarefa 1.1.2** - Identificar responsabilidades (já feito nesta análise)
3. ⏳ **Tarefa 1.1.3** - Criar GerberModel
4. ⏳ **Tarefa 1.1.4** - Criar GerberController
5. ⏳ **Tarefa 1.1.5** - Criar GerberCommands
6. ⏳ **Tarefa 1.1.6** - Refatorar MainWindow

## Conclusão

A classe `GerberMacroViewer` necessita de refatoração urgente para atender aos princípios SOLID. A separação de responsabilidades em Model, Controller e Commands irá:

- ✅ Reduzir complexidade de 46 → <15
- ✅ Reduzir tamanho de 1,384 → <500 linhas
- ✅ Aumentar testabilidade (testes sem PyQt6)
- ✅ Facilitar manutenção e extensão
- ✅ Atender SRP, OCP e ISP

---

**Status da Tarefa 1.1.1:** ✅ COMPLETA
**Próxima Tarefa:** 1.1.2 - Já está implicitamente completa nesta análise
