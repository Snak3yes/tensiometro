# Project

## Nome

tensiometro

## Tipo

Aplicacao desktop industrial para medicao de tensao de stencil e inspecao visual.

## Stack principal

- Python 3.13
- PyQt6
- OpenCV
- numpy
- pymodbus
- pyserial
- matplotlib
- reportlab

## Entrada

- `main.py`

## Areas principais

- `aoi_lib/`: dominio, hardware, persistencia, tensiometro, PLC, camera e inspecao.
- `consumo_lib/`: UI, controllers, coordinators, services, factories e dialogs.
- `config/`: configuracoes locais de runtime.
- `tension_routines/`: resultados e payloads de medicao de tensao.
- `.gsd/`: runtime atual do GSD 2.
- `.planning/`: snapshot humano solicitado do estado atual.

## Observacoes operacionais

- Evitar expandir `consumo_lib/main_window.py` sem necessidade.
- Colocar regra de negocio em `aoi_lib/` ou `consumo_lib/services/`.
- Preservar degradacao graciosa quando hardware nao estiver conectado.
- Tratar `config/aoi_config.json` como configuracao local da maquina.
- Para PLC, consultar `MAPA.txt` antes de mexer em enderecos Modbus, registradores, memorias, entradas, saidas, homing ou movimentos.

## Integracao atual

- Consulta de stencil: servidor final `147.1.0.100` por padrao.
- Consulta de stencil: endpoint alteravel por ADMIN em `Sistema > Endpoint de Consulta de Stencil...`.
- Consulta de stencil: sempre ativa; configuracoes legadas `sfcs_stencil_lookup.enabled=false` sao ignoradas pelo servico.
- Envio de resultado de tensao: servidor homologacao `147.1.0.85` no arquivo de configuracao atual.
- Envio de resultado de tensao: endpoint e ativacao/desativacao alteraveis por ADMIN em `Sistema > Endpoint da API de Tensao...`.
- Autenticacao DRT Digiboard: servidor homologacao `147.1.0.85`.
