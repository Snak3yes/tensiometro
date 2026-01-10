# Plano da Track: Melhoria da Arquitetura e Implementação de Testes Básicos

## Fase 1: Análise e Setup de Testes [checkpoint: ef1cc29]
- [x] Tarefa: Analisar dependências circulares e acoplamento em `aoi_lib` <!-- c5b623c -->
- [x] Tarefa: Configurar ambiente de teste unificado (pytest + coverage) <!-- b5891dc -->
- [x] Tarefa: Conductor - User Manual Verification 'Fase 1: Análise e Setup de Testes' (Protocol in workflow.md)

## Fase 2: Testes de Bibliotecas Core [checkpoint: 0e0f303]
- [x] Tarefa: Escrever Testes para `aoi_lib/config_manager.py` <!-- 460bd9a -->
- [x] Tarefa: Implementar correções para passar nos testes em `config_manager.py` <!-- 688f9d3 -->
- [x] Tarefa: Escrever Testes para `aoi_lib/stencil_database.py` <!-- 3adc05f -->
- [x] Tarefa: Implementar correções para passar nos testes em `stencil_database.py` <!-- 74df431 -->
- [x] Tarefa: Conductor - User Manual Verification 'Fase 2: Testes de Bibliotecas Core' (Protocol in workflow.md)

## Fase 3: Verificação de Integridade (Smoke Test) [checkpoint: d11620a]
- [x] Tarefa: Executar Smoke Test em `main.py` e validar inicialização <!-- 26456 -->
- [x] Tarefa: Conductor - User Manual Verification 'Fase 3: Verificação de Integridade (Smoke Test)' (Protocol in workflow.md)

## Fase 4: Aumento de Cobertura (Meta: 95%)
- [x] Tarefa: Identificar módulos críticos com baixa cobertura <!-- manual -->
- [x] Tarefa: Criar testes unitários para `aoi_lib/aoi_controller.py` <!-- 1f57d4c -->
- [ ] Tarefa: Criar testes unitários para `aoi_lib/plc_axis_controller.py` (com mocks)
- [ ] Tarefa: Verificar cobertura total e ajustar testes faltantes
- [ ] Tarefa: Conductor - User Manual Verification 'Fase 4: Aumento de Cobertura (Meta: 95%)' (Protocol in workflow.md)