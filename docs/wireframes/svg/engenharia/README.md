# Propostas Visuais - Fluxo de Engenharia
## Criação de Programa de Inspeção Visual

**Data:** 2026-01-09
**Versão:** 1.0
**Status:** Propostas Aprovadas para Implementação

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Padrões de Design Utilizados](#padrões-de-design-utilizados)
3. [Descrição das Abas](#descrição-das-abas)
4. [Como Visualizar](#como-visualizar)
5. [Validações por Aba](#validações-por-aba)

---

## 🎯 VISÃO GERAL

Este diretório contém **7 propostas visuais em formato SVG** para o dialog de criação de programa de inspeção visual. Cada SVG representa uma aba do fluxo wizard que um engenheiro percorre para configurar um programa de inspeção completo.

### Estrutura do Dialog

```
Dialog: CreateInspectionProgramDialog
├── Aba 1: Dados do Programa
├── Aba 2: Carregar Gerber
├── Aba 3: Definir Fiduciais
├── Aba 4: Posicionamento e Captura
├── Aba 5: Alinhamento
├── Aba 6: Janelas de Inspeção
└── Aba 7: Confirmar e Salvar
```

---

## 🎨 PADRÕES DE DESIGN UTILIZADOS

### Cores Principais

| Uso | Cor Hex | Descrição |
|-----|---------|-----------|
| Primary Blue | `#1976D2` | Títulos, botões primários, destaques |
| Success Green | `#4CAF50` | Conclusões, itens completos, badges positivos |
| Warning Orange | `#FF9800` | Alertas, estados de atenção |
| Danger Red | `#F44336` | Erros, ações destrutivas |
| Background White | `#FFFFFF` | Fundo principal |
| Background Gray | `#F5F5F5` | Painéis secundários |
| Border Gray | `#E0E0E0` | Bordas padrão |
| Text Title | `#1976D2` | Títulos principais |
| Text Body | `#616161` | Texto corporativo |

### Tipografia

**Fonte:** Roboto (Google Fonts)

| Elemento | Tamanho | Peso | Cor |
|----------|---------|------|-----|
| Dialog Title | 24px | 700 (Bold) | `#1976D2` |
| Section Title | 18-20px | 700 (Bold) | `#1976D2` |
| Label | 13px | 500 (Medium) | `#424242` |
| Body Text | 14px | 400 (Regular) | `#616161` |
| Small Text | 11px | 400 (Regular) | `#6B7280` |
| Button Text | 14px | 500 (Medium) | `#FFFFFF` |

### Componentes

- **Dialog:** 1200×800px ou 1400×900px, border-radius 8px
- **Cards:** Background `#FFFFFF`, border 1-2px `#E0E0E0`, border-radius 8-12px
- **Buttons:** Height 35-45px, border-radius 4px
  - Primary: `#1976D2`, texto branco
  - Secondary: `#F5F5F5`, texto `#424242`
  - Success: `#4CAF50`
- **Inputs:** Height 35-40px, border 1px `#E0E0E0`, border-radius 4px

---

## 📑 DESCRIÇÃO DAS ABAS

### 1. Dados do Programa (`01_aba_dados_programa.svg`)

**Objetivo:** Coletar informações básicas do programa de inspeção.

**Componentes:**
- Campo: Código do Stencil (com autocomplete/busca)
- Campo: Nome do Programa de Inspeção
- Dropdown: Receita Base (opcional)
- Botão: "Cadastrar Novo Stencil" (abre dialog existente)
- Painel lateral: Informações do stencil selecionado
- Painel lateral: Próximos passos do wizard

**Validações:**
- [ ] Código do stencil preenchido
- [ ] Stencil existe no sistema (ou usuário cadastra novo)
- [ ] Nome do programa preenchido

**Botão "Próximo":** Habilitado após validações passarem.

---

### 2. Carregar Gerber (`02_aba_carregar_gerber.svg`)

**Objetivo:** Carregar e preparar arquivo Gerber do stencil.

**Componentes:**
- Área de upload (drag & drop ou seleção)
- Botão: "Carregar Arquivo Gerber" (`.ger`, `.gbr`, `.gtl`)
- Painel: Informações do arquivo carregado
  - Nome do arquivo
  - Dimensões (X × Y mm)
  - Número de apertures detectados
  - Número de fiduciais detectados
  - Formato (RS-274X)
- Lista: Fiduciais detectados automaticamente (3 candidatos)
  - Botão "Usar" para cada fiducial
- Botão: "Limpar Gerber" (abre dialog de limpeza)
- Botão: "Remover Arquivo"

**Validações:**
- [ ] Arquivo Gerber carregado
- [ ] Arquivo válido (pelo menos 1 aperture)
- [ ] Fiduciais detectados (ou usuário define manualmente na próxima aba)

**Botão "Próximo":** Habilitado após Gerber carregado com sucesso.

---

### 3. Definir Fiduciais (`03_aba_definir_fiduciais.svg`)

**Objetivo:** Marcar fiduciais 1 e 2 no arquivo Gerber.

**Componentes:**
- Preview: Gerber visualizado com overlay
- Controles de zoom: Zoom in/out/reset
- Radio buttons: Seleção de Fiducial 1 e Fiducial 2
- Display: Coordenadas (X, Y) de cada fiducial
- Checkbox: "Fiduciais não visíveis - usar ponto/grupo como referência"
- Botão: "Redefinir Fiduciais"
- Painel lateral: Controles de seleção e edição

**Validações:**
- [ ] Fiducial 1 definido (coordenadas válidas)
- [ ] Fiducial 2 definido (coordenadas válidas)
- [ ] Distância entre fiduciais > 50mm (evita erro de precisão)

**Botão "Próximo":** Habilitado após 2 fiduciais definidos.

---

### 4. Posicionamento e Captura (`04_aba_posicionamento_captura.svg`)

**Objetivo:** Mover máquina para fiduciais e capturar mosaico do stencil.

**Componentes:**
- **Painel Esquerdo:**
  - Display: Posição atual (X, Y, Z)
  - Passo 1: Campos X, Y para Fiducial 1 + Botão "Definir Ponto"
  - Passo 2: Campos X, Y para Fiducial 2 + Botão "Definir Ponto"
  - Passo 3: Campos para Canto 1 e Canto 2 + Botão "Auto-Calcular"
  - Botão Principal: "📷 Realizar Captura"
  - Barra de progresso durante captura
- **Painel Direito:**
  - Grid 4×4 visualizando FOVs (16 imagens)
  - Legenda: Capturado (verde), Atual (laranja), Pendente (cinza)
  - Informações: Área de captura, resolução, tempo estimado

**Validações:**
- [ ] Fiducial 1 posicionado (X, Y definidos)
- [ ] Fiducial 2 posicionado (X, Y definidos)
- [ ] Canto 1 definido
- [ ] Canto 2 definido
- [ ] Mosaico capturado com sucesso (todas as FOVs)

**Botão "Próximo":** Habilitado após captura completa.

---

### 5. Alinhamento (`05_aba_alinhamento.svg`)

**Objetivo:** Alinhar Gerber com imagem capturada do stencil.

**Componentes:**
- **Preview Principal:**
  - Imagem capturada (mosaico montado)
  - Gerber overlay (50% opacidade, azul)
  - Marcadores de fiduciais (círculos verdes)
  - Linha de distância entre fiduciais
  - Info de transformação (tx, ty, θ, scale, score)
- **Controles de Ajuste:**
  - Translação X (mm): Spinbox
  - Translação Y (mm): Spinbox
  - Rotação (graus): Spinbox
  - Escala: Spinbox
- **Score Display:** Porcentagem de alinhamento (87% = bom)
- **Botões:**
  - "🎯 Auto-Tuning": Melhorar centralização automaticamente
  - "🔄 Reset": Voltar ao estado inicial
  - "✓ Aplicar": Confirmar alinhamento
- **Zoom/Pan:** Controles de visualização

**Validações:**
- [ ] Alinhamento realizado (manual ou auto)
- [ ] Score de alinhamento ≥ 70%
- [ ] Transformação aplicada

**Botão "Próximo":** Habilitado após score ≥ 70%.

---

### 6. Janelas de Inspeção (`06_aba_janelas_inspecao.svg`)

**Objetivo:** Configurar parâmetros de inspeção por agrupamento de aberturas.

**Componentes:**
- **Painel Esquerdo (Árvore de Grupos):**
  - Lista hierárquica de grupos por dimensão
  - Ícones: 📦 (grupo), ✓ (configurado), 🟢 (não confirmado), ⚪ (pendente)
  - Toolbar: Expandir Todos, Recolher Todos, Auto-Agrupar
  - Exemplos:
    - "📦 0.5mm (145) ✅" → Confirmado
    - "📦 0.8mm (82) 🟢" → Configurado, não confirmado
    - "📦 1.2mm (23) ⚪" → Pendente
- **Painel Direito (Configuração):**
  - Info do grupo selecionado
  - Threshold OK (%): Spinbox (ex: 90)
  - Threshold PARTIAL (%): Spinbox (ex: 70)
  - Método de Binarização: Dropdown (Otsu, Adaptativo, Fixed)
  - Pré-processamento: Dropdown (Blur, Denoise, None)
  - Preview Visual: 3 exemplos do grupo com resultado
  - Botões de Ação:
    - "Aplicar a Todas"
    - "✓ Confirmar Grupo"
    - "⚙️ Exceção" (config específica para 1 aperture)
    - "💾 Salvar na Biblioteca"
  - Biblioteca: Configs reaproveitáveis

**Validações:**
- [ ] Todos os grupos configurados (pelo menos 1 grupo)
- [ ] Pelo menos 1 grupo confirmado
- [ ] Não há grupos sem configuração

**Botão "Próximo":** Habilitado quando todos grupos têm configuração.

---

### 7. Confirmar e Salvar (`07_aba_confirmar_salvar.svg`)

**Objetivo:** Revisão final e salvamento do programa de inspeção.

**Componentes:**
- **Resumo Completo ( verde):**
  - ✅ Stencil: código e descrição
  - ✅ Nome do Programa
  - ✅ Gerber: nome, número de apertures
  - ✅ Fiduciais: 2 definidos com coordenadas
  - ✅ Alinhamento: tx, ty, θ, scale, score
  - ✅ Mosaico: grid FOVs, área capturada
  - ✅ Janelas: grupos configurados, total de aberturas
  - Breakdown de grupos com status
- **Painel de Estatísticas:**
  - Tempo estimado de execução
  - Memória estimada
  - Qualidade esperada
  - Precisão de alinhamento
- **Painel de Validações:**
  - ✓ Todos campos obrigatórios preenchidos
  - ✓ Gerber válido
  - ✓ Fiduciais definidos
  - ✓ Mosaico capturado
  - ✓ Grupos configurados
  - ✓ Programa pronto para uso!

**Botões:**
- "← Anterior": Voltar para revisar abas anteriores
- "🧪 Testar": Salva e executa inspeção completa em modo teste
- "💾 Salvar": Salva programa e fecha dialog
- "Cancelar": Aborta criação (confirmação)

---

## 👁️ COMO VISUALIZAR

### Opção 1: Navegador de Arquivos

1. Abra qualquer arquivo `.svg` diretamente no navegador (Chrome, Firefox, Edge)
2. Use Ctrl+Mouse Wheel para zoom
3. Arraste para pan se necessário

### Opção 2: Visualizador de Imagens

1. Abra o SVG em:
   - Windows: Photos, Paint.NET
   - Linux: EOG, GIMP
   - macOS: Preview
2. Zoom para ver detalhes

### Opção 3: Editores de SVG

1. Abra em editor vetorial:
   - Inkscape (grátis, open-source)
   - Adobe Illustrator
   - Figma
2. Possível editar cores, textos, layouts

---

## ✅ VALIDAÇÕES POR ABA

### Aba 1: Dados do Programa
- Código stencil: não vazio
- Stencil existe: verifica em `StencilTracker.stencil_exists()`
- Nome programa: não vazio
- Receita: opcional

### Aba 2: Carregar Gerber
- Arquivo carregado: caminho não vazio
- Arquivo válido: `GerberParser.parse()` sem erro
- Apertures > 0: pelo menos 1 aperture detectada
- Fiduciais: opcional aqui (pode definir manualmente na aba 3)

### Aba 3: Definir Fiduciais
- Fiducial 1: coordenadas (x, y) definidas, dentro dos limites do Gerber
- Fiducial 2: coordenadas (x, y) definidas, dentro dos limites do Gerber
- Distância mínima: `dist(fid1, fid2) > 50mm` (evita erro)

### Aba 4: Posicionamento e Captura
- Fiduciais posicionados: X, Y definidos para ambos
- Cantos definidos: Canto 1 (x1, y1) e Canto 2 (x2, y2)
- Área válida: `x2 > x1` e `y2 > y1`
- Mosaico capturado: todas as FOVs salvas em disco

### Aba 5: Alinhamento
- Transformação definida: tx, ty, θ, scale têm valores
- Score mínimo: `score >= 70%` (calculado por `FiducialAligner`)
- Gerber overlay: visível sobre imagem

### Aba 6: Janelas de Inspeção
- Todos grupos configurados: cada grupo tem thresholds definidos
- Pelo menos 1 confirmado: pelo menos 1 grupo marcado como confirmado
- Thresholds válidos: `OK >= PARTIAL >= 0`
- Método binarização: selecionado para cada grupo

### Aba 7: Confirmar e Salvar
- Todas validações anteriores: passam
- Consistência: dados fazem sentido juntos
- Caminho de salvamento: definido (ex: `data/inspection_programs/`)

---

## 📊 RESUMO DE COMPONENTES

### Widgets Reutilizáveis Existentes

Estes widgets JÁ ESTÃO IMPLEMENTADOS e serão reutilizados:

- ✅ `StencilCreateDialog` - Cadastro de stencil (aoi_lib/stencil_tracker_ui.py)
- ✅ `GerberParser` - Parser de arquivos Gerber (aoi_lib/gerber_parser.py)
- ✅ `FiducialAlignmentWidget` - Alinhamento interativo (aoi_lib/fiducial_alignment_widget.py)
- ✅ `MovementControlWidget` - Controles CNC (consumo_lib/widgets/movement_control.py)
- ✅ `MosaicBuilder` - Captura de mosaico (tools/mosaic_builder.py)
- ✅ `InspectionSettingsDialog` - Configuração de thresholds (consumo_lib/dialogs/inspection_settings.py)

### Novos Componentes a Implementar

Estes componentes PRECISAM SER CRIADOS:

- 🔴 `CreateInspectionProgramDialog` - Dialog principal com wizard
- 🔴 `InspectionWindowConfigWidget` - Configuração por agrupamento (Aba 6)
- 🟡 `GerberLoaderWidget` - Carregamento e preview de Gerber (Aba 2)
- 🟡 `FiducialSelectorWidget` - Seleção visual de fiduciais (Aba 3)
- 🟡 `PositioningCaptureCoordinator` - Orquestrador de captura (Aba 4)

Legenda:
- 🔴 Alta prioridade (complexo, crítico)
- 🟡 Média prioridade (moderadamente complexo)
- 🟢 Baixa prioridade (simples)

---

## 🚀 PRÓXIMOS PASSOS

1. **Apresentação ao Cliente**
   - Mostrar SVGs em tela cheia
   - Explicar fluxo wizard
   - Coletar feedback

2. **Aprovação**
   - Cliente aprova propostas
   - Documenta alterações solicitadas

3. **Implementação**
   - Criar componentes na ordem de prioridade
   - Testar cada aba individualmente
   - Integrar fluxo completo

4. **Validação**
   - Testar com hardware real
   - Ajustar based em feedback prático
   - Documentar decisões técnicas

---

**Autor:** Claude Code (Sonnet 4.5)
**Data:** 2026-01-09
**Versão:** 1.0
**Total de SVGs:** 7 abas criadas
