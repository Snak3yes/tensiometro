# Questionário de Validação - Fluxo de Engenharia
## Criação de Programa de Inspeção Visual

**Data:** 2026-01-09
**Objetivo:** Eliminar ambiguidades e gaps de informação antes da implementação
**Base:** Diagrama de fluxo + Propostas visuais SVG (7 abas)

---

## 📋 ÍNDICE

1. [Conceitos Fundamentais](#1-conceitos-fundamentais)
2. [Aba 1 - Dados do Programa](#2-aba-1---dados-do-programa)
3. [Aba 2 - Carregar Gerber](#3-aba-2---carregar-gerber)
4. [Aba 3 - Definir Fiduciais](#4-aba-3---definir-fiduciais)
5. [Aba 4 - Posicionamento e Captura](#5-aba-4---posicionamento-e-captura)
6. [Aba 5 - Alinhamento](#6-aba-5---alinhamento)
7. [Aba 6 - Janelas de Inspeção](#7-aba-6---janelas-de-inspeção)
8. [Aba 7 - Confirmar e Salvar](#8-aba-7---confirmar-e-salvar)
9. [Integração com Cadastro de Stencil](#9-integração-com-cadastro-de-stencil)
10. [Dialog Modais](#10-dialog-modais)

---

## 1. CONCEITOS FUNDAMENTAIS

### 1.1. Relação Programa ↔ Stencil

**⚠️ GAP CRÍTICO IDENTIFICADO:**

O diagrama original declara:

> "o programa de inspeção deve ser criado de forma genérica a qual quer momento posterior ser associado a um stencil pois um programa de inspeção deve ser associado ao código do stencil e o gerber. A aplicação para que funcione dessa forma e que um stencil com um código de barras diferente pode ter sido feito a partir do mesmo gerber, então deve existir um programa de inspeção A, feito a partir do gerber A, que vai ser usado para stencils x, y, z que foram fabricados a partir do mesmo mesmo gerber mas possuem códigos de barras diferentes."

**Questões:**

Q1.1 - **Qual é a estrutura correta?**

**Opção A:** (Minha proposta original)
- Aba 1 pede "Código do Stencil" como um campo obrigatório
- Programa é criado JÁ associado a um stencil específico
- Exemplo: "Programa de Inspeção do STENCIL-ABC-123"

**Opção B:** (Conforme diagrama)
- Aba 1 NÃO pede código do stencil
- Programa é criado de forma GENÉRICA, baseado apenas no Gerber
- Exemplo: "Programa de Inspeção A (baseado no Gerber A)"
- Posteriormente, esse programa genérico é ASSOCIADO a múltiplos stencils
- Exemplo: STENCIL-ABC-123, STENCIL-ABC-456, STENCIL-ABC-789 usam todos o "Programa de Inspeção A"

**Sua resposta:** A ou B? letra A

---

Q1.2 - **Se resposta for B (Genérico):**

O campo "Código do Stencil" na Aba 1 deve ser:
- [ ] Removido completamente
- [ ] Mantido como OPICIONAL (apenas para referência/sugestão de nome)
- [ ] Substituído por "Nome do Programa de Inspeção" (ex: "Inspeção Padrão 0.5mm - Gerber v1.2")

**Sua resposta:** Escolha acima.

---

Q1.3 - **Como funciona a associação posterior?**

Quando um engenheiro cadastra um NOVO stencil, ele deve:
- [x] Selecionar programas de inspeção existentes de uma lista
- [ ] Criar novos programas associados naquele momento
- [ ] Ambas opções acima

**Sua resposta:** Escolha acima.

---

### 1.2. Terminologia de "Centro" vs "Canto"

**⚠️ GAP IDENTIFICADO:**

Diagrama original menciona:
- "definir centro 1"
- "definir centro 2"

Minha proposta usou:
- "Definir Canto 1"
- "Definir Canto 2"

**Q2.1 - Qual termo está correto?**

- [ ] **Centro 1 e Centro 2**: Refere-se aos centros dos fiduciais (pontos de referência para alinhamento)
- [x] **Canto 1 e Canto 2**: Refere-se aos cantos opostos da área de captura do mosaico (retângulo que delimita a região do stencil a ser capturada)
- [ ] **Ambos**: Primeiro define os centros dos fiduciais, depois define os cantos da área de captura

**Sua resposta:** Escolha acima.

---

### 1.3. Estrutura de Diálogos

**Q3.1 - Como o fluxo deve ser estruturado?**

**Opção A:** (Minha proposta)
- Um ÚNICO dialog modal com 7 abas (wizard)
- Usuário percorre todas as abas sequencialmente
- Botão "Salvar" apenas na última aba

**Opção B:** (Múltiplos diálogos encadeados)
- Dialog 1: Dados básicos + Carregar Gerber
- Dialog 2: Definir fiduciais (abre após Gerber carregado)
- Dialog 3: Posicionamento e captura (abre após fiduciais definidos)
- Dialog 4: Alinhamento (abre após captura)
- Dialog 5: Configuração de janelas (abre após alinhamento)
- Dialog 6: Resumo e salvar

**Opção C:** (Híbrida)
- Dialog principal com abas
- Alguns passos críticos abrem sub-diálogos modais (ex: limpeza de Gerber, auto-tuning)

**Sua resposta:** A, B ou C? letra A

---

## 2. ABA 1 - DADOS DO PROGRAMA

### 2.1. Campos Obrigatórios vs Opcionais

Assumindo resposta **Q1.1 = B** (Programa Genérico):

**Q4.1 - Quais campos devem existir na Aba 1?**

Marque TODOS os campos que devem estar presentes:

- [x] **Nome do Programa de Inspeção** (obrigatório)
  - Exemplo: "Inspeção Padrão 0.5mm - Linha A"
- [x] **Descrição/Comentários** (opcional)
  - Exemplo: "Programa para stencils da linha A fabricados de Jan/2025 em diante"
- [ ] **Código do Stencil de Referência** (opcional)
  - Exemplo: "STENCIL-ABC-123" usado apenas como base para testes
- [ ] **Tag/Etiqueta** (opcional)
  - Exemplo: "Produção", "Teste", "Protótipo"
- [ ] **Versão do Programa** (opcional)
  - Exemplo: "v1.0", "v2.1"
- [ ] **Data de Criação** (automático, somente leitura)

**Sua resposta:** Lista os campos obrigatórios acima.

---

### 2.2. Receita Base

**Q5.1 - A "Receita Base" deve:**

- [ ] Ser selecionada de uma lista de receitas existentes
- [ ] Ser criada em tempo real (durante o fluxo)
- [ ] Ser opcional (programa pode não ter receita associada)
- [ ] Todas as acima

**Sua resposta:** Escolha acima.

---

## 3. ABA 2 - CARREGAR GERBER

### 3.1. Diálogo de Limpeza

Diagrama menciona: "diálogo para realizar a limpeza do gerber, se necessário."

**Q6.1 - Quando esse diálogo deve aparecer?**

- [ ] **Automaticamente** após carregar Gerber (se o sistema detectar problemas)
- [ ] **Apenas** se usuário clicar no botão "Limpar Gerber"
- [ ] **Ambos**: Automaticamente se detectar problemas + botão manual
- [ ] **Nunca**: Limpeza de Gerber não é necessária

**Sua resposta:** Escolha acima.

---

**Q6.2 - O que significa "limpeza do Gerber"?**

Assinale TODAS as operações que o diálogo de limpeza deve permitir:

- [ ] Remover aperturas específicas (por lista visual)
- [ ] Remover apertures por tipo (ex: "remover todos os oblongs")
- [ ] Remover apertures por localização (ex: "remover apertures fora da área útil")
- [ ] Editar dimensões de apertures (redimensionar)
- [ ] Mover apertures (translação)
- [ ] Adicionar apertures manualmente
- [ ] Cortar/trimar área útil do Gerber
- [ ] Corrigir erros de parsing

**Sua resposta:** Lista as operações acima.

---

### 3.2. Detecção Automática de Fiduciais

**Q7.1 - Se o sistema NÃO detectar fiduciais automaticamente, ou se o usuário rejeitar os detectados:**

- [ ] Fluxo pode continuar normalmente (usuário define manualmente na Aba 3)
- [ ] Fluxo é BLOQUEADO até que fiduciais sejam identificados
- [ ] Sistema sugere "usar ponto ou grupo como referência" (conforme diagrama)

**Sua resposta:** Escolha acima.

---

## 4. ABA 3 - DEFINIR FIDUCIAIS

### 4.1. Método de Definição

Diagrama menciona: "usar ponto ou grupo como referência."

**Q8.1 - O que isso significa exatamente?**

Se fiduciais não estão visíveis:

- [ ] Usar **coordenadas manuais** digitadas pelo usuário (ex: X=15.2, Y=20.3)
- [ ] Usar **aperture específica** do Gerber como referência (ex: "usar aperture D10 como marcador")
- [ ] Usar **grupo de apertures** como referência (ex: "centro de massa do grupo de apertures do canto superior esquerdo")
- [ ] Usar **intersecção de linhas** do Gerber (ex: "intersecção das linhas de grade do painel")
- [ ] Outro (descrever):

**Sua resposta:** Escolha acima ou descreva.

---

### 4.2. Número de Fiduciais

**Q9.1 - O sistema DEVE suportar:**

- [ ] Exatamente 2 fiduciais (fixo)
- [ ] 2 a 4 fiduciais (usuário escolhe quantos usar)
- [ ] 2 ou mais fiduciais (flexível)

**Sua resposta:** Escolha acima.

---

## 5. ABA 4 - POSICIONAMENTO E CAPTURA

### 5.1. Ordem dos Passos

Diagrama original:

1. "mover a head até a posição do fiducial 1" → "definir ponto"
2. "mover a head até a posição do fiducial 2" → "definir ponto"
3. "definir centro 1"
4. "definir centro 2"
5. "botão: realizar captura"

Minha proposal trocou "centro" por "canto".

**Q10.1 - Qual é a ordem correta?**

- [ ] **Minha proposta**: Mover para fiduciais → Definir pontos → Definir cantos → Capturar
- [ ] **Diagrama original**: Mover para fiduciais → Definir pontos → Definir centros → Capturar
- [ ] **Outra ordem** (descrever):

**Sua resposta:** Escolha acima ou descreva a ordem correta.

---

### 5.2. Captura de Mosaico

**Q11.1 - Como é determinado o grid de captura?**

- [ ] **Grid fixo**: Sempre 4×4 (16 FOVs), independente do tamanho do stencil
- [ ] **Grid calculado**: Baseado na área definida (centro 1 e centro 2 / canto 1 e canto 2)
- [ ] **Configurável**: Usuário define NxM (ex: 3×3, 4×4, 5×5) antes de capturar
- [ ] **Automático**: Sistema calcula número ideal de FOVs baseado no tamanho total do Gerber

**Sua resposta:** Escolha acima.

---

**Q11.2 - Durante a captura:**

- [ ] Usuário vê preview de cada FOV capturada
- [ ] Usuário vê apenas barra de progresso
- [ ] Usuário pode CANCELAR captura no meio do processo
- [ ] Se uma FOV falhar, sistema:
  - [ ] Tenta capturar novamente automaticamente
  - [ ] Pergunta ao usuário o que fazer
  - [ ] Marca FOV como falha e continua

**Sua resposta:** Assinale as opções acima.

---

### 5.3. "Definir Ponto"

**Q12.1 - O que significa "definir ponto" ao mover para fiducial?**

- [ ] **Apenas salvar coordenadas**: Sistema registra posição atual (X, Y) como posição do fiducial
- [ ] **Capturar template**: Sistema captura imagem do fiducial para usar no alinhamento (template matching)
- [ ] **Ambos**: Salva coordenadas E captura template

**Sua resposta:** Escolha acima.

---

## 6. ABA 5 - ALINHAMENTO

### 6.1. Preview Visual

Diagrama: "gerber editado é 'plotado' sobre a imagem capturada, como se fosse uma imagem com a opacidade em 50% sobre as FOVs capturadas e montadas em uma imagem única."

**Q13.1 - Opacidade do overlay é:**

- [ ] Fixa em 50%
- [ ] Ajustável pelo usuário (slider de 0% a 100%)
- [ ] Ajustável entre 30% e 70%

**Sua resposta:** Escolha acima.

---

**Q13.2 - Qual é a interação EXATA de alinhamento?**

Diagrama: "o usuário vai clicar, manter pressionado e arrastar até uma posição em que se chegue em um alinhamento entre os fiduciais do gerber com os fiduciais do stencil."

Isso significa:

- [ ] **Drag & Drop do Gerber inteiro**: Usuário clica em qualquer lugar do overlay do Gerber e arrasta TODO o Gerber para ajustar alinhamento global
- [ ] **Arrastar fiduciais individualmente**: Usuário pode arrastar fiducial 1 e fiducial 2 separadamente
- [ ] **Ambas opções** acima
- [ ] **Controles manuais**: Apenas spinboxes para translação, rotação e escala (sem drag & drop)
- [ ] **Combinação**: Drag & drop + controles manuais + botão de auto-tuning

**Sua resposta:** Escolha acima.

---

### 6.2. Auto-Tuning

Diagrama: "talvez seja necessário criar um sistema de auto tuning para melhorar a centralização da imagem."

**Q14.1 - Auto-tuning deve:**

- [ ] Ser OBRIGATÓRIO (executa automaticamente após captura)
- [ ] Ser OPCIONAL (botão que usuário pode clicar se quiser melhorar)
- [ ] Ser SUGERIDO (sistema sugere "Deseja melhorar o alinhamento?" se score < 80%)

**Sua resposta:** Escolha acima.

---

**Q14.2 - O que auto-tuning faz exatamente?**

- [ ] Executa template matching para encontrar fiduciais automaticamente
- [ ] Calcula transformação ótima baseada em correspondência de pontos
- [ ] Ajusta apenas translação (X, Y)
- [ ] Ajusta translação + rotação
- [ ] Ajusta translação + rotação + escala
- [ ] Refina alinhamento já feito pelo usuário (não começa do zero)

**Sua resposta:** Assinale as operações acima.

---

## 7. ABA 6 - JANELAS DE INSPEÇÃO

### 7.1. Agrupamento

Diagrama: "as janelas de inspeção devem ser ajustadas, perfeitamente iguais, devem ter suas configurações ajustadas para que o usuário possa realizar os seus ajustes e configurações de inspeção de forma mais fácil e simples."

Há um erro de digitação: "perfeitamente iguais, devem ter suas configurações ajustadas"

**Q15.1 - Qual é a frase correta?**

- [ ] "as janelas de inspeção que forem **PERFEITAMENTE IGUAIS** devem ser agrupadas..."
- [ ] "as janelas de inspeção devem ser **AGRUPADAS**; janelas perfeitamente iguais devem ter suas configurações ajustadas..."
- [ ] Outra interpretação:

**Sua resposta:** Escolha acima ou corrija.

---

**Q15.2 - Critério de agrupamento:**

Janelas são consideradas "perfeitamente iguais" se:

- [ ] **Dimensões EXATAMENTE iguais**: Ex: 0.5mm × 0.5mm = 0.5mm × 0.5mm
- [ ] **Dimensões COM TOLERÂNCIA**: Ex: 0.48mm a 0.52mm são agrupadas como "0.5mm"
- [ ] **Dimensões + Forma**: 0.5mm círculo é DIFERENTE de 0.5mm quadrado
- [ ] **Todas acima** (dimensão + forma + tolerância)

**Sua resposta:** Escolha acima.

---

### 7.2. Configuração de Exceções

Diagrama: "no agrupamento deve existir a possibilidade de fazer uma configuração específica para uma abertura mesmo que ela seja igual a outras."

**Q16.1 - Como usuário cria uma exceção?**

- [ ] Clica na aperture específica na lista e seleciona "Criar Exceção"
- [ ] Expande o grupo e seleciona as apertures que deseja exceção
- [ ] Botão "Adicionar Exceção" que pede IDs das apertures (ex: "ID=45, ID=78")
- [ ] Clica na aperture no preview visual e marca como exceção

**Sua resposta:** Escolha acima.

---

**Q16.2 - Exceção aparece onde?**

- [ ] **Como sub-item do grupo**: Ex: "📦 0.5mm (145) → ├─ Padrão (142) └─ Exceções (3)"
- [ ] **Como grupo separado**: Ex: "📦 0.5mm Padrão (142)" + "📦 0.5mm Exceção 1 (1)"
- [ ] **Como lista à parte**: Ex: "📦 0.5mm (142)" + "⚙️ Exceções Individuais (3)"

**Sua resposta:** Escolha acima.

---

### 7.3. Edição Visual

Diagrama: "os agrupamentos devem ser exibidos de uma forma que o usuário possa expandir o grupo e possa fazer uma edição visual."

**Q17.1 - O que é "edição visual"?**

Assinale o que é possível fazer:

- [ ] Ver preview de 3+ aperturas do grupo selecionado
- [ ] Clicar em uma aperture no preview e ver ela destacada no Gerber
- [ ] Ajustar manualmente a janela de inspeção daquela aperture (redimensionar)
- [ ] Ver resultado da análise (OK/PARTIAL/BLOCKED) para aquela aperture com configurações atuais
- [ ] Comparar resultado antes/depois de ajustar configurações
- [ ] Arrastar e soltar janela de inspeção para reposicionar
- [ ] Ver sobreposição de múltiplas janelas (detectar conflitos)

**Sua resposta:** Assinale as operações acima.

---

### 7.4. Feedback Visual

Diagrama: "deve existir feedback visual para mostrar quais aberturas já foram configuradas ou confirmadas."

**Q18.1 - O que significa "configurada" vs "confirmada"?**

- [ ] **Configurada**: Usuário definiu thresholds, mas NÃO validou ainda
- [ ] **Confirmada**: Usuário revisou e aprovou as configurações
- [ ] **Ambos são iguais**: Não há distinção entre configurado e confirmado

**Sua resposta:** Escolha acima.

---

**Q18.2 - Onde aparece esse feedback?**

- [ ] Na árvore de grupos (ícones: ⚪ configurada | ✅ confirmada)
- [ ] No preview visual (cores de borda: cinza configurada | verde confirmada)
- [ ] No Gerber overlay (janelas confirmadas aparecem em verde sobre o Gerber)
- [ ] Todas as acima

**Sua resposta:** Escolha acima.

---

### 7.5. Biblioteca de Configurações

Diagrama: "o usuário pode configurar as edições visuais em uma biblioteca para que sejam carregadas automaticamente com base nas dimensões das aberturas."

**Q19.1 - Como a biblioteca funciona?**

- [ ] Usuário salva configuração atual com nome (ex: "Configuração padrão 0.5mm")
- [ ] Sistema SUGERE configurações baseadas em histórico (ex: "Para 0.5mm, costuma usar OK=90%")
- [ ] Sistema APLICA AUTOMATICAMENTE configurações da biblioteca ao criar novo grupo
- [ ] Biblioteca é GLOBAL (compartilhada entre todos os programas)
- [ ] Biblioteca é POR PROGRAMA (cada programa tem sua própria biblioteca)

**Sua resposta:** Escolha acima.

---

## 8. ABA 7 - CONFIRMAR E SALVAR

### 8.1. Salvamento

Diagrama: "salva as modificações, o nome do programa é o código de barras do seu stencil."

**⚠️ GAP CRÍTICO:**

**Q20.1 - Como o programa é salvo?**

Assumindo **Q1.1 = B** (Programa Genérico):

- [ ] Com nome fornecido na Aba 1 (ex: "Inspeção Padrão 0.5mm")
- [ ] Com nome AUTOMÁTICO (ex: "Inspecao_GerberA_v1.0")
- [ ] Com nome do stencil SE selecionado (ex: "STENCIL-ABC-123_Insp")
- [ ] Outro (descrever):

**Sua resposta:** Escolha acima ou descreva.

---

**Q20.2 - Onde é salvo?**

- [ ] Em arquivo JSON: `data/inspection_programs/nome_do_programa.json`
- [ ] No banco de dados do stencil (SQLite)
- [ ] Na estrutura de pastas do stencil
- [ ] Outro (descrever):

**Sua resposta:** Escolha acima ou descreva.

---

## 9. INTEGRAÇÃO COM CADASTRO DE STENCIL

### 9.1. Fluxo de Cadastro

Diagrama para "cadastrar novo stencil":

1. "abre janela de diálogo para cadastrar as informações do novo stencil"
2. "o usuário cadastra as informações do stencil."
3. "o usuário adiciona uma das rotinas de medição disponíveis."
4. "o usuário adiciona um dos programas de inspeção disponíveis."
5. "salva as modificações, o nome do programa é o código de barras do seu stencil."

**Q21.1 - "Cadastrar novo stencil" acontece em que momento?**

- [ ] Como uma das 3 opções INICIAIS após login (conforme diagrama)
- [ ] Como um diálogo acessível a qualquer momento
- [ ] Durante o fluxo de "Criar Programa de Inspeção" (se stencil ainda não existe)
- [ ] Todas as acima

**Sua resposta:** Escolha acima.

---

**Q21.2 - "Informações do stencil" incluem:**

Assinale TODAS:

- [ ] Código de barras (obrigatório)
- [ ] Descrição
- [ ] Receita associada
- [ ] Data de fabricação
- [ ] Fornecedor
- [ ] Lotes/Part Numbers
- [ ] Arquivo Gerber associado
- [ ] Programas de inspeção associados
- [ ] Rotinas de medição associadas
- [ ] Outros:

**Sua resposta:** Lista os campos acima.

---

### 9.2. Associação Programa ↔ Stencil

**Q22.1 - Como um stencil fica associado a um programa de inspeção?**

- [ ] Durante cadastro do stencil, usuário SELECIONA programas existentes
- [ ] Após criar programa, usuário pode ASSOCIAR a stencils existentes
- [ ] Usuário pode fazer AMBAS as coisas (selecionar durante cadastro OU associar depois)
- [ ] Sistema ASSOCIA AUTOMATICAMENTE baseado no Gerber (se stencil X usa Gerber A, adiciona "Inspeção Gerber A")

**Sua resposta:** Escolha acima.

---

## 10. DIALOG MODAIS

### 10.1. Sub-Diálogos

Alguns passos podem precisar de dialogs modais específicos.

**Q23.1 - Quais dialogs modais são necessários além do dialog principal?**

Assinale TODOS os necessários:

- [ ] **Diálogo de Limpeza de Gerber** (conforme diagrama)
- [ ] **Diálogo de Confirmação** (antes de descartar mudanças)
- [ ] **Diálogo de Progresso** (durante captura de mosaico)
- [ ] **Diálogo de Preview** (mostrar resultado de teste)
- [ ] **Diálogo de Auto-Tuning** (mostrar melhoria de alinhamento)
- [ ] **Diálogo de Exportação** (exportar configurações/biblioteca)
- [ ] **Diálogo de Importação** (importar configurações/biblioteca)

**Sua resposta:** Assinale os dialogs acima.

---

### 10.2. Validação e Bloqueios

**Q24.1 - Se usuário tentar avançar para próxima aba sem completar validações:**

- [ ] Botão "Próximo" fica desabilitado (cinza)
- [ ] Botão "Próximo" mostra mensagem de erro ao ser clicado
- [ ] Aparece mensagem de erro automática (toast/inline) sem clicar em botão
- [ ] Sistema permite avançar, mas mostra alerta visual (ícone de erro na aba)

**Sua resposta:** Escolha acima.

---

## 11. PERGUNTAS ADICIONAIS

### 11.1. Casos de Uso

**Q25.1 - Como lidar com estes cenários?**

**Cenário A:** Usuário criou programa de inspeção, mas depois descobriu que precisa ajustar thresholds de um grupo.
- [ ] Usuário EDITA programa existente (reabre dialog de criação)
- [ ] Usuário cria NOVO programa (versão 2.0)
- [ ] Usuário pode fazer AMBAS as coisas

**Cenário B:** Usuário carregou Gerber errado.
- [ ] Pode VOLTAR para Aba 2 e carregar novo Gerber
- [ ] Pode clicar em "Remover Arquivo" e carregar novo
- [ ] Precisa CANCELAR todo o fluxo e começar do zero

**Cenário C:** Captura de mosaico falhou (FOV 8 de 16 falhou).
- [ ] Sistema continua com FOVs capturadas (8 de 16)
- [ ] Sistema permite recapturar APENAS as FOVs que falharam
- [ ] Sistema pede para recomeçar captura do zero

**Cenário D:** Alinhamento score baixo (60%).
- [ ] Sistema bloqueia avanço e pede para melhorar
- [ ] Sistema alerta, mas permite continuar
- [ ] Sistema sugere auto-tuning automaticamente

**Sua resposta:** Para cada cenário, escolha uma opção.

---

### 11.2. Funcionalidades Opcionais

**Q26.1 - Quais funcionalidades são "nice to have" (opcionais)?**

Assinale as que NÃO são críticas para MVP (Primeira Versão):

- [ ] Biblioteca de configurações
- [ ] Edição visual de janelas (apenas configuração por grupo)
- [ ] Auto-tuning de alinhamento
- [ ] Preview de 3 exemplos por grupo (apenas lista)
- [ ] Undo/Redo de alterações
- [ ] Exportar/importar configurações
- [ ] Histórico de versões de programa
- [ ] Comparação de programas
- [ ] Teste de inspeção "dry run"

**Sua resposta:** Assinale as opcionais acima.

---

### 11.3. Hardware

**Q27.1 - Fluxo de engenharia PRECISA de hardware conectado?**

- [ ] Sim, PLC deve estar conectado para mover a máquina
- [ ] Sim, câmera deve estar conectada para captura
- [ ] Não, pode ser feito offline (usar dados simulados ou capturas anteriores)
- [ ] Parcialmente: CNC precisa estar conectado, mas câmera pode usar imagens salvas

**Sua resposta:** Escolha acima.

---

## 12. PRIORIZAÇÃO

### 12.1. Fases de Implementação

**Q28.1 - Em que ordem as abas devem ser implementadas?**

Ordene por prioridade (1 = mais crítica, 7 = menos crítica):

- [ ] Aba 1: Dados
- [ ] Aba 2: Gerber
- [ ] Aba 3: Fiduciais
- [ ] Aba 4: Posicionamento e Captura
- [ ] Aba 5: Alinhamento
- [ ] Aba 6: Janelas de Inspeção
- [ ] Aba 7: Confirmar e Salvar

**Sua resposta:** Liste a ordem (ex: "1, 2, 3, 4, 5, 6, 7").

---

### 12.2. Complexidade

**Q29.1 - Qual aba é MAIS complexa de implementar?**

- [ ] Aba 2 (Gerber)
- [ ] Aba 4 (Posicionamento e Captura)
- [ ] Aba 5 (Alinhamento)
- [ ] Aba 6 (Janelas de Inspeção)

**Sua resposta:** Escolha acima.

---

**Q29.2 - Qual aba é MENOS complexa?**

- [ ] Aba 1 (Dados)
- [ ] Aba 3 (Fiduciais)
- [ ] Aba 7 (Confirmar)

**Sua resposta:** Escolha acima.

---

## 13. VALIDAÇÃO FINAL

### 13.1. Revisão das Propostas SVG

**Q30.1 - Após responder este questionário:**

- [ ] As propostas SVG estão CORRETAS e podem ser usadas como estão
- [ ] As propostas SVG precisam de AJUSTES (especificar quais)
- [ ] As propostas SVG precisam ser REFEITAS (especificar quais abas)

**Sua resposta:** Escolha acima e adicione comentários se necessário.

---

## 📊 INSTRUÇÕES PARA RESPOSTA

### Como Responder

1. **Salve este questionário** como um arquivo markdown
2. **Responda marcando com [X]** as opções escolhidas
3. **Para questões abertas**, edite o texto e adicione suas respostas
4. **Se houver dúvidas**, adicione comentários entre parênteses `(exemplo: assim...)`
5. **Se faltar alguma opção**, adicione "Outro:" e descreva
6. **Revise suas respostas** antes de enviar

### Prazo

- Responder em até 2 dias úteis
- Quanto mais detalhadas as respostas, menos ambiguidades na implementação
- Dúvidas serão esclarecidas em reunião de follow-up

### Entrega

- Enviar questionário respondido por:
  - Email (preferencial)
  - Slack/Teams
  - Reunião presencial com apresentação

---

**Autor:** Claude Code (Sonnet 4.5)
**Data:** 2026-01-09
**Versão:** 1.0
**Total de Questões:** 30 questões organizadas em 13 seções
