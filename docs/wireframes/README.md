# Wireframes - Interface do Operador

**Data:** 2026-01-08
**Versão:** 1.0
**Status:** ✅ Pronto para Validação com Cliente

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Estrutura de Arquivos](#estrutura-de-arquivos)
3. [Como Visualizar](#como-visualizar)
4. [Lista de Wireframes](#lista-de-wireframes)
5. [Fluxo de Validação](#fluxo-de-validação)
6. [Após Validação](#após-validação)

---

## VISÃO GERAL

### Propósito

Esta pasta contém os wireframes em formato SVG da interface do usuário operador do sistema Tensiômetro. Estes wireframes foram criados para validação com o cliente antes da implementação.

### O que são Wireframes?

Wireframes são representações visuais estáticas da interface, focadas em:
- **Layout:** Posição dos componentes na tela
- **Fluxo:** Navegação entre telas
- **Funcionalidade:** O que cada componente faz
- **Conteúdo:** Informações exibidas em cada tela

**NÃO são:**
- Design visual final (cores, fontes, etc)
- Interface funcional (não interagem)
- Código de implementação

### Público-Alvo

- **Cliente:** Validar se a interface atende às necessidades
- **Gerente de Projeto:** Aprovar escopo e funcionalidades
- **Desenvolvedores:** Usar como referência para implementação
- **Designers:** Criar design visual final baseado nestes wireframes

---

## ESTRUTURA DE ARQUIVOS

```
docs/wireframes/
├── README.md                        # Este arquivo
└── svg/                             # Wireframes em formato SVG
    ├── 01_login_dialog.svg          # Tela de login
    ├── 02_tela_inicial_treeview.svg # Tela inicial com lista de programas
    ├── 03_confirmacao_posicionamento.svg # Confirmação de posicionamento
    ├── 04_escolha_modo.svg          # Escolha do modo de inspeção
    ├── 05_tela_execucao.svg         # Tela de execução automática
    ├── 06_analise_visual_humana.svg # Análise de defeitos (v1 original)
    ├── 06_analise_visual_humana_v2.svg # Análise de defeitos (v2 simplificada)
    ├── 07_tela_historico.svg        # Histórico de medições (v1 original)
    └── 07_tela_historico_v2.svg     # Histórico de medições (v2 limpo)
```

### Convenção de Nomenclatura

Arquivos são numerados para refletir a ordem do fluxo:
- `01_` - Primeira tela (login)
- `02_` - Segunda tela (treeview)
- etc.

---

## COMO VISUALIZAR

### Opção 1: Navegador Web (Recomendado)

1. Abra qualquer navegador (Chrome, Firefox, Edge)
2. Arraste o arquivo `.svg` para o navegador
3. OU clique com botão direito → "Abrir com" → Navegador

**Vantagens:**
- Zoom livre (Ctrl + Scroll)
- Fácil compartilhar com cliente
- Não requer instalação

### Opção 2: Visualizador de Imagens

- Windows: Fotos, Paint.NET
- Linux: Eye of GNOME, Gwenview
- macOS: Preview

### Opção 3: Editor de SVG

Para abrir e editar:
- **Inkscape** (grátis, multiplataforma)
- **Adobe Illustrator** (pago)
- **Figma** (online, gratuito)

---

## LISTA DE WIREFRAMES

### Nota sobre Versões

**v1 (Original):** Primeira versão apresentada ao cliente.
**v2 (Atualizada):** Versões modificadas com base no feedback do cliente.

**Telas com versões atualizadas:**
- `06_analise_visual_humana_v2.svg` - Abordagem simplificada "descartar e recomeçar"
- `07_tela_historico_v2.svg` - Histórico limpo sem informações de iteração

**Mudanças Principais nas versões v2:**
- Removido fluxo iterativo de correção e reteste
- Adicionada opção final "Descartar Inspeção" quando há defeitos confirmados
- Histórico agora mostra apenas 3 status: A-AUTO, A-USER, REPROV
- Inspeções descartadas NÃO ficam no histórico (apenas log de auditoria interno)

Veja `docs/guides/ANALISE_PROPOSTA_SIMPLIFICADA.md` para análise comparativa completa.

---

### 01_login_dialog.svg

**Descrição:** Tela de login do sistema

**Componentes:**
- Logo TENSIO METRO
- Campo de usuário
- Campo de senha
- Botões: Entrar, Cancelar
- Versão do sistema

**Fluxo:**
- Entrada: Usuário abre aplicação
- Saída: Usuário autenticado → Vai para tela 02

**Decisões do Cliente:**
- [ ] Layout aprovado?
- [ ] Campos necessários?
- [ ] Botões adequados?

---

### 02_tela_inicial_treeview.svg

**Descrição:** Tela inicial com lista de programas cadastrados

**Componentes:**
- Campo de busca incremental
- Filtros (período, status)
- Ordenação
- TreeView com programas
- Painel de detalhes do stencil
- Histórico visual (10 pontos)
- Botão: Escanear código de barras
- Status do hardware (PLC, Tensiômetro, Câmera)
- Botão: Inspecionar Stencil

**Fluxo:**
- Entrada: Usuário faz login
- Saída: Usuário seleciona programa → Vai para tela 03

**Decisões do Cliente:**
- [ ] Informações suficientes no painel de detalhes?
- [ ] Histórico visual adequado?
- [ ] Filtros necessários?
- [ ] Layout aprovado?

---

### 03_confirmacao_posicionamento.svg

**Descrição:** Dialog de confirmação de posicionamento do stencil

**Componentes:**
- Ícone do stencil
- Código do stencil selecionado
- Instruções de verificação
- Checklist visual
- Botões: Confirmar, Cancelar
- Aviso sobre Emergency Stop

**Fluxo:**
- Entrada: Usuário seleciona programa
- Saída: Usuário confirma → Vai para tela 04
- Saída: Usuário cancela → Volta para tela 02

**Decisões do Cliente:**
- [ ] Instruções claras?
- [ ] Checklist necessário?
- [ ] Aviso de Emergency Stop adequado?

---

### 04_escolha_modo.svg

**Descrição:** Dialog para escolher modo de inspeção

**Componentes:**
- 3 cards com opções:
  - Apenas Tensão
  - Apenas Inspeção Visual
  - Ambos (Completo)
- Descrições e tempos estimados
- Indicador de "Recomendado"
- Botão de seleção em cada card
- Botão Cancelar

**Fluxo:**
- Entrada: Usuário confirma posicionamento
- Saída: Usuário escolhe modo → Vai para validação de hardware → tela 05
- Saída: Usuário cancela → Volta para tela 02

**Decisões do Cliente:**
- [ ] 3 opções necessárias?
- [ ] Tempos estimados corretos?
- [ ] Indicador "Recomendado" adequado?
- [ ] Descrições claras?

---

### 05_tela_execucao.svg

**Descrição:** Tela de execução automática com feedback visual

**Componentes:**
- Barra de progresso
- Contador (ex: "12/25 pontos (48%)")
- Grid visual 5x5:
  - Pontos medidos (verde)
  - Ponto atual (laranja)
  - Pontos pendentes (cinza)
- Tempo estimado restante
- Valores em tempo real (animados)
- Estatísticas (mínima, máxima, média)
- Status de hardware
- Log de medição
- Botão: Parar Execução

**Fluxo:**
- Entrada: Usuário escolhe modo + hardware validado
- Saída: Execução completa → Vai para tela 06 (se houver defeitos) ou salvamento
- Saída: Usuário para → Dados descartados → Volta para tela 02

**Decisões do Cliente:**
- [ ] Feedback visual suficiente?
- [ ] Grid visual necessário?
- [ ] Valores em tempo real necessários?
- [ ] Log de medição útil?
- [ ] Botão Parar adequado?

---

### 06_analise_visual_humana.svg

**⚠️ VERSÃO ATUALIZADA DISPONÍVEL:** `06_analise_visual_humana_v2.svg`

**Descrição:** Tela de julgamento de defeitos identificados pelo sistema

**Versão v1 (Original):**
- Inclui botão "Corrigir e Retestar"
- Permite múltiplas iterações na mesma sessão

**Versão v2 (Atualizada - APROVADA PELO CLIENTE):**
- Abordagem simplificada "descartar e recomeçar"
- 2 opções de julgamento: Aprovar / Confirmar Defeito
- Dialog final com opções: Descartar / Reprovar
- Sem loop de iteração

**Componentes (v2):**
- Lista de defeitos (paginação)
- Imagem do defeito atual
- Controles de zoom
- Análise do sistema (área esperada vs observada, % aberta)
- Campo de anotações
- Dropdown de tipos de defeitos
- Julgamento (2 opções):
  - ✓ Aprovar (Falha Falsa)
  - ✓ Confirmar como Defeito Real
- Navegação (Anterior/Próximo)
- Botão: Finalizar Análise
- **Dialog final (se há defeitos confirmados):**
  - 🗑️ Descartar Inspeção (não salva no histórico)
  - ❌ Reprovar Sessão (salva como reprovado)

**Fluxo (v2):**
- Entrada: Sistema identifica defeitos na inspeção
- Usuário julga cada defeito (Aprovar/Confirmar)
- Ao finalizar:
  - Se todos aprovados → Salva no histórico
  - Se há defeitos confirmados → Usuário escolhe Descartar/Reprovar

**Decisões do Cliente:**
- [x] Aprovação da versão v2 (2026-01-08)
- [x] Abordagem simplificada aprovada
- [ ] Layout final aprovado?

---

### 07_tela_historico.svg

**⚠️ VERSÃO ATUALIZADA DISPONÍVEL:** `07_tela_historico_v2.svg`

**Descrição:** Tela de histórico de medições do stencil

**Versão v1 (Original):**
- Inclui informações de iteração
- Mostra histórico de tentativas de correção

**Versão v2 (Atualizada - APROVADA PELO CLIENTE):**
- Histórico limpo (sem informações de iteração)
- 3 status distintos com badges coloridos:
  - **A-AUTO** (Verde #4CAF50): Aprovado Automático
  - **A-USER** (Verde-amarelo #CDDC39): Aprovado com Julgamento
  - **REPROV** (Vermelho #F44336): Reprovado
- Estatísticas separadas: Aprovadas Auto vs Aprovadas User
- Coluna "Defeitos" mostra: Encontrados / Julgados
  - Exemplo: "15" com "12 / 3" = 12 falhas falsas, 3 defeitos reais
- Legenda explicando que inspeções descartadas não ficam no histórico

**Componentes (v2):**
- Filtros de período (7, 30, 60, 90, 180, 365 dias)
- Filtros de status (Todos, A-AUTO, A-USER, REPROV)
- Estatísticas do período (separadas por tipo de aprovação)
- Tabela de medições com 3 status badges
- Ações:
  - Ver detalhes
  - Gerar PDF
  - Exportar CSV
- Botão: Voltar para TreeView
- **Legenda:** Inspeções descartadas NÃO ficam no histórico (apenas log de auditoria)

**Fluxo:**
- Entrada: Usuário clica em "Ver Histórico"
- Mostra apenas inspeções salvas (não mostra descartadas)
- Saída: Usuário volta para tela 02

**Decisões do Cliente:**
- [x] Aprovação da versão v2 (2026-01-08)
- [x] Histórico limpo aprovado
- [ ] Layout final aprovado?

---

## FLUXO DE VALIDAÇÃO

### Processo

1. **Apresentação ao Cliente**
   - Marcar reunião com cliente
   - Apresentar wireframes em ordem (01 a 07)
   - Explicar fluxo entre telas

2. **Coleta de Feedback**
   - Anotar todas as observações do cliente
   - Marcar alterações necessárias em cada wireframe
   - Priorizar alterações (críticas, importantes, opcionais)

3. **Revisão dos Wireframes**
   - Implementar alterações aprovadas
   - Criar nova versão (v1.1, v1.2, etc)
   - Apresentar novamente ao cliente

4. **Aprovação Final**
   - Cliente aprova todos os wireframes
   - Assinar termo de aprovação
   - Iniciar implementação

### Checklist de Validação

Para cada wireframe, pergunte ao cliente:

**Geral:**
- [ ] Você entende o que esta tela faz?
- [ ] As informações estão organizadas de forma clara?
- [ ] Algo está faltando?
- [ ] Algo está sobrando?

**Componentes:**
- [ ] Todos os campos necessários estão presentes?
- [ ] Os botões estão adequados?
- [ ] Os rótulos (labels) são claros?
- [ ] As cores fazem sentido?

**Fluxo:**
- [ ] Você sabe como chegar a esta tela?
- [ ] Você sabe o que fazer nesta tela?
- [ ] Você sabe para onde ir depois?

### Formulário de Feedback

```
Wireframe: _____________
Data: _____________
Revisor: _____________

O que você GOSTOU:
-
-
-

O que você MUDARIA:
-
-
-

O que está FALTANDO:
-
-
-

O que está SOBRANDO:
-
-
-

Classificação Geral:
[ ] Aprovado
[ ] Aprovado com sugestões menores
[ ] Requer alterações
[ ] Requer revisão completa

Assinatura: _____________
```

---

## APÓS VALIDAÇÃO

### Próximos Passos

1. **Documento de Requisitos Finais**
   - Compilar feedback do cliente
   - Criar lista de requisitos validados
   - Atualizar `plano_implementacao_interface.md`

2. **Especificação Técnica**
   - Detalhar componentes técnicos
   - Definir arquitetura final
   - Especificar integrações

3. **Design Visual (Opcional)**
   - Criar paleta de cores
   - Escolher tipografia
   - Definir espaçamentos
   - Criar protótipos de alta fidelidade

4. **Início da Implementação**
   - Seguir `plano_implementacao_interface.md`
   - Implementar fase por fase
   - Validar com cliente a cada fase

### Versionamento

- **v1.0** (2026-01-08): Criação inicial dos wireframes (telas 01-07)
- **v2.0** (2026-01-08): Atualização das telas 06 e 07 com abordagem simplificada
  - `06_analise_visual_humana_v2.svg`: Fluxo "descartar e recomeçar"
  - `07_tela_historico_v2.svg`: Histórico limpo sem iterações
  - Baseado em feedback do cliente: "não é interessante guardar retrabalhos no histórico"
- **v1.1** (DD/MM/AAAA): Após próximo feedback do cliente
- etc.

Manter histórico de versões em cada arquivo SVG:
```xml
<!-- Versão: 1.0 -->
<!-- Data: 2026-01-08 -->
<!-- Autor: Claude Code -->
<!-- Status: Em validação -->

<!-- Para v2: -->
<!-- Versão: 2.0 -->
<!-- Data: 2026-01-08 -->
<!-- Autor: Claude Code -->
<!-- Status: Aprovada pelo cliente - Aguardando validação final -->
```

---

## REFERÊNCIAS

- **Documento de Fluxo:** `docs/guides/fluxo_usuario_operador.md`
- **Plano de Implementação:** `docs/guides/plano_implementacao_interface.md`
- **Questionário Base:** `docs/guides/fluxo_usuario_questionario.md`
- **CLAUDE.md:** Documentação geral do projeto

---

**Documento criado em:** 2026-01-08
**Versão:** 1.0
**Próxima revisão:** Após validação com cliente
