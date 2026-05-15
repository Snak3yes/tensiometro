# Environment

## Sistema

- Shell usado: PowerShell
- Data de referencia: 2026-05-14
- Timezone: America/Manaus
- Repositorio: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tenciometro\tensiometro`

## Python

- Ambiente virtual local: `.venv/`
- Comando Python usado nas validacoes: `.\.venv\Scripts\python.exe`

## GSD

- Comando global: `gsd`
- Versao: `2.82.0`
- Runtime canonico do GSD 2 no projeto: `.gsd/`
- Snapshot humano legado solicitado: `.planning/`

## Configuracao de integracao observada

- `integration.enabled`: `true`
- `integration.endpoint_url`: `http://147.1.0.100:3075/sfcs-print/stencil/stencil_tensiometro`
- `integration.timeout_sec`: `10.0`
- `integration.line_name`: `IMC4-LM03`
- Comportamento atual do payload: `nmlinha` deve ser enviado como `null`, independentemente de `integration.line_name`.

