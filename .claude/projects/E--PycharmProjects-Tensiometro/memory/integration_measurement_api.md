---
name: integration_measurement_api
description: Estado atual da integracao SFCS, simulacoes de medicao, configuracoes ADMIN e build
type: project
---

# Integracao SFCS e Medicao

## Endpoints atuais

- Consulta de stencil: `http://147.1.0.100:3075/sfcs-print/stencil/{codigo_barras}`
- Envio de resultado de tensao: `http://147.1.0.85:3075/sfcs-print/stencil/stencil_tensiometro`
- Consulta DRT Digiboard: `http://147.1.0.85:3075/sfcs-print/tbusuario/consultar/matricula/{drt}`

## Configuracao pela interface

- `Sistema > Endpoint de Consulta de Stencil...`: altera `sfcs_stencil_lookup.endpoint_url`.
- A consulta de stencil nao tem checkbox de ativar/desativar e permanece sempre ativa.
- O servico ignora configuracao legada `sfcs_stencil_lookup.enabled=false`.
- `Sistema > Endpoint da API de Tensao...`: altera `integration.endpoint_url` e permite ativar/desativar o envio final.

## Codigo simulado

- Codigo: `32B01A642723416`
- Consulta em `147.1.0.100`: OK
- `idstencil`: `9`
- Grid: `3x3`
- Padrao local: `Teste1_V14_V5`
- Medicao simulada: 9 pontos aprovados
- Envio real para homologacao `147.1.0.85`: HTTP 404 na rota configurada
- Usuario informou depois que o envio pelo servidor `147.1.0.100` funcionou normalmente
- Simulacao com envio desabilitado: concluiu sem POST final

## Build atual

- Pacote: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tensiometro\tensiometro_build_20260617_config_atual`
- Executavel: `Tensiometro.exe`
- Gerado fora do worktree com `python -m PyInstaller` porque o wrapper `pyinstaller.exe` falhou.
- Mudancas de 2026-06-24 ainda nao tem novo build registrado nesta memoria.
