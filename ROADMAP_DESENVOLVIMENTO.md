# 🎯 Sistema AOI para Inspeção de Stencil

> **Versão:** 0.4  
> **Última atualização:** 10/12/2024  
> **Status:** Em desenvolvimento ativo

---

## 📋 Visão Geral

Sistema de Inspeção Óptica Automatizada (AOI) industrial para:
- **Medição de tensão superficial** de stencils de pasta de solda
- **Inspeção visual automatizada** das aberturas para validação de limpeza
- **Controle CNC** de máquina com eixos X, Y, Z
- **Rastreabilidade individual** de cada stencil físico
- **Análise de tendência** para suporte a decisões de reposição

### Workflow de Operação
```
1. Identificar Stencil → Código de barras lido manualmente pelo operador
2. Carregar Receita   → Sistema carrega configurações do modelo automaticamente
3. Medição de Tensão  → Grid NxN com classificação OK/WARNING/NOK
4. Inspeção Visual    → Mosaico alinhado com Gerber via fiduciais
5. Relatórios         → Histórico individual por stencil
```

---

## 🏗️ Arquitetura do Sistema

| Componente | Tecnologia | Status |
|------------|------------|--------|
| Backend de movimento | PLCAxisController (Modbus TCP) | ✅ Concluído |
| Interface gráfica | PyQt6 | ✅ Concluído |
| Visão computacional | OpenCV | ✅ Concluído |
| Comunicação industrial | pymodbus (porta 502) | ✅ Concluído |
| Controlador | CLP Delta série AS | ✅ Integrado |
| Sistema de Receitas | RecipeManager (JSON) | ✅ Concluído |
| Medição de Tensão | TensiometerSerialManager | ✅ Concluído |
| Alinhamento Fiduciais | FiducialAligner | 🟡 ~80% |
| Rastreabilidade | StencilTracker | 🔴 Pendente |

---

## ✅ Funcionalidades Desenvolvidas

### 🔧 FASE 1: Controle de Movimento CNC
**Status: ✅ Concluído**

Desenvolvimento de driver completo para comunicação com CLP Delta via protocolo Modbus TCP:
- [x] Controle de 3 eixos (X, Y, Z) com movimentação absoluta e relativa
- [x] Sistema de homing (referenciamento) automático
- [x] Limites de segurança (soft limits e hard limits)
- [x] Velocidade variável por tipo de operação
- [x] Conversão automática pulsos ↔ milímetros

**Arquivo:** `aoi_lib/plc_axis_controller.py`

---

### 📹 FASE 2: Sistema de Visão
**Status: ✅ Concluído**

Sistema de captura e processamento de imagem com OpenCV:
- [x] Captura contínua em tempo real (stream de vídeo)
- [x] Preview com crosshair central e grid opcional
- [x] Controle de exposição e foco
- [x] Captura de imagens individuais para análise
- [x] Base para geração de mosaico (stitching)
- [x] **Calibração de Campo de Visão (FOV)** - Diálogo para configurar relação pixel↔mm em diferentes alturas Z
- [x] **Movimento por clique no vídeo** - Clique no preview da câmera move a head para centralizar o ponto
- [x] **Integração na interface** - Menu Ferramentas → Calibração de FOV, checkbox para habilitar clique

**Arquivos:**
- `aoi_lib/camera_controller.py` - Controle de câmera
- `aoi_lib/fov_calibration.py` - Calibração FOV e conversão pixel→pulsos (baseado em ADESIVADORA)
- `consumo_lib.py` - Integração no CameraPreviewWidget e menu

---

### 📊 FASE 3: Sistema de Receitas
**Status: ✅ Concluído**

Sistema de receitas modular para configuração de diferentes modelos de stencil:
- [x] Estrutura de dados `Recipe` com parâmetros completos
- [x] Critérios de aceitação configuráveis (OK/WARNING/NOK)
- [x] Persistência em JSON para fácil backup e versionamento
- [x] Interface de edição visual com preview
- [x] Suporte a múltiplos pontos de medição por receita
- [x] Validação de integridade dos dados

**Classes:** `Recipe`, `RecipeManager`, `TensionAcceptance`

---

### 📐 FASE 4: Medição de Tensão
**Status: ✅ Concluído**

Integração completa com tensiômetro AS-120N via serial RS232:
- [x] Protocolo de comunicação decodificado (9 bytes, 2400 baud)
- [x] Leitura automática de valores de tensão
- [x] Rotina de medição em grid NxN configurável
- [x] Descida controlada do eixo Z para contato com o stencil
- [x] Classificação automática baseada nos critérios da receita
- [x] Execução em thread separada (não bloqueia a interface)

**Classes:** `TensiometerSerialManager`, `TensionMeasurementThread` (`aoi_lib/stencil_tension.py`)

---

### 🖥️ FASE 5: Interface Principal
**Status: ✅ Concluído**

Aplicação desktop desenvolvida em PyQt6:
- [x] Layout modular com abas funcionais
- [x] Painel de controle manual de movimento (jog)
- [x] Visualização de câmera em tempo real
- [x] Indicadores de status de conexão (CLP, câmera, tensiômetro)
- [x] Sistema de logs para diagnóstico
- [x] Persistência de configurações do usuário

**Arquivo:** `consumo_lib.py` (~3600 linhas)

---

### 🎯 FASE 6: Alinhamento de Fiduciais
**Status: 🟡 Em desenvolvimento (~80%)**

Sistema de alinhamento do arquivo Gerber com a imagem real do stencil:
- [x] Captura de templates de fiduciais por clique
- [x] Busca automática por template matching (OpenCV)
- [x] Cálculo de transformação (translação, rotação, escala)
- [x] Interface interativa com zoom, pan e arraste
- [x] Ajuste fino manual da transformação
- [x] Suporte a 2+ pontos de referência
- [ ] Integrar com parser Gerber para identificar fiduciais automaticamente
- [ ] Testar workflow completo integrado

**Arquivos:**
- `aoi_lib/fiducial_alignment.py` - Core de alinhamento
- `aoi_lib/fiducial_alignment_widget.py` - Interface PyQt6

**Notas:** Baseado em funcionalidade da aplicação ADESIVADORA, adaptada para inspeção visual

---

### 🏷️ FASE 7: Rastreabilidade de Stencils
**Status: ✅ Concluído (~95%)**

Controle individualizado de cada stencil físico:
- [x] Modelo de dados `Stencil` (código, descrição, receita, datas, status)
- [x] Modelo de dados `TensionRecord` para histórico de medições
- [x] `StencilTracker` - CRUD de stencils + persistência JSON
- [x] Entrada de código de barras (manual ou leitor USB)
- [x] Histórico de medições de tensão por stencil
- [x] Análise de tendência (média móvel, variação %)
- [x] Alertas de degradação automáticos
- [x] Widgets de UI: Identificação, Histórico, Edição, Gerenciamento
- [x] Aba dedicada "🏷️ Rastreabilidade" no consumo_lib.py
- [x] Menu "Stencils" com gerenciamento e cadastro
- [x] Conexão com medição de tensão (salva resultado no histórico)
- [ ] Histórico de inspeções visuais (após Fase 9)

**Arquivos:**
- `aoi_lib/stencil_tracker.py` - Modelos e lógica de negócio
- `aoi_lib/stencil_tracker_ui.py` - Widgets PyQt6
- `consumo_lib.py` - Integração de aba, menu e handlers

**Notas:** 
- Persistência em JSON (ver nota de evolução futura para BD)
- Suporte a leitor USB de código de barras via campo de texto

---

### 📄 FASE 8: Relatórios
**Status: 🔴 Pendente**

Geração de relatórios para documentação e rastreabilidade:
- [ ] Relatório individual de medição (heatmap + tabela)
- [ ] Relatório de inspeção visual (imagem anotada)
- [ ] Histórico consolidado por stencil
- [ ] Exportação PDF e CSV

---

### 🔬 FASE 9: Inspeção Visual Automatizada
**Status: 🔴 Pendente**

Análise automática das aberturas do stencil usando máscaras do Gerber:
- [ ] Parser de arquivos Gerber
- [ ] Geração de mosaico completo do stencil
- [ ] Aplicação de transformação de alinhamento (Fase 6)
- [ ] Análise de cada abertura (sujeira, obstrução)
- [ ] Classificação OK/NOK por região

---

## 📊 Resumo do Progresso

| Fase | Descrição | Status |
|------|-----------|--------|
| 1 | Controle de Movimento CNC | ✅ 100% |
| 2 | Sistema de Visão | ✅ 100% |
| 3 | Sistema de Receitas | ✅ 100% |
| 4 | Medição de Tensão | ✅ 100% |
| 5 | Interface Principal | ✅ 100% |
| 6 | Alinhamento de Fiduciais | 🟡 ~80% |
| 7 | Rastreabilidade | ✅ ~95% |
| 8 | Relatórios | 🔴 Pendente |
| 9 | Inspeção Visual Automatizada | 🔴 Pendente |

**Progresso Geral: ~80%**

---

## 🔧 Tecnologias Utilizadas

- **Python 3.10+** - Linguagem principal
- **PyQt6** - Interface gráfica desktop
- **OpenCV** - Processamento de imagem e visão computacional
- **pymodbus** - Comunicação Modbus TCP com CLP industrial
- **NumPy** - Computação numérica para transformações e análise
- **pyserial** - Comunicação serial com tensiômetro

---

## 📚 Referências Técnicas

| Item | Especificação |
|------|---------------|
| Controlador | CLP Delta série AS (Modbus TCP, porta 502) |
| Tensiômetro | AS-120N (Serial RS232, 2400 baud) |
| Câmera | USB compatível com OpenCV |
| Arquivo de máscaras | Gerber (formato RS-274X) |

---

> **Próximas prioridades:**
> 1. ~~Integrar aba de rastreabilidade na interface principal~~ ✅
> 2. ~~Conectar medição de tensão ao histórico do stencil~~ ✅
> 3. Finalizar integração do alinhamento de fiduciais (Fase 6)
> 4. Implementar geração de relatórios (Fase 8)
> 5. Iniciar parser Gerber para inspeção visual (Fase 9)

---

## 🔮 Melhorias Futuras

| Item | Descrição | Prioridade |
|------|-----------|------------|
| **Banco de Dados** | Migrar persistência de JSON para SQLite para melhor performance com grande volume de dados | Média |
| **Relatórios PDF** | Geração automática de relatórios em PDF com gráficos e imagens | Alta |
| **API REST** | Expor dados de inspeção via API para integração com sistemas MES/ERP | Baixa |
| **Backup Automático** | Sistema de backup incremental dos dados de stencils | Média |
