# Questionário: Fluxo de Engenharia - Fase 2 (Gaps Restantes)

**Data:** 2026-01-11
**Objetivo:** Fechar gaps e ambiguidades restantes
**Base:** Questionário anterior (respostas já consolidadas)

---

## 📋 RESPOSTAS JÁ CONSOLIDADAS

Para contexto, estas decisões JÁ ESTÃO DEFINIDAS:

✅ **Q1.1** - Programa é associado a stencil específico (Opção A)
✅ **Q1.3** - Ao cadastrar stencil, seleciona programas de lista existente
✅ **Q2.1** - "Canto" = área de captura do mosaico (não centro dos fiduciais)
✅ **Q3.1** - Dialog único com 7 abas (wizard)
✅ **Q6.1** - Limpeza de Gerber SEMPRE aparece após carregar
✅ **Q7.1** - Sistema NÃO detecta fiduciais automaticamente
✅ **Q9.1** - Exatamente 2 fiduciais (fixo)
✅ **Q10.1** - Ordem: Mover fiduciais → Definir pontos → Definir cantos → Capturar
✅ **Q11.1** - Grid automático (baseado em tamanho do Gerber)
✅ **Q11.2** - 3 tentativas automáticas, depois pergunta usuário
✅ **Q12.1** - "Definir ponto" = salva coordenadas E captura template

---

## 🔥 GAP 1: Campos da Aba 1

### P1. Quais campos EXISTEM na Aba 1?

Considerando que programa é associado a stencil específico (resposta consolidada), marque TODOS os campos que aparecem na primeira aba:

- [x] **Nome do Programa** (ex: "Inspeção STENCIL-ABC-123")
- [x] **Código do Stencil** (ex: "STENCIL-ABC-123") - obrigatório
- [x] **Descrição** (opcional, texto livre)
- [x] **Versão** (ex: "v1.0")
- [x] **Data de Criação** (automático, somente leitura)
- [ ] **Receita Base** (dropdown de receitas existentes)
- [ ] **Comentários/Notas** (opcional)
- [ ] **Tag/Etiqueta** (ex: "Produção", "Protótipo")
- [ ] Outro:

**Sua resposta:** Marque acima.

---

### P2. Campo "Receita Base" é obrigatório?

- [ ] **Sim** - Usuário DEVE selecionar uma receita existente
- [ ] **Não** - Campo opcional, programa pode não ter receita associada
- [ ] **Parcial** - Sistema sugere receita baseada em histórico, mas usuário pode alterar

**Sua resposta:** Escolha acima.

---

## 🔥 GAP 2: Limpeza de Gerber (Aba 2)

### P3. Como funciona a limpeza EXATAMENTE?

Considere sua resposta anterior: "usuário seleciona partes que não são aberturas e remove, seleção por clique ou área, exibição vetorial com zoom/pan."

**Quais operações são permitidas?** Marque TODAS:

- [x] **Remover elemento individual** (clique no elemento para remover)
- [x] **Seleção por área** (arrasta retângulo, remove tudo dentro)
- [x] **Seleção múltipla** (ctrl+clique para selecionar vários)
- [x] **Desfazer** (undo última remoção)
- [x] **Refazer** (redo)
- [ ] **Remover por tipo** (ex: "remover todo texto")
- [ ] **Editar propriedades** (ex: mudar dimensão de uma aperture)
- [x] **Zoom in/out** (scroll do mouse)
- [x] **Pan** (clique scroll + arrastar)
- [x] **Ajustar à janela** (botão "Fit")

**Sua resposta:** Marque acima.

---

### P4. Como usuário indica que terminou a limpeza?

- [ ] Botão **"Concluir Limpeza"** / **"Próximo"**
- [ ] Sistema detecta automaticamente (ex: não há mais elementos não-abertura)
- [ ] Ambos acima
- [ ] Outro:

**Sua resposta:** Escolha acima.

---

## 🔥 GAP 3: Fiduciais (Aba 3)

### P5. "Definir ponto" - qual é o fluxo EXATO?

Você respondeu: "usuário move manualmente até posição do fiducial, define posição (XYZ), captura primeira imagem de referência, faz testes de visualização."

**P5.1 - Em que ORDEM isso acontece?**

Numere os passos:

1. [ ] Usuário clica botão "Mover para Fiducial 1"
2. [ ] Sistema move máquina para posição XYZ salva (se existente)
3. [ ] Usuário usa jog/joystick para posicionar manualmente
4. [ ] Usuário clica "Definir Ponto" (salva posição XYZ)
5. [ ] Sistema captura imagem template do fiducial
6. [ ] Sistema mostra preview da imagem capturada
7. [ ] Sistema executa teste de template matching
8. [ ] Usuário aprova/reprova resultado
9. [ ] Repete para Fiducial 2

**Ordem correta:** Liste números em sequência (ex: "1, 3, 4, 5, 6, 7, 8, 9")

---

### P6. "Testes de visualização" - o que são?

Você mencionou: "faz testes de visualização para garantir que o posicionamento usando essa imagem está funcionando corretamente."

**P6.1 - O que o teste faz?**

- [ ] **Template matching**: Sistema tenta encontrar fiducial na imagem atual usando template capturado
- [ ] **Preview**: Sistema mostra resultado simulado do alinhamento
- [ ] **Score**: Sistema calcula porcentagem de correspondência
- [ ] **Verificação manual**: Usuário aprova visualmente se template está bom
- [ ] Outro:

**P6.2 - Como usuário aprova?**

- [ ] Botão **"Aprovar"** / **"Reprovar"**
- [ ] Score > X% = auto-aprova
- [ ] Sistema considera aprovado se captura foi bem-sucedida
- [ ] Outro:

**Sua resposta:** Escolha acima.

---

## 🔥 GAP 4: Definir Cantos (Aba 4)

### P7. Como usuário "define canto"?

Após capturar mosaico, usuário precisa definir a área de captura (canto 1 e canto 2).

**P7.1 - Como é feito?**

- [ ] **Clique no preview** - Usuário clica no mosaico capturado para marcar cantos
- [ ] **Coordenadas manuais** - Usuário digita X1, Y1, X2, Y2
- [ ] **Arrastar retângulo** - Usuário desenha retângulo sobre o mosaico
- [ ] **Automático** - Sistema detecta área útil do Gerber
- [ ] Outro:

**P7.2 - Preview mostra o QUÊ exatamente?**

- [ ] Mosaico montado (todas as FOVs)
- [ ] Gerber overlay sobre mosaico
- [ ] Ambos (toggle entre visões)
- [ ] Outro:

**Sua resposta:** Escolha acima.

---

## 🔥 GAP 5: Captura de Mosaico

### P8. Se FOV falhar após 3 tentativas, o que acontece?

Você respondeu: "Tenta mais duas vezes, se a falha persistir, o sistema deve perguntar ao usuário."

**P8.1 - Quais opções o usuário tem?**

Marque TODAS:

- [ ] **Tentar novamente** (4ª, 5ª tentativa manual)
- [ ] **Pular FOV** (continua sem essa imagem)
- [ ] **Usar imagem anterior** (se houver)
- [ ] **Cancelar captura** (volta e ajusta parâmetros)
- [ ] **Marcar FOV como falha** e continuar
- [ ] Outro:

**P8.2 - Se usuário pular FOV, o sistema:**

- [ ] Continua captura normalmente
- [ ] Adiciona "buraco" no mosaico (região sem imagem)
- [ ] Reajusta grid automaticamente
- [ ] Outro:

**Sua resposta:** Escolha acima.

---

## 🔥 GAP 6: Alinhamento (Aba 5)

### P9. Overlay do Gerber - Opacidade e Interação

**P9.1 - Opacidade do overlay:**

- [ ] Fixa em 50%
- [ ] Ajustável 0-100%
- [ ] Ajustável 30-70%
- [ ] Ajustável por slider, mas inicia em 50%

**P9.2 - Usuário pode arrastar TODO o Gerber?**

Você respondeu que quer: **Drag & Drop do Gerber inteiro** + **Controles manuais** (combinação).

- [ ] **SIM** - Clica em qualquer lugar do overlay e arrasta
- [ ] **NÃO** - Apenas controles manuais (spinboxes translação/rotação/escala)
- [ ] **Ambos** - Pode arrastar E usar controles manuais

**Sua resposta:** Escolha acima.

---

### P10. Auto-tuning - quando aparece?

Você respondeu: "OPCIONAL (botão que usuário pode clicar se quiser melhorar)"

**P10.1 - Botão aparece:**

- [ ] Sempre (mesmo se alinhamento estiver perfeito)
- [ ] Apenas se score < X%
- [ ] Apenas se usuário clicar
- [ ] Sistema sugere: "Deseja melhorar?" se score baixo

**P10.2 - O que auto-tuning faz?**

- [ ] Template matching automático
- [ ] Calcula transformação ótima (translação + rotação + escala)
- [ ] Refina alinhamento já feito (não começa do zero)
- [ ] Outro:

**Sua resposta:** Escolha acima.

---

## 🔥 GAP 7: Janelas de Inspeção (Aba 6)

### P11. Agrupamento - Critério e Hierarquia

Você respondeu: "janelas perfeitamente iguais devem ter suas configurações agrupadas. Mas ainda deve ser possível criar configuração específica para uma abertura."

**P11.1 - Critério para "perfeitamente iguais":**

- [ ] Dimensões EXATAS (ex: 0.5mm = 0.5mm)
- [ ] Dimensões com tolerância (ex: 0.48-0.52mm agrupam como "0.5mm")
- [ ] Dimensões + forma (0.5mm círculo ≠ 0.5mm quadrado)
- [ ] Todas acima

**P11.2 - Como aparece na árvore?**

- [ ] `📦 0.5mm Círculo (142)`
- [ ] `📦 0.5mm Círculo (142) → ├─ Padrão (139) └─ Exceções (3)`
- [ ] `📦 0.5mm Círculo (142) → ├─ Grupo A (139) └─ Individuais (3)`
- [ ] Outro:

**Sua resposta:** Escolha acima.

---

### P12. Exceções - Como criar?

Você marcou múltiplas opções para criar exceção.

**P12.1 - Qual é o método PRINCIPAL?**

Escolha o método principal (os outros podem ser alternativos):

- [ ] **Expandir grupo** - Expande o nó na árvore, marca checkboxes das apertures
- [ ] **Clique no preview** - Clica na aperture na imagem visual, marca como exceção
- [ ] **Botão "Criar Exceção"** - Abre diálogo para selecionar por ID
- [ ] **Arrastar para fora** - Arrasta aperture do grupo para fora

**P12.2 - Apertures em exceção aparecem:**

- [ ] **Como sub-item**: `📦 0.5mm (142) → └─ ⚙️ Exceções (3)`
- [ ] **Como grupo separado**: `📦 0.5mm Padrão (139)` + `📦 0.5mm Exceção 1 (1)`
- [ ] **Mantém no grupo, com ícone diferente**: `⚙️ 0.5mm (exceção)`

**Sua resposta:** Escolha acima.

---

### P13. Feedback Visual - "Configurada" vs "Confirmada"

Você respondeu: "existem valores padrão... usuário pode confirmar ou avançar sem confirmar."

**P13.1 - Ícones na árvore:**

- [ ] `⚪` = padrão aplicado (não confirmado) | `✅` = confirmado pelo usuário
- [ ] `⚙️` = configurado (editado) | `✅` = confirmado
- [ ] `🔵` = padrão | `🟢` = confirmado
- [ ] Sem ícone (apenas texto normal vs negrito)

**P13.2 - No preview visual (imagem):**

- [ ] Borda cinza = padrão | Borda verde = confirmado
- [ ] Sem destaque = padrão | Contorno verde = confirmado
- [ ] Ícone sobreposto (⚙️ ou ✅)
- [ ] Outro:

**Sua resposta:** Escolha acima.

---

### P14. Biblioteca de Configurações

Você respondeu: "biblioteca é gerada automaticamente com base no nome automático da abertura (dimensão + forma). Sistema consulta biblioteca e aplica padrão automaticamente."

**P14.1 - Biblioteca é:**

- [ ] **GLOBAL** - Compartilhada entre todos os programas
- [ ] **POR PROGRAMA** - Cada programa tem sua própria biblioteca
- [ ] **Por stencil** - Cada stencil tem sua biblioteca

**P14.2 - Onde é salva?**

- [ ] `data/inspection_config_library.json` (global)
- [ ] `data/inspection_programs/nome_programa/config_library.json`
- [ ] Dentro do arquivo do programa (`programs/nome_programa.json` inclui biblioteca)
- [ ] Outro:

**Sua resposta:** Escolha acima.

---

## 🔥 GAP 8: Salvamento (Aba 7)

### P15. Nome do arquivo

Considerando que programa é associado a stencil específico:

**P15.1 - Arquivo é salvo como:**

- [ ] `data/inspection_programs/STENCIL-ABC-123_inspecao.json`
- [ ] `data/inspection_programs/Inspecao_STENCIL-ABC-123_v1.0.json`
- [ ] `data/stencils/STENCIL-ABC-123/inspecao.json`
- [ ] `data/stencils/STENCIL-ABC-123/inspecao_v1.0.json`
- [ ] Outro:

**P15.2 - Se usuário editar programa depois, versão:**

- [ ] Sobrescreve arquivo (sem controle de versão)
- [ ] Cria novo arquivo: `..._v2.0.json`
- [ ] Salva histórico no mesmo arquivo
- [ ] Pergunta ao usuário se deseja criar nova versão

**Sua resposta:** Escolha acima.

---

## 🔥 GAP 9: Validação e Navegação

### P16. Se usuário tentar avançar sem completar aba

**P16.1 - Comportamento do botão "Próximo":**

- [ ] Fica desabilitado (cinza) até completar validações
- [ ] Permite clicar, mas mostra mensagem de erro
- [ ] Permite avançar, mas mostra alerta visual (ícone de erro na aba)
- [ ] Mostra mensagem inline (toast/texto) sem bloquear

**P16.2 - Usuário pode voltar para aba anterior?**

- [ ] Sim, pode navegar livremente entre abas
- [ ] Sim, mas precisa completar validação da aba atual antes
- [ ] Não, só pode avançar (voltar bloqueia mudanças já feitas)
- [ ] Pode voltar, mas mudanças são perdidas

**Sua resposta:** Escolha acima.

---

## 🔥 GAP 10: Sub-Diálogos Modais

### P17. Quais diálogos são necessários?

Marque TODOS os necessários além do dialog principal de 7 abas:

- [ ] **Diálogo de Limpeza de Gerber** (é a própria Aba 2, ou sub-dialog?)
- [ ] **Diálogo de Progresso** (barra de progresso durante captura de mosaico)
- [ ] **Diálogo de Confirmação** (antes de descartar mudanças)
- [ ] **Diálogo de Preview** (mostrar resultado de teste de fiducial)
- [ ] **Diálogo de Auto-Tuning** (mostrar before/after)
- [ ] **Diálogo de Exportação** (exportar configurações)
- [ ] **Diálogo de Importação** (importar configurações)
- [ ] **Diálogo de Edição de Exceção** (configurar apertures específicas)
- [ ] **Diálogo de Teste de Inspeção** (dry run)
- [ ] Nenhum (tudo na tela principal)

**Sua resposta:** Marque acima.

---

## 🔥 GAP 11: Hardware e Conectividade

### P18. Fluxo de engenharia PRECISA de hardware?

Você mencionou operações como "mover a head", "capturar imagem", "mover para fiducial".

**P18.1 - Hardware obrigatório:**

- [ ] **Sim** - PLC E câmera devem estar conectados
- [ ] **Parcial** - PLC conectado, mas câmera pode usar imagens salvas
- [ ] **Não** - Pode ser feito 100% offline (simulado)
- [ ] **Híbrido** - Pode criar programa offline, mas precisa hardware para validar

**P18.2 - Se hardware não estiver conectado:**

- [ ] Fluxo é bloqueado (não permite avançar)
- [ ] Permite criar programa, mas avisa que precisa validar depois
- [ ] Modo "simulação" com dados fictícios
- [ ] Outro:

**Sua resposta:** Escolha acima.

---

## 🎯 GAP 12: Priorização de Implementação

### P19. Ordem das abas (1 = mais crítica, 7 = menos)

Numere as abas por ordem de prioridade de implementação:

- [ ] Aba 1: Dados do Programa
- [ ] Aba 2: Carregar Gerber
- [ ] Aba 3: Definir Fiduciais
- [ ] Aba 4: Posicionamento e Captura
- [ ] Aba 5: Alinhamento
- [ ] Aba 6: Janelas de Inspeção
- [ ] Aba 7: Confirmar e Salvar

**Ordem:** Liste números (ex: "1, 2, 3, 4, 5, 6, 7")

---

### P20. Qual aba é MAIS complexa?

- [ ] Aba 2 (Gerber + Limpeza)
- [ ] Aba 4 (Posicionamento + Captura)
- [ ] Aba 5 (Alinhamento + Auto-tuning)
- [ ] Aba 6 (Janelas + Agrupamento + Biblioteca)

**Sua resposta:** Escolha acima.

---

## ✨ ÚLTIMA PERGUNTA

### P21. Validação Final

Após responder este questionário:

- [ ] As especificações estão CLARAS e posso começar prototipagem
- [ ] Ainda tenho DÚVIDAS sobre [especificar qual aba]
- [ ] Precisamos de uma REUNIÃO para discutir [tópico]

**Sua resposta:** Escolha acima e adicione comentários se necessário.

---

## 📊 INSTRUÇÕES

1. **Copie este documento** para seu editor
2. **Responda** marcando `[X]` e editando texto onde necessário
3. **Revise** antes de enviar
4. **Cole sua resposta** completa aqui

**Prazo:** 1-2 dias úteis
**Próximo passo:** Após respostas, criarei **protótipos visuais das telas** antes da implementação.

---

**Autor:** Claude Code (Sonnet 4.5)
**Data:** 2026-01-11
**Versão:** 2.0 (Fase 2 - Gaps Restantes)
**Total de Perguntas:** 21 (focadas em ambiguidades)
