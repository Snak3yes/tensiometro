# Environment

## Sistema

- Shell usado: PowerShell
- Data de referencia: 2026-06-17
- Timezone: America/Manaus
- Repositorio: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tensiometro\tensiometro`
- Branch atual: `frobert/ajuste_rotina_medicao`

## Python

- Ambiente virtual local: `.venv/`
- Comando Python usado nas validacoes recentes: `python`
- PyInstaller disponivel via `python -m PyInstaller`.
- `pyinstaller.exe` direto falhou no build de 2026-06-17; usar modulo Python como fallback.

## GSD

- Comando global: `gsd`
- Versao: `2.82.0`
- Runtime canonico do GSD 2 no projeto: `.gsd/`
- Snapshot humano legado solicitado: `.planning/`

## Configuracao de integracao observada

- `integration.enabled`: `true`
- `integration.endpoint_url`: `http://147.1.0.85:3075/sfcs-print/stencil/stencil_tensiometro`
- `integration.timeout_sec`: `10.0`
- `integration.line_name`: `IMC4-LM03`
- Comportamento atual do payload: `nmlinha` deve ser enviado como `null`, independentemente de `integration.line_name`.

## Configuracao de consulta SFCS

- `sfcs_stencil_lookup.enabled`: `true`
- `sfcs_stencil_lookup.endpoint_url`: `http://147.1.0.100:3075/sfcs-print/stencil/{codigo_barras}`
- `sfcs_stencil_lookup.timeout_sec`: `10.0`
- `sfcs_stencil_lookup.grid_pattern_map.3x3`: `Teste1_V14_V5`

## Build externo atual

- Pacote final: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tensiometro\tensiometro_build_20260617_config_atual`
- Executavel: `Tensiometro.exe`
- Saida criada fora do worktree, conforme regra do projeto.
