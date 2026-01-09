# Plano de Propostas Visuais - Fluxo de Engenharia
## Criação de Programa de Inspeção Visual

**Data:** 2026-01-09
**Status:** Planejamento
**Versão:** 1.0

---

## 📋 ÍNDICE

1. [Objetivo](#objetivo)
2. [Padrões de Design Identificados](#padrões-de-design-identificados)
3. [Estrutura do Dialog Principal](#estrutura-do-dialog-principal)
4. [Especificações das Abas](#especificações-das-abas)
5. [Plano de Criação dos SVGs](#plano-de-criação-dos-svgs)

---

## 🎯 OBJETIVO

Criar propostas visuais em formato SVG para cada aba do dialog de criação de programa de inspeção visual, seguindo rigorosamente os padrões de design já estabelecidos na aplicação Tensiometro.

**Metas:**
- ✅ Seguir padronização visual existente
- ✅ Manter consistência com wireframes anteriores
- ✅ Facilitar validação com cliente antes da implementação
- ✅ Documentar decisões de design

---

## 🎨 PADRÕES DE DESIGN IDENTIFICADOS

### Paleta de Cores

| Categoria | Cor | Hex | Uso |
|-----------|-----|-----|-----|
| **Primary** | Blue | `#1976D2` | Títulos, botões primários, destaques |
| **Success** | Green | `#4CAF50` | Conclusão, sucesso, badges positivos |
| **Warning** | Orange | `#FF9800` | Alertas, estados de atenção |
| **Danger** | Red | `#F44336` | Erros, ações destrutivas |
| **Background** | White | `#FFFFFF` | Fundo principal, cards |
| **Background** | Light Gray | `#F5F5F5` | Painéis, seções secundárias |
| **Background** | Gray | `#FAFAFA` | Fundo de janela |
| **Border** | Light Gray | `#E0E0E0` | Bordas padrão |
| **Border** | Medium Gray | `#E5E7EB` | Bordas de cards |
| **Text** | Dark Blue | `#1976D2` | Títulos principais |
| **Text** | Black | `#212121` | Texto principal, valores |
| **Text** | Dark Gray | `#424242` | Labels |
| **Text** | Medium Gray | `#616161` | Descrições, subtítulos |
| **Text** | Light Gray | `#6B7280` | Textos secundários |
| **Info BG** | Light Blue | `#E3F2FD` | Fundo de ícones, info boxes |
| **Info BG** | Blue | `#EFF6FF` | Cards de informação |
| **Info BG** | Darker Blue | `#DBEAFE` | Ícones destacados |
| **Success BG** | Light Green | `#E8F5E9` | Fundo de sucesso |
| **Success BG** | Green | `#ECFDF5` | Badges de sucesso |
| **Warning BG** | Light Orange | `#FFF3E0` | Alert boxes |

### Tipografia

**Fonte:** Roboto (Google Fonts)

| Elemento | Tamanho (px) | Peso | Cor | Exemplo |
|----------|--------------|------|-----|---------|
| Dialog Title | 24 | 700 (Bold) | `#1976D2` | "Criar Programa de Inspeção" |
| Section Title | 18-20 | 700 (Bold) | `#1976D2` | "Dados do Programa" |
| Card Title | 18 | 700 (Bold) | `#212121` | "Medição de Tensão" |
| Label | 13 | 500 (Medium) | `#424242` | "Código do Stencil:" |
| Body Text | 14 | 400 (Regular) | `#616161` | Descrições |
| Small Text | 11-12 | 400 (Regular) | `#6B7280` | Detalhes secundários |
| Value Text | 18 | 700 (Bold) | `#212121` | Valores numéricos |
| Button Text | 14 | 500 (Medium) | `#FFFFFF` | Botões primários |

### Componentes UI

**Buttons:**
- Primary: `#1976D2`, texto branco, border-radius 4px, altura 35-45px
- Secondary: `#F5F5F5`, texto `#424242`, border `#BDBEBD`, border-radius 4px
- Hover: 10% mais escuro
- Padding: 5px 15px

**Cards:**
- Background: `#FFFFFF`
- Border: `#E0E0E0`, 1-2px
- Border Radius: 8-12px
- Padding: 16px
- Hover: Background `#F9FAFB`, border `#D1D5DB`

**Painéis:**
- Background: `#FFFFFF` ou `#F5F5F5`
- Border: `#E0E0E0`, 1px
- Border Radius: 4-8px

**Icones:**
- Container: Circle 40-56px radius
- Background: `#E3F2FD` (info), `#E8F5E9` (success)
- Tamanho: 32-48px

**Inputs/Fields:**
- Background: `#FFFFFF`
- Border: `#E0E0E0`, 1px
- Border Radius: 4px
- Height: 35-40px

**Progress Bar:**
- Background: `#E0E0E0`
- Fill: `#4CAF50`
- Height: 40px
- Border Radius: 4px

### Dimensões de Dialog

**Tamanho Padrão:**
- Width: 1200-1400px
- Height: 700-900px
- Min Width: 1000px
- Min Height: 600px

**Margens:**
- External margin: 20px
- Internal spacing: 16-20px
- Element spacing: 8-12px

---

## 📐 ESTRUTURA DO DIALOG PRINCIPAL

### Nome: `CreateInspectionProgramDialog`

**Layout Geral:**

```
┌──────────────────────────────────────────────────────────────────┐
│  [X] Criar Programa de Inspeção Visual                    [_][□][×] │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Abas de Navegação (Wizard Steps)                         │  │
│  │  [1. Dados] [2. Gerber] [3. Fiduciais] [4. Posição]        │  │
│  │  [5. Alinhamento] [6. Janelas] [7. Confirmar]              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │                     CONTEÚDO DA ABA ATIVA                    │  │
│  │                     (varia por aba)                         │  │
│  │                                                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  [< Anterior]  [Próximo >]  [Cancelar]       [❓ Ajuda]    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Navegação (Wizard)

- **Total de abas:** 7
- **Navegação linear:** Apenas avança/volta 1 aba por vez
- **Validação:** Cada aba deve ser validada antes de avançar
- **Indicador visual:**
  - ✅ Aba completa (verde)
  - 🔵 Aba atual (azul)
  - ⚪ Aba pendente (cinza)

---

## 📑 ESPECIFICAÇÕES DAS ABAS

### Aba 1: Dados do Programa

**Objetivo:** Coletar informações básicas do programa de inspeção

**Componentes:**
1. Campo: Código do Stencil (autocomplete ou busca)
2. Campo: Nome do Programa de Inspeção
3. Dropdown: Receita Base (opcional)
4. Botão: "Cadastrar Novo Stencil"
5. Info Box: Instruções preenchimento

**Validação:**
- [ ] Código do stencil preenchido
- [ ] Nome do programa preenchido
- [ ] Stencil existe no sistema (ou usuário cadastra novo)

**Botão "Próximo":** Habilitado após validação

---

### Aba 2: Carregar Gerber

**Objetivo:** Carregar e preparar arquivo Gerber do stencil

**Componentes:**
1. Botão: "Carregar Arquivo Gerber" (`.ger`, `.gbr`, `.gtl`)
2. Preview: Informações do arquivo
   - Dimensões (X × Y mm)
   - Número de apertures
   - Número de fiduciais detectados
3. Lista: Fiduciais detectados automaticamente
4. Botão: "Limpar Gerber" (abre diálogo de limpeza)
5. Info Box: Status de carregamento

**Validação:**
- [ ] Arquivo Gerber carregado
- [ ] Arquivo válido (pelo menos 1 aperture)
- [ ] Fiduciais detectados (ou usuário seleciona manualmente na aba 3)

**Botão "Próximo":** Habilitado após Gerber carregado

---

### Aba 3: Definir Fiduciais

**Objetivo:** Marcar fiduciais 1 e 2 no Gerber

**Componentes:**
1. Widget: Preview do Gerber com overlay visual
2. Controles:
   - Zoom in/out/reset
   - Pan (arrastar)
3. Seleção:
   - Radio button: Fiducial 1 (clicar no Gerber)
   - Radio button: Fiducial 2 (clicar no Gerber)
   - Display de coordenadas (X, Y) para cada fiducial
4. Checkbox: "Fiduciais não visíveis - usar ponto/grupo como referência"
5. Info Box: Instruções de seleção

**Validação:**
- [ ] Fiducial 1 definido
- [ ] Fiducial 2 definido
- [ ] Coordenadas válidas

**Botão "Próximo":** Habilitado após 2 fiduciais definidos

---

### Aba 4: Posicionamento e Captura

**Objetivo:** Mover CNC para fiduciais e capturar mosaico

**Componentes:**
1. **Seção Esquerda:** Controles de Movimento
   - Widget: MovementControlWidget (já existe)
   - Display: Posição atual (X, Y, Z)
   - Instruções passo-a-passo:
     - "Mover até fiducial 1" → [Definir Ponto]
     - "Mover até fiducial 2" → [Definir Ponto]
   - Campos: Definir Canto 1 (X, Y)
   - Campos: Definir Canto 2 (X, Y)
2. **Seção Direita:** Grid de Captura
   - Preview: Grid de FOVs (ex: 4×4 = 16 imagens)
   - Display: Dimensões da área de captura
3. **Botão Principal:** "📷 Realizar Captura"
   - Barra de progresso durante captura
   - Status messages
4. Info Box: Instruções de posicionamento

**Validação:**
- [ ] Fiducial 1 posicionado
- [ ] Fiducial 2 posicionado
- [ ] Canto 1 definido
- [ ] Canto 2 definido
- [ ] Mosaico capturado com sucesso

**Botão "Próximo":** Habilitado após captura completa

---

### Aba 5: Alinhamento

**Objetivo:** Alinhar Gerber com imagem capturada

**Componentes:**
1. Widget: FiducialAlignmentWidget (JÁ EXISTE! ~800 linhas)
2. Display:
   - Imagem capturada (mosaico montado)
   - Gerber overlay (50% opacidade)
   - Marcadores de fiduciais
3. Controles:
   - Clique + arraste para posicionar Gerber
   - Spinboxes: Translação X, Y (mm)
   - Spinbox: Rotação (graus)
   - Spinbox: Escala (fator)
4. Botão: "Auto-Tuning" (melhorar centralização automaticamente)
5. Info Box:
   - Transformação calculada
   - Qualidade do alinhamento (score)

**Validação:**
- [ ] Alinhamento realizado (manual ou auto)
- [ ] Score de alinhamento ≥ 70%
- [ ] Transformação aplicada

**Botão "Próximo":** Habilitado após alinhamento aceitável

---

### Aba 6: Janelas de Inspeção ⭐ **NOVA**

**Objetivo:** Configurar parâmetros de inspeção por agrupamento de aberturas

**Componentes:**

**Layout Principal:**
```
┌─────────────────────────────────────────────────────────────────┐
│  🔍 Configuração de Janelas de Inspeção                          │
├───────────────────────────────┬─────────────────────────────────┤
│  ┌─────────────────────────┐ │  ┌─────────────────────────────┐ │
│  │ 📦 Lista de Grupos      │ │  │  Configuração do Grupo      │ │
│  │ (árvore hierárquica)    │ │  │  selecionado                │ │
│  │                         │ │  │                             │ │
│  │ 📦 0.5mm (145)  ✅      │ │  │  Grupo: 0.5mm              │ │
│  │   ├─ Padrão             │ │  │  Quantidade: 145 aberturas  │ │
│  │   └─ Exceções (3)       │ │  │                             │ │
│  │      └─ ⚙️ ID=45        │ │  │  Thresholds:               │ │
│  │                         │ │  │  ✅ OK ≥ [90]%             │ │
│  │ 📦 0.8mm (82)  🟢       │ │  │  ⚠️ PARTIAL ≥ [70]%        │ │
│  │   └─ Padrão             │ │  │  ❌ BLOQUEADO < 70%        │ │
│  │                         │ │  │                             │ │
│  │ 📦 1.2mm (23)  ⚪       │ │  │  Binarização:              │ │
│  │   └─ Padrão             │ │  │  Método: [Otsu ▼]         │ │
│  │                         │ │  │  Pré-process: [Blur ▼]    │ │
│  │ [Expandir Todos]        │ │  │                             │ │
│  │ [Recolher Todos]        │ │  │  Preview Visual (3 exemplos):│
│  │ [Auto-Agrupar]          │ │  │  [┌───┐ ┌───┐ ┌───┐]       │ │
│  └─────────────────────────┘ │  │  [│ ✓ │ │ ✓ │ │ ✓ │]       │ │
│                             │ │  │  [└───┘ └───┘ └───┘]       │ │
│                             │ │  │                             │ │
│                             │ │  │  [Aplicar a Todas]         │ │
│                             │ │  │  [Confirmar Grupo] ✅      │ │
│                             │ │  │  [Adicionar Exceção] ⚙️   │ │
│                             │ │  │  [Salvar na Biblioteca] 💾 │ │
│                             │ │  └─────────────────────────────┘ │
│                             │                                     │
│  ┌─────────────────────────┐ │                                     │
│  │ 📚 Biblioteca de Configs│ │                                     │
│  │ (configs reaproveitáveis)│ │                                     │
│  │                         │ │                                     │
│  │ ⚙️ 0.5mm - Padrão      │ │                                     │
│  │ ⚙️ 0.8mm - Padrão      │ │                                     │
│  │ [Carregar no Grupo]     │ │                                     │
│  └─────────────────────────┘ │                                     │
└───────────────────────────────┴─────────────────────────────────┘
```

**Funcionalidades:**
1. **Agrupamento Automático:**
   - Por dimensão exata (ex: 0.5mm = 0.5mm)
   - Por tolerância (ex: 0.48-0.52mm ≈ 0.5mm)
   - Botão: "Auto-Agrupar" (executa agrupamento inicial)

2. **Árvore de Grupos:**
   - Ícone pasta: 📦
   - Nome: dimensão principal
   - Contador: (N aberturas)
   - Status:
     - ⚪ Não configurado
     - 🟢 Configurado (mas não confirmado)
     - ✅ Confirmado
   - Expandir/recolher grupos
   - Sub-itens:
     - "Padrão" (configuração aplicada à maioria)
     - "Exceções" (aberturas com config específica)

3. **Configuração por Grupo:**
   - Threshold OK (%)
   - Threshold PARTIAL (%)
   - Método de binarização (Otsu, Adaptativo, Fixed)
   - Pré-processamento (Blur, Denoise, None)
   - Preview visual de 3 aberturas do grupo
   - Checkbox: "Aplicar a todas do grupo"
   - Botões: "Confirmar Grupo", "Adicionar Exceção"

4. **Biblioteca de Configurações:**
   - Salvar config atual como template
   - Carregar config salva
   - Auto-sugestão baseada em histórico

**Validação:**
- [ ] Todos os grupos configurados (pelo menos 1 grupo)
- [ ] Pelo menos 1 grupo confirmado
- [ ] Não há grupos sem configuração

**Botão "Próximo":** Habilitado quando todos grupos têm config

---

### Aba 7: Confirmar e Salvar

**Objetivo:** Revisão final e salvamento do programa

**Componentes:**
1. **Resumo Completo:**
   - ✅ Stencil: ABC-123
   - ✅ Nome do Programa: "Inspeção Padrão 0.5mm"
   - ✅ Gerber: stencil_abc.gbr (245 apertures)
   - ✅ Fiduciais: 2 definidos [(15.2, 20.3), (180.5, 20.3)]
   - ✅ Alinhamento: tx=1.2mm, ty=-0.5mm, θ=0.3°, scale=1.01
   - ✅ Mosaico: 4×4 = 16 FOVs capturadas
   - ✅ Janelas: 8 grupos configurados, 245 aberturas totais

2. **Estatísticas:**
   - Tempo estimado de execução: ~5 min
   - Memória estimada: ~150 MB
   - Qualidade esperada: 95%

3. **Botões de Ação:**
   - "💾 Salvar Programa" (principal)
   - "🧪 Testar Inspeção" (executa inspeção completa em modo teste)
   - "← Voltar" (revisar abas anteriores)

4. **Info Box:**
   - Mensagem de confirmação
   - Local de salvamento (path do arquivo)

**Validação Final:**
- [ ] Todos os dados preenchidos
- [ ] Validações passadas
- [ ] Programa pronto para uso

**Botão "Salvar":** Salva e fecha dialog

**Botão "Testar":** Salva e executa inspeção teste

---

## 🖼️ PLANO DE CRIAÇÃO DOS SVGS

### Estrutura de Arquivos

```
docs/wireframes/svg/engenharia/
├── 01_aba_dados_programa.svg
├── 02_aba_carregar_gerber.svg
├── 03_aba_definir_fiduciais.svg
├── 04_aba_posicionamento_captura.svg
├── 05_aba_alinhamento.svg
├── 06_aba_janelas_inspecao.svg
├── 07_aba_confirmar_salvar.svg
└── README.md
```

### Metadados de Cada SVG

Cada arquivo SVG deve conter:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg width="1400" height="900" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&amp;display=swap');
      /* Classes CSS reutilizáveis */
    </style>
  </defs>

  <!-- Background -->
  <!-- Dialog Shadow -->
  <!-- Main Dialog -->
  <!-- Header -->
  <!-- Tab Navigation -->
  <!-- Tab Content (varia por arquivo) -->
  <!-- Footer Buttons -->
</svg>
```

### CSS Classes Reutilizáveis

```css
/* Typography */
.title { font-family: 'Roboto', sans-serif; font-size: 24px; font-weight: 700; fill: #1976D2; }
.subtitle { font-family: 'Roboto', sans-serif; font-size: 16px; font-weight: 400; fill: #616161; }
.label { font-family: 'Roboto', sans-serif; font-size: 13px; font-weight: 500; fill: #424242; }
.body-text { font-family: 'Roboto', sans-serif; font-size: 14px; font-weight: 400; fill: #616161; }
.small-text { font-family: 'Roboto', sans-serif; font-size: 11px; font-weight: 400; fill: #6B7280; }
.button-text { font-family: 'Roboto', sans-serif; font-size: 14px; font-weight: 500; fill: #FFFFFF; }

/* Colors */
.primary-blue { fill: #1976D2; }
.success-green { fill: #4CAF50; }
.warning-orange { fill: #FF9800; }
.danger-red { fill: #F44336; }
.bg-white { fill: #FFFFFF; }
.bg-gray { fill: #F5F5F5; }
.bg-light-blue { fill: #E3F2FD; }
.border-gray { stroke: #E0E0E0; }

/* Components */
.dialog-bg { fill: #FFFFFF; stroke: #E0E0E0; stroke-width: 1; }
.card-bg { fill: #FFFFFF; stroke: #E0E0E0; stroke-width: 1; }
.panel-bg { fill: #F5F5F5; stroke: #E0E0E0; stroke-width: 1; }
.button-primary { fill: #1976D2; }
.button-secondary { fill: #F5F5F5; stroke: #BDBEBD; stroke-width: 1; }

/* States */
.tab-active { fill: #1976D2; }
.tab-complete { fill: #4CAF50; }
.tab-pending { fill: #E0E0E0; }
```

### Template SVG Base

Vou criar um template SVG reutilizável que contém:
- Background principal
- Dialog container
- Header fixo
- Navegação de abas
- Footer fixo (botões)

Cada aba específica vai apenas substituir a área de conteúdo.

---

## 📝 CHECKLIST DE CRIAÇÃO

### Para Cada SVG:

- [ ] Template base aplicado
- [ ] Header com título da aba
- [ ] Navegação de abas com indicadores de estado
- [ ] Conteúdo específico da aba desenhado
- [ ] Componentes seguindo padronização (cores, fontes, tamanhos)
- [ ] Botões de navegação (Anterior/Próximo) com estados corretos
- [ ] Validações visuais (campos obrigatórios marcados)
- [ ] Tooltips ou instruções quando necessário
- [ ] Responsividade considerada (proporções corretas)
- [ ] Acessibilidade (contraste, tamanho de fonte)

### Após Criação de Todos os SVGs:

- [ ] Revisão de consistência visual entre abas
- [ ] Validação de que todos os componentes existem
- [ ] Verificação de fluxo lógico (navegação faz sentido?)
- [ ] Documentação de decisões de design
- [ ] Preparação para apresentação ao cliente

---

## 🚀 PRÓXIMOS PASSOS

1. **Criar diretório** `docs/wireframes/svg/engenharia/`
2. **Criar template SVG base** reutilizável
3. **Gerar SVG das 7 abas** seguindo especificações
4. **Criar README.md** no diretório com descrição de cada aba
5. **Validar visualmente** todos os SVGs
6. **Apresentar ao cliente** para aprovação
7. **Documentar feedback** e revisar se necessário

---

**Autor:** Claude Code (Sonnet 4.5)
**Data:** 2026-01-09
**Versão:** 1.0
