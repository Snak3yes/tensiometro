# State

## Snapshot

- Data: 2026-06-17
- Timezone: America/Manaus
- Diretorio: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tensiometro\tensiometro`
- GSD CLI: `2.82.0`
- GSD runtime local: `.gsd/`
- GSD phase: `pre-planning`
- GSD blockers: nenhum
- GSD next action: manter `.planning/` e memoria sincronizados apos mudancas de integracao/build.

## Estado Git observado

Arquivos modificados:

- `aoi_lib/auth/auth_service.py`
- `aoi_lib/config_manager.py`
- `aoi_lib/report_generator.py`
- `aoi_lib/tensiometer/measurement_thread.py`
- `config/aoi_config.json`
- `consumo_lib/controllers/tension_measurement_controller.py`
- `consumo_lib/dialogs/integration_endpoint_dialog.py`
- `consumo_lib/dialogs/tensiometer_calibration_dialog.py`
- `consumo_lib/main_window.py`
- `tests/unit/test_integration_endpoint_settings.py`
- `tests/unit/test_measurement_thread.py`
- `tests/unit/test_tension_external_send_policy.py`
- `.planning/`
- `.claude/projects/E--PycharmProjects-Tensiometro/memory/`

Arquivos novos:

- `tests/unit/test_report_output_directories.py`
- `tests/unit/test_tensiometer_calibration_flow.py`
- `.claude/projects/E--PycharmProjects-Tensiometro/memory/integration_measurement_api.md`

Resumo do diff antes da atualizacao desta documentacao:

- 12 arquivos rastreados alterados
- 2 arquivos de teste novos

## Validacoes recentes

Build gerado em 2026-06-17:

```powershell
python -m PyInstaller --noconfirm --clean --windowed --name Tensiometro ...
```

Resultado:

- Pacote final: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tensiometro\tensiometro_build_20260617_config_atual`
- Workpath: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tensiometro\_build\tensiometro_build_20260617_config_atual`
- Dist PyInstaller: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tensiometro\_dist\tensiometro_build_20260617_config_atual\Tensiometro`
- Observacao: `tools/build_app.ps1` falhou ao chamar `pyinstaller.exe`; o build equivalente foi gerado com `python -m PyInstaller`.

Configuracao validada no pacote:

- `sfcs_stencil_lookup.endpoint_url`: `http://147.1.0.100:3075/sfcs-print/stencil/{codigo_barras}`
- `integration.endpoint_url`: `http://147.1.0.85:3075/sfcs-print/stencil/stencil_tensiometro`
- `integration.enabled`: `true`

Comandos executados apos as alteracoes de integracao:

```powershell
python -m pytest tests/unit/test_sfcs_stencil_lookup_service.py tests/unit/test_integration_endpoint_settings.py
python -m pytest tests/unit/test_integration_endpoint_settings.py
```

Resultado:

- 10 testes passaram no conjunto lookup/integracao.
- 6 testes passaram no conjunto do dialog de endpoint.

Simulacao operacional:

- Codigo testado: `32B01A642723416`
- Consulta em `147.1.0.100` retornou stencil `idstencil=9`, grid `3x3`, status `DISPONIVEL`.
- Padrao local resolvido: `Teste1_V14_V5`.
- Medicao simulada aprovada com 9 pontos.
- Envio real para `147.1.0.85` retornou HTTP 404 para a rota configurada.
- Simulacao com envio desabilitado em memoria concluiu sem POST final.
