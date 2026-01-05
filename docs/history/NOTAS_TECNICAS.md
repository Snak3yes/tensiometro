# 📋 Notas Técnicas de Desenvolvimento

> **Uso interno** - Documento para equipe de desenvolvimento
> **Última atualização:** 10/12/2024

---

## 🔄 Reutilização de Código - Aplicação ADESIVADORA

A aplicação ADESIVADORA contém módulos que foram/serão adaptados para o projeto do Tensiômetro.

### Módulos Reutilizados

| Módulo Original | Novo Módulo | Descrição |
|-----------------|-------------|-----------|
| `fiducial_config_widget.py` | `aoi_lib/fiducial_alignment.py` | Lógica de template matching |
| `helpers.py` (read_fiducials) | `aoi_lib/fiducial_alignment.py` | Cálculo de offset em pixels |
| `sequence_control.py` | `aoi_lib/fiducial_alignment_widget.py` | UI de configuração |

### Módulos com Potencial (Não Prioritários)

| Módulo | Funcionalidade | Observação |
|--------|----------------|------------|
| `inspection_logger.py` | Geração de logs JSON + HTTP | Útil para relatórios |
| `inspection_engine.py` | Engine de inspeção visual | Adaptar para máscaras Gerber |
| `adhesive_program_manager.py` | Gerenciamento de pastas | Estrutura de histórico |
| ~~`barcode_scanner.py`~~ | ~~Leitura de barcode~~ | **NÃO USAR** - Stencil usa entrada manual |

### Diferenças Importantes

**Barcode Scanner:**
- ADESIVADORA: Leitura automática via câmera (código na placa)
- Tensiômetro: Entrada manual (código do stencil fora do alcance da câmera)

**Fiduciais:**
- ADESIVADORA: Correção de offset X/Y para aplicação de dots
- Tensiômetro: Transformação completa (translação + rotação + escala) para alinhar Gerber com imagem

---

## 📁 Estrutura de Arquivos

### Módulos Principais (`aoi_lib/`)

```
aoi_lib/
├── plc_axis_controller.py    # Controle CNC via Modbus TCP
├── aoi_controller.py         # Controlador principal
├── camera_controller.py      # Controle de câmera OpenCV
├── config_manager.py         # Configurações JSON
├── stencil_tension.py        # Medição de tensão (TensiometerSerialManager)
├── position_manager.py       # Posições de inspeção
├── gcode_manager.py          # Parser G-CODE
├── fiducial_alignment.py     # NOVO - Alinhamento de fiduciais
└── fiducial_alignment_widget.py  # NOVO - UI de alinhamento
```

### Classes Principais

| Classe | Arquivo | Responsabilidade |
|--------|---------|------------------|
| `AOIControllerApp` | consumo_lib.py | Janela principal PyQt6 |
| `CNCAOIController` | aoi_controller.py | Controlador integrando CNC + câmera |
| `PLCAxisController` | plc_axis_controller.py | Comunicação Modbus com CLP |
| `TensiometerSerialManager` | stencil_tension.py | Comunicação serial com tensiômetro |
| `TensionMeasurementThread` | stencil_tension.py | Thread de medição |
| `Recipe` | recipe_manager.py | Dados de receita |
| `RecipeManager` | recipe_manager.py | CRUD de receitas |
| `TensionAcceptance` | recipe_manager.py | Critérios OK/NOK |
| `FiducialAligner` | fiducial_alignment.py | Core de alinhamento com fiduciais |
| `FiducialTemplate` | fiducial_alignment.py | Template de fiducial capturado |
| `AlignmentTransform` | fiducial_alignment.py | Transformação calculada |
| `FiducialAlignmentWidget` | fiducial_alignment_widget.py | UI de alinhamento interativo |

---

## 🔧 Configurações Técnicas

### CLP Delta (Modbus TCP)
- **Porta:** 502
- **Endereços:** Ver documentação de endereços do ladder
- **Timeout:** 1 segundo

### Tensiômetro AS-120N
- **Baudrate:** 2400
- **Databits:** 8
- **Stopbits:** 1
- **Parity:** None
- **Frame:** 9 bytes

### Câmera
- **Backend:** OpenCV (cv2.VideoCapture)
- **Resolução:** Configurável
- **FPS:** ~30 (depende da câmera)

---

## 📝 Tarefas Pendentes Detalhadas

### Fase 6 - Alinhamento de Fiduciais (restante ~20%)
- [ ] Integrar com parser Gerber para identificar fiduciais no arquivo
- [ ] Testar workflow completo: captura → alinhamento → preview
- [ ] Adicionar persistência da transformação na receita

### Fase 7 - Rastreabilidade
- [ ] Criar modelo `Stencil` (código, receita, data criação, status)
- [ ] Criar `StencilTracker` para gerenciar histórico
- [ ] UI de seleção de stencil (campo de entrada manual de código)
- [ ] Armazenamento SQLite ou JSON por stencil

### Fase 8 - Relatórios
- [ ] Adaptar `inspection_logger.py` para logs de medição
- [ ] Gerar PDF com heatmap de tensão
- [ ] Gerar histórico consolidado por stencil

### Fase 9 - Inspeção Visual
- [ ] Finalizar parser Gerber (em `testes_gerber/gerber_viewer/`)
- [ ] Implementar geração de mosaico (stitching)
- [ ] Integrar alinhamento de fiduciais
- [ ] Adaptar `inspection_engine.py` para análise de aberturas
