# 🎯 Roadmap de Refatoração - Próximos Passos

## Status Atual (pós-Sessions 13-16)

### Controllers Criados
1. ConnectionManagerController (286 linhas) ✅
2. TensionMeasurementController (224 linhas) ✅
3. DialogManagerController (172 linhas) ✅
4. FileIOController (294 linhas) ⚠️ PARCIAL

### Linhas do main_window
- **Início:** 4.285
- **Após Session 12:** 2.532 (-40.9%)
- **Após Session 13:** 2.580 (+48)
- **Após Session 14:** 2.609 (+29)
- **Após Session 15:** 2.713 (+104)
- **Meta Sessão 16:** ~2.600 (-100 estimado)

## Session 16 - FileIOController (INCOMPLETA)

### ✅ Criado
- Arquivo: `consumo_lib/controllers/file_io_controller.py` (294 linhas)
- 4 métodos: load_gcode, save_gcode, save_program, load_program
- 9 signals para notificação

### ⚠️ Pendente
- [ ] Adicionar ao __init__.py dos controllers ✅ FEITO
- [ ] Adicionar import no main_window ✅ FEITO
- [ ] Criar instância no __init__ ✅ FEITO
- [ ] Substituir load_gcode() por delegate
- [ ] Substituir save_gcode() por delegate
- [ ] Substituir save_program() por delegate
- [ ] Substituir load_program() por delegate
- [ ] Validar sintaxe
- [ ] Testar aplicação

### Como Completar
```python
# 1. Substituir load_gcode (linha 1885)
def load_gcode(self):
    if self.file_io_controller is not None:
        self.file_io_controller.load_gcode()
    else:
        # código original como fallback

# 2. Repetir para save_gcode, save_program, load_program
```

## Sessions Futuras (17-19+)

### Session 17 - PositionManagerController (~100 linhas)
**Métodos:**
- update_position_display()
- add_current_position()
- remove_position()
- on_position_selected()
- Handlers relacionados (8-10 handlers)

### Session 18 - InspectionWorkflowController (~120 linhas)
**Métodos:**
- _on_inspection_requested()
- _on_inspection_completed()
- _on_inspection_failed()
- _on_inspection_step_changed()
- _on_inspection_progress()
- E mais 6-8 handlers

### Session 19 - RecipeManagerController (~80 linhas)
**Métodos:**
- show_recipe_manager()
- show_new_recipe_dialog()
- apply_recipe_to_capture()
- apply_recipe_to_tension()
- Handlers de recipe

## Estimativa de Redução

| Sessão | Linhas Organizadas | Redução main_window |
|--------|-------------------|---------------------|
| 16 | 294 | ~100 |
| 17 | 100 | ~80 |
| 18 | 120 | ~100 |
| 19 | 80 | ~60 |
| **Total** | **594** | **~340** |

**Resultado esperado após Session 19:**
- main_window: 2.713 → ~2.373 linhas
- Redução total: 4.285 → 2.373 (-44.6%)

## Meta Final: < 1.500 linhas

Para atingir < 1.500 linhas, seriam necessárias:
- **Sessões adicionais:** 20-22
- **Redução adicional:** ~900 linhas
- **Controllers extras:** 5-7

**Recomendação:** Continuar até atingir ~2.000 linhas, então reavaliar.

## Instruções para Continuar

1. Completar Session 16 (FileIOController integration)
2. Implementar Session 17 (PositionManagerController)
3. Implementar Session 18 (InspectionWorkflowController)
4. Implementar Session 19 (RecipeManagerController)
5. Validar e testar após cada sessão
6. Documentar cada sessão completamente

## Arquivos de Referência

- `REFACTORING_SESSION_12_2026-01-05.md`
- `REFACTORING_SESSION_13_2026-01-05.md`
- `REFACTORING_SESSION_14_2026-01-05.md`
- `REFACTORING_SESSION_15_2026-01-05.md`
- `REFACTORING_ROADMAP_2026-01-05.md`
- `ROADMAP_CONTINUACAO.md` (este arquivo)
