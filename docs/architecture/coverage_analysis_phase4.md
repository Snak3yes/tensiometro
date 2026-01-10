# Análise de Cobertura de Testes (Meta 95%)

**Data:** 10/01/2026

## Status Atual (baseado na Fase 2)
Cobertura Global: ~10.68%

## Módulos Críticos com Baixa Cobertura

### 1. `aoi_lib/aoi_controller.py` (16%)
- **Função:** Orquestrador principal.
- **Risco:** Alto. Lógica de integração entre PLC e Câmera.
- **Estratégia:** Criar testes com mocks para PLC e Câmera para simular sequências de inspeção.

### 2. `aoi_lib/plc_axis_controller.py` (12%)
- **Função:** Driver de comunicação Modbus.
- **Risco:** Alto. Controle de movimento físico.
- **Estratégia:** Mockar `pymodbus.client` para simular respostas do CLP sem hardware real. Cobrir tratativa de erros e timeouts.

### 3. `aoi_lib/camera_controller.py` (7%)
- **Função:** Captura de imagem.
- **Risco:** Médio. Dependência de hardware/OpenCV.
- **Estratégia:** Mockar `cv2.VideoCapture` ou a interface de câmera subjacente.

### 4. `aoi_lib/stencil_tracker.py` (31%)
- **Função:** Lógica de negócio de rastreabilidade.
- **Risco:** Médio.
- **Estratégia:** Testes unitários puros (sem mocks complexos) para cálculos e lógica de estado.

## Plano de Ação
1. Focar em `aoi_controller` e `plc_axis_controller` primeiro (já no plano).
2. Adicionar testes para `stencil_tracker` se a cobertura global ainda estiver baixa.
