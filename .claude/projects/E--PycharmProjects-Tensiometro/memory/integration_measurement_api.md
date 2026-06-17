---
name: integration_measurement_api
description: Estado atual da integracao SFCS, simulacoes de medicao e build
type: project
---

# Integracao SFCS e Medicao

## Endpoints atuais

- Consulta de stencil: `http://147.1.0.100:3075/sfcs-print/stencil/{codigo_barras}`
- Envio de resultado de tensao: `http://147.1.0.85:3075/sfcs-print/stencil/stencil_tensiometro`
- Consulta DRT Digiboard: `http://147.1.0.85:3075/sfcs-print/tbusuario/consultar/matricula/{drt}`

## Codigo simulado

- Codigo: `32B01A642723416`
- Consulta em `147.1.0.100`: OK
- `idstencil`: `9`
- Grid: `3x3`
- Padrao local: `Teste1_V14_V5`
- Medicao simulada: 9 pontos aprovados
- Envio real para homologacao: HTTP 404 na rota configurada
- Simulacao com envio desabilitado: concluiu sem POST final

## Build atual

- Pacote: `C:\Users\FelipeRobert-Digiboa\Documents\projetos CTD\Tensiometro\tensiometro_build_20260617_config_atual`
- Executavel: `Tensiometro.exe`
- Gerado fora do worktree com `python -m PyInstaller` porque o wrapper `pyinstaller.exe` falhou.
