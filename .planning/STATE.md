# State

## Snapshot

- Data: 2026-05-14
- Timezone: America/Manaus
- Diretorio: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tenciometro\tensiometro`
- GSD CLI: `2.82.0`
- GSD runtime local: `.gsd/`
- GSD phase: `pre-planning`
- GSD blockers: nenhum
- GSD next action: criar um milestone quando houver especificacao.

## Estado Git observado

Arquivos modificados:

- `.gitignore`
- `AGENTS.md`
- `aoi_lib/config_manager.py`
- `conductor/README.md`
- `conductor/workflow.md`
- `config/aoi_config.json`
- `consumo_lib/controllers/tension_measurement_controller.py`
- `consumo_lib/dialogs/tracking_dialog.py`
- `consumo_lib/handlers/menu_handler.py`
- `consumo_lib/main_window.py`
- `consumo_lib/managers/measurement_pattern_manager.py`
- `consumo_lib/services/__init__.py`
- `consumo_lib/services/tension_external_payload_service.py`
- `consumo_lib/widgets/stencil/identification_widget.py`
- `tests/unit/test_stencil_code_normalization.py`
- `tests/unit/test_stencil_flow.py`
- `tests/unit/test_tension_external_send_policy.py`

Arquivos ou diretorios nao rastreados:

- `.bg-shell/`
- `.gsd/`
- `consumo_lib/services/sfcs_stencil_lookup_service.py`
- `resources/endpoint.png`
- `tests/unit/test_measurement_pattern_grid_resolution.py`
- `tests/unit/test_sfcs_stencil_lookup_service.py`

Resumo do diff rastreado no momento do snapshot:

- 17 arquivos alterados
- 299 insercoes
- 74 remocoes

## Validacoes recentes

Build gerado em 2026-05-15:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\build_app.ps1 -ExeName Tensiometro -PackageName tensiometro_build_20260515 -EntryPoint main.py
```

Resultado:

- Pacote final: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tenciometro\tensiometro_build_20260515`
- Workpath: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tensiometro\_build\tensiometro_build_20260515`
- Dist PyInstaller: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tensiometro\_dist\tensiometro_build_20260515\Tensiometro`

Comando executado apos a alteracao do payload externo:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_stencil_code_normalization.py tests\unit\test_tension_external_send_policy.py -q
```

Resultado:

- 11 testes passaram

Comando executado para validar GSD:

```powershell
gsd headless --output-format json query
```

Resultado:

- Sem blockers
- Estado `pre-planning`
