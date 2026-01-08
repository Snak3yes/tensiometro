# Questionário - Fluxo de Usuário Tensiômetro

**Data:** 2026-01-07
**Objetivo:** Mapear completamente o fluxo de uso do operador para criar documentação de UX/UI
**Status:** 📝 Em preenchimento

---

## INSTRUÇÕES

Por favor, responda a cada pergunta o mais detalhadamente possível.

- **Respostas completas** ajudam a evitar ter que voltar e esclarecer depois
- Se **não souber** ou **não se aplicar**, coloque "N/A" ou "Não definido ainda"
- Se tiver **dúvidas** sobre alguma pergunta, marque com `❓` e podemos conversar
- Pode responder **direto neste arquivo**, editando abaixo de cada pergunta

---

## 1. TELA INICIAL & TREEVIEW

### 1.1 Estado Inicial

**Q1:** Ao abrir a aplicação, essa TreeView é a **primeira coisa** que o usuário vê? Ou ele passa por alguma tela antes?

<font color="gray">*Resposta:*</font> podemos ter um splash de entrada na aplicação e com certeza vamos ter um login de acesso para definir se o usuário é operador ou engenharia, isso define qual tela vai ser exibida.

**Q2:** Onde essa tela fica na estrutura atual? É uma tab nova? Uma janela modal? Uma tela separada?

<font color="gray">*Resposta:*</font> uma tab nova, vamos ocultar as outras tabs e outros recursos dependendo do nivel de privilégio do usuário logado.

**Q3:** E se **não houver programas** cadastrados? Mostra lista vazia, mensagem de "nenhum programa", ou formulário para criar o primeiro?

<font color="gray">*Resposta:*</font> mostrar mensagem de nenhum programa e lista vazia.

### 1.2 Informações na TreeView

**Q4:** A TreeView mostra **apenas o código do stencil**? Ou mostra mais informações (ex: data da última medição, último status OK/NOK, descrição)?

<font color="gray">*Resposta:*</font> podemos ter um campo onde são exibidas mais informações sobre o stencil selecionado, o que é visualizado na treeview é apenas o nome do programa, mas podemos mostrar outros detalhes como ultima medição, histórico de medições, nome do modelo do stencil, fabricante, etc.

**Q5:** Tem **ordenação**? Ex: por código, por data da última medição, por status?

<font color="gray">*Resposta:*</font> podemos sim adicionar tipos de ordenação.

**Q6:** Tem **filtro** além da busca? Ex: mostrar apenas stencils com medição recente, apenas reprovados?

<font color="gray">*Resposta:*</font> sim.

### 1.3 Busca & Código de Barras

**Q7:** O campo de busca é **incremental** (filtra enquanto digita) ou só busca ao pressionar Enter?

<font color="gray">*Resposta:*</font> sim, filtra enquanto digita.

**Q8:** Quando o usuário lê o **código de barras**, como o sistema sabe que terminou de ler? Enter automático? Timeout?

<font color="gray">*Resposta:*</font> enter automático do leitor.

**Q9:** E se o código de barras **não for encontrado** na lista? O que acontece? Mensagem de erro? Opção de criar novo programa?

<font color="gray">*Resposta:*</font> apenas mensagem de programa não encontrado.

---

## 2. CONFIRMAÇÃO DE POSICIONAMENTO

### 2.1 Validação

**Q10:** A mensagem pede para confirmar que está posicionado, mas o **sistema valida** isso de alguma forma? Ex: lê código de barras do stencil físico para garantir que é o mesmo código?

<font color="gray">*Resposta:*</font> esse ponto vai ser discutido com o cliente. isso pode permitir que o usuário burle o sistema se não for bem amarrado.

**Q11:** Como o usuário **sabe qual é o stencil correto**? O código está gravado fisicamente no stencil?

<font color="gray">*Resposta:*</font> sim, existe um código de barras único em cada stencil.

**Q12:** E se o usuário **errar o stencil** (ex: selecionou ABC-123 mas posicionou XYZ-456)? O sistema detecta ou confia na confirmação?

<font color="gray">*Resposta:*</font> será discutido com o cliente esse ponto.

### 2.2 Cancelamento

**Q13:** Depois de confirmar que está posicionado, o usuário pode **cancelar** se percebeu que errou? Ou já passou o ponto sem volta?

<font color="gray">*Resposta:*</font> vamos colocar um botão para cancelar a operação e monitorar o emergency stop para cancelamento automático caso pressionado.

**Q14:** A mensagem de confirmação tem botão **"Cancelar"** ou só "OK"?

<font color="gray">*Resposta:*</font> deve ter as opções confirmar e cancelar.

---

## 3. ESCOLHA DO MODO

### 3.1 Critérios de Decisão

**Q15:** Como o usuário **sabe qual modo escolher**? É decisão dele baseada em conhecimento ou o sistema sugere?

<font color="gray">*Resposta:*</font> a decisão é baseada no conhecimento do operador treinado. mas vou levar essa questão ao cliente tambem pois talvez ele queira 'obrigar' o usuário a realizar ambas as medições dentro de algum periodo e o sistema pode monitorar isso e sugerir ou forçar dependendo do periodo.

**Q16:** Existe algum **critério padrão**? Ex: stencils novos sempre inspecionar, stencils recém-limpados apenas medir tensão?

<font color="gray">*Resposta:*</font> existe critério padrão e isso será levado ao cliente.

**Q17:** O **histórico influencia** a escolha? Ex: último NOK → sugerir inspeção completa?

<font color="gray">*Resposta:*</font> validar com o cliente

### 3.2 Configuração por Stencil

**Q18:** Cada **programa/stencil tem um modo padrão** salvo? Ou o usuário escolhe toda vez?

<font color="gray">*Resposta:*</font> o usuário escolhe toda vez.

**Q19:** Pode **configurar** que o Stencil ABC sempre use "Ambos" e o XYZ sempre use "Apenas Tensão"?

<font color="gray">*Resposta:*</font> podemos colocar essa configuração para a engenharia, ela pode definir nas configurações do programa e quando exibido ao usuário operador as outras opções ficam desabilitadas e fica habilitada apenas a opção que a engenharia definiu.

### 3.3 Mudança Durante Execução

**Q20:** Depois de escolher um modo e começar execução, o usuário pode **mudar de ideia** e pausar para trocar de modo?

<font color="gray">*Resposta:*</font> pausar não, pode cancelar e recomeçar, a inspeção/medição que não for concluída não é registrada.

**Q21:** Se escolher "Apenas Tensão" e depois ver que precisa inspecionar visualmente, tem como **adicionar inspeção** sem recomeçar tudo?

<font color="gray">*Resposta:*</font> não.

---

## 4. EXECUÇÃO AUTOMÁTICA

### 4.1 Feedback Visual

**Q22:** Enquanto a máquina executa, o que o usuário vê na tela? **Barra de progresso**? Mensagem "Medindo ponto 3/25"?

<font color="gray">*Resposta:*</font> ambos, barra e fração.

**Q23:** Tem **tempo estimado**? Ex: "Tempo restante: ~3 minutos"

<font color="gray">*Resposta:*</font> sim.

**Q24:** Mostra **valores em tempo real**? Ex: "Tensão atual: 32.5 N/cm" conforme mede?

<font color="gray">*Resposta:*</font> sim, vamos colocar animações para melhorar a experiência do usuário.

### 4.2 Controle de Execução

**Q25:** O usuário pode **pausar** a execução? Ex: parar para verificar algo, depois continuar?

<font color="gray">*Resposta:*</font> não vamos dar a opção de pausar, apenas de parar.

**Q26:** Pode **cancelar** no meio? O que acontece com os dados já coletados?

<font color="gray">*Resposta:*</font> os dados coletados serão descartados e a medição interrompida não entra para o histórico.

**Q27:** Pode **pular** um ponto? Ex: ponto 5 está inacessível, pular para o 6?

<font color="gray">*Resposta:*</font> não.

### 4.3 Tratamento de Erros

**Q28:** E se o **PLC desconectar** durante execução? O sistema avisa? Para tudo?

<font color="gray">*Resposta:*</font> sim, para tudo e exibe mensagem de erro 'clp desconectado'.

**Q29:** E se o **tensômetro falhar** em um ponto (valor 0 ou erro)? Continua ou para?

<font color="gray">*Resposta:*</font> se a medição for zero a operação deve parar e deve ser solicitado ao usuário que confirme a presença do stencil.

**Q30:** E se a **câmera não capturar** imagem? Tenta de novo ou falha?

<font color="gray">*Resposta:*</font> tenta reconectar a camera uma vez, se o erro persistir cancela a operação e exibe erro 'camera não captura'.

### 4.4 Duração Típica

**Q31:** Quanto tempo **demora tipicamente** uma medição completa? Ex: medição de tensão 5x5 = 25 pontos, quanto tempo?

<font color="gray">*Resposta:*</font> ainda não foi medido, mas cerca de 3~5 minutos.

**Q32:** Isso influencia o design? Ex: se demora 5 minutos, precisa de mais feedback. Se demora 30 segundos, pode ser mais simples.

<font color="gray">*Resposta:*</font> não entendi a pergunta. mas o tempo vai ser diretamente proporcional a quantidade de medições, e está tudo bem em relação a isso.

---

## 5. TELA DE RESULTADOS

### 5.1 Conteúdo Exibido

**Q33:** Que **dados são exatamente mostrados**?
  - Para tensão: todos os 25 pontos? Apenas os reprovados? Média/min/max?
  - Para inspeção: todas as aberturas? Apenas as bloqueadas? Imagens dos defeitos?

<font color="gray">*Resposta:*</font> _______________________________

### 5.2 Status Aprovado/Reprovado

**Q34:** Quem define o **critério de aprovação**? É automático baseado em recipe? O usuário pode ajustar?

<font color="gray">*Resposta:*</font> quem define o critério de aprovação é a engenharia na criação do programa, o usuário vai ter liberdade para fazer julgamentos dos resultados.

**Q35:** Para tensão: é **cada ponto** que tem OK/NOK? Ou uma média global?

<font color="gray">*Resposta:*</font> cada ponto tem OK/NOK.

**Q36:** Para inspeção: é **cada abertura** que tem OK/PARTIAL/BLOCKED? Ou o stencil inteiro é aprovado se X% estiver OK?

<font color="gray">*Resposta:*</font> cada abertura vai ter um aprovado ou reprovado de acordo com as regras de inspeção. Existem **3 status finais possíveis** para o stencil:
1. ✅ **Aprovado Automático** (Verde vibrante): Sistema aprovou sem intervenção do usuário, todos os pontos dentro da especificação.
2. ✅ **Aprovado com Julgamento** (Verde-amarelo): Sistema identificou defeitos, mas usuário julgou como "falhas falsas" (override do sistema), fica registrado no histórico que foi aprovado pelo operador.
3. ❌ **Reprovado** (Vermelho): Sistema identificou defeitos, usuário confirmou como "defeitos reais" e finalizou a operação sem correção.

Se um ponto estiver reprovado o stencil inteiro vai ser reprovado, mas o usuário terá recursos para marcar como aprovado ou corrigir e retestar (ver Q41a-c).

### 5.3 Ações Disponíveis

**Q37:** Na tela de resultados, que **ações o usuário pode fazer**?
  - Salvar no histórico?
  - Gerar PDF?
  - Ver imagens dos defeitos?
  - Comparar com medições anteriores?

<font color="gray">*Resposta:*</font> o salvamento no histórico é automático, a geração do PDF deve ser feita em outro recurso, provavelmente algum botão na barra de menus. teremos uma tela onde serão exibidos os resultados da medição para que o usuário possa confirmar como defeito ou julgar como aprovado (isso define o julgamento como falha falsa e pode ser usado para sugerir melhorias nos parâmetros para a engenharia).

### 5.4 Comparação com Histórico

**Q38:** A tela de resultados mostra **comparação com histórico**? Ex: "Tensão média: 32.5 (última: 30.2, aumento de 7.6%)"

<font color="gray">*Resposta:*</font> esse tipo de análise deve ser feita mas em outra tela. e não deve ser exibido na tela de resultados.

**Q39:** Mostra **tendência**? Ex: gráfico com últimas 5 medições?

<font color="gray">*Resposta:*</font> esse tipo de análise deve ser feita mas em outra tela. e não deve ser exibido na tela de resultados.

---

## 6. ANÁLISE VISUAL HUMANA

### 6.1 O Que é Analisado

**Q40:** Você mencionou que o usuário "realiza sua análise visual e confirma se é defeito ou não". Quais pontos ele analisa?
  - Apenas os que o sistema **classificou como reprovado**?
  - Todos os pontos (mesmo os OK)?
  - Apenas pontos **limítrofes** (ex: tensão 28.5 num min de 29.0)?

<font color="gray">*Resposta:*</font> ele deve analisar apenas os pontos reprovados.

### 6.2 Interface de Confirmação

**Q41:** Como o usuário **confirma se é defeito**? Clica em cada ponto? Seleciona múltiplos? Tem botão "Confirmar todos como defeito"?

<font color="gray">*Resposta:*</font> deve existir uma lista com os defeitos identificados pelo sistema, o usuário deve percorrer todos os defeitos e julgar se é defeito ou não.

**Q42:** Mostra a **imagem do ponto** para ele confirmar? Ex: imagem da abertura bloqueada?

<font color="gray">*Resposta:*</font> para fazer a análise, o sistema vai capturar fotos de todo o stencil, e vai usa-las para fazer seu julgamento interno. caso algum ponto seja considerado defeito, deve ser exibido ao usuário a mesma imagem que foi considerada defeituosa para que ele faça o julgamento final.

**Q43:** Pode **adicionar anotação**? Ex: "Bloqueado por resíduo de pasta"

<font color="gray">*Resposta:*</font> sim, a engenharia vai ter um campo onde pode cadastrar uma lista de defeitos. essa lista vai ser usada para que o usuário possa fazer o julgamento final. pode ser um dropdown que exibe as opções cadastradas pela engenharia para que o operador escolha entre elas. essa classificação pode gerar relatórios mais ricos no futuro.

**Q41a:** Quando o usuário identifica um defeito durante a inspeção, quais ações ele pode tomar para cada ponto?

<font color="gray">*Resposta:*</font> o usuário tem 2 opções para cada defeito identificado:
1. **Aprovar (Falha Falsa)**: Marca o ponto como aprovado (override do sistema), registrando no histórico que foi julgado pelo operador.
2. **Confirmar como Defeito Real**: Marca o ponto como defeito confirmado, mantém na lista de defeitos.

**Q44a:** Ao final da análise, se houver defeitos confirmados, quais opções o usuário tem?

<font color="gray">*Resposta:*</font> se houver defeitos confirmados ao final da análise, o usuário tem 2 opções:
1. **Descartar Inspeção** ⭐ NOVO: NÃO salva no histórico (apenas log de auditoria interno), usuário pode fazer correção necessária e inspecionar novamente do zero. Isso mantém o histórico limpo, sem retrabalhos.
2. **Reprovar Sessão**: Salva no histórico como reprovado, registrando os defeitos confirmados. Usuário pode então fazer nova limpeza e inspecionar em nova sessão.

### 6.3 Resultado da Confirmação

**Q44:** O que acontece se o usuário **discordar do sistema**? Ex: sistema disse "reprovado" mas usuário confirma "não é defeito" - esse ponto passa a ser OK?

<font color="gray">*Resposta:*</font> o usuário tem 2 opções:
1. **Aprovar (Falha Falsa)**: Ponto é considerado OK, mas fica registrado no histórico que foi julgado pelo operador (imagem + classificação + nome do operador).
2. **Confirmar como Defeito Real**: Ponto é mantido como defeito, registrado na lista.

Ao final da análise, se houver defeitos confirmados, usuário escolhe entre:
- **Descartar Inspeção**: Não salva no histórico (apenas log de auditoria), faz correção e inspeciona novamente do zero.
- **Reprovar Sessão**: Salva no histórico como reprovado.

**Q45:** Essa confirmação humana **salva junto com os dados**? Fica registrado que usuário revisou?

<font color="gray">*Resposta:*</font> sim, esse registro vai ser salvo no histórico.

---

## 7. HISTÓRICO

### 7.1 Acesso ao Histórico

**Q46:** Como o usuário **acessa o histórico posteriormente**? Voltando para a TreeView e clicando no stencil? Tem botão "Ver Histórico"?

<font color="gray">*Resposta:*</font> sim, vamos adicionar esse botão ou algo similar caso haja espaço na interface.

**Q47:** O histórico mostra **todas as medições** ou apenas as últimas N? Ex: últimas 10 medições?

<font color="gray">*Resposta:*</font> a princípio deve mostrar apenas as ultimas 10 medições, mas deve guardar todas as medições do ultimo ano. deve existir um recurso para mostrar outros periodos, ultimos 7 dias, 30 dias, 60 dias, 90 dias, 180 dias, 365 dias.

### 7.2 Conteúdo do Histórico

**Q48:** O histórico mostra **quais informações**? Data, status, valores médios, quem operou?

<font color="gray">*Resposta:*</font> data-hora, status (3 opções: Aprovado Automático, Aprovado com Julgamento, Reprovado), valores medidos, operador, resultado, defeitos encontrados vs julgados (quantos foram aprovados como falha falsa vs confirmados como defeito real). não mostra informações de iterações porque inspeções com problemas não são salvas no histórico (são descartadas). 

**Q49:** Pode **clicar numa medição antiga** e ver os detalhes completos (todos os pontos, imagens)?

<font color="gray">*Resposta:*</font> sim, deve existir um botão para isso.

### 7.3 Exportação/Relatórios

**Q50:** Pode **gerar PDF** de medições antigas? Ex: "Quero relatório da medição de 15/12/2025"

<font color="gray">*Resposta:*</font> sim, deve existir um botão para isso.

**Q51:** Pode **exportar dados** para Excel/CSV para análise externa?

<font color="gray">*Resposta:*</font> sim, deve existir um botão para isso.

---

## 8. FLUXOS ALTERNATIVOS & EXCEÇÕES

### 8.1 Criação de Novo Programa

**Q52:** Se o usuário escanear um código de barras **não cadastrado**, o que acontece? Sistema oferece cadastrar? Ou exige ir em outra tela para cadastrar primeiro?

<font color="gray">*Resposta:*</font> apenas informa ao usuário que oStencil não foi cadastrado, pode sugerir que informe a engenharia para que o cadastre, cadastro é equivalente a criação de um programa para esse stencil.

### 8.2 Edição de Parâmetros

**Q53:** Antes de começar execução, o usuário pode **ajustar parâmetros**? Ex: mudar grid de 5x5 para 3x3? Mudar limites de tensão?

<font color="gray">*Resposta:*</font> o usuário operador não tem acesso a esse tipo de modificação, apenas a engenharia pode fazer isso.

**Q54:** Esses ajustes **salvam no programa** ou são válidos apenas para essa medição?

<font color="gray">*Resposta:*</font> não deve haver a possibilidade de fazer uma modificação temporaria nem para a engenharia, o usuário operado define o comportamento do programa e salva, o usuário operador apenas seleciona e executa o que foi predeterminado pela engenharia para aquele stencil.

### 8.3 Recomeço

**Q55:** Se a execução **falhar no meio** (ex: queda de energia), ao reiniciar, o usuário pode **continuar de onde parou** ou precisa recomeçar do zero?

<font color="gray">*Resposta:*</font> 

### 8.4 Troca de Operador

**Q56:** Se um operador começa uma medição e outro **termina**, isso fica registrado? Tem login de operador?

<font color="gray">*Resposta:*</font> não é possível logar/deslogar no meio de uma inspeção. o que pode acontecer, um operador inicia uma inspeção, chega outro operado, cancela a inspeção atual, os dados são descartados, o novo operador desloga e loga com o seu login, e inicia uma nova inspeção.

---

## 9. HARDWARE & INTEGRAÇÃO

### 9.1 Validação de Hardware

**Q57:** Antes de começar execução, o sistema **verifica se hardware está conectado**? Ex: PLC OK? Tensiômetro OK? Câmera OK?

<font color="gray">*Resposta:*</font> sim, o sistema deve verificar se o hardware está conectado e funcionando corretamente. caso algo não esteja funcionando corretamente exibe erro e bloqueia a execução.

**Q58:** Se algum hardware **não estiver conectado**, o que acontece? Bloqueia execução? Avisa mas permite?

<font color="gray">*Resposta:*</font> sim, o sistema deve verificar se o hardware está conectado e funcionando corretamente. caso algo não esteja funcionando corretamente exibe erro e bloqueia a execução.

### 9.2 Leitura de Código de Barras do Stencil Físico

**Q59:** O stencil físico tem **código de barras gravado**? Onde? No corpo? Na plaquinha?

<font color="gray">*Resposta:*</font> existe uma placa de identificação no stencil, essa placa exibe os dados do stencil e possui um código de barras, na criação do programa as informações do stencil serão associadas a esse código de barras.

**Q60:** O sistema **lê esse código** para validar que é o mesmo código selecionado na TreeView?

<font color="gray">*Resposta:*</font> não, a leitura do código de barras é mais um atalho para selecionar o programa correto.

---

## 10. PÓS-PROCESSO

### 10.1 Ações Após Salvar

**Q61:** Depois que os resultados são salvos no histórico, **o que acontece**? Volta para a TreeView? Fica na tela de resultados?

<font color="gray">*Resposta:*</font> retorna para a tela de TreeView. que é a tela inicial.

**Q62:** Pode **iniciar nova medição do mesmo stencil** sem voltar para a TreeView? Ex: botão "Medir Novamente"?

<font color="gray">*Resposta:*</font> não, para realizar uma nova medição do mesmo stencil é necessário voltar para a tela de TreeView e selecionar o stencil novamente.

### 10.2 Integração com Outros Sistemas

**Q63:** Os resultados **sincronizam** com algum sistema externo? MES/ERP? Ou ficam apenas local?

<font color="gray">*Resposta:*</font> os resultados ficam guardados localmente mas é gerado um arquivo json mais simples e específico que é enviado para uma API, deve existir uma configuração no sistema onde o usuário habilita ou desabilita do envio para a API e define a URL da API.

**Q64:** Gera algum **alerta** se o stencil for reprovado? Ex: envia email, mostra aviso em outro sistema?

<font color="gray">*Resposta:*</font> não por enquanto mas essa ideia vai ser levada ao cliente para que decida se vamos fazer algo nessa linha.

---

## ESPAÇO PARA NOTAS ADICIONAIS

Use este espaço para adicionar qualquer informação que não foi coberta pelas perguntas:

<font color="gray">
*
*
*
*
</font>

---

## CHECKLIST DE REVISÃO

Após responder, use este checklist para verificar se respondeu tudo:

- [v] Seção 1 - Tela Inicial & TreeView (9 perguntas)
- [v] Seção 2 - Confirmação de Posicionamento (5 perguntas)
- [v] Seção 3 - Escolha do Modo (7 perguntas)
- [v] Seção 4 - Execução Automática (11 perguntas)
- [v] Seção 5 - Tela de Resultados (7 perguntas)
- [v] Seção 6 - Análise Visual Humana (6 perguntas)
- [v] Seção 7 - Histórico (6 perguntas)
- [v] Seção 8 - Fluxos Alternativos & Exceções (5 perguntas)
- [v] Seção 9 - Hardware & Integração (4 perguntas)
- [v] Seção 10 - Pós-Processo (4 perguntas)

**Total:** 64 perguntas

---

**Documento criado em:** 2026-01-07
**Versão:** 1.0
**Próxima etapa:** Após respostas, criar documento de fluxo de uso com wireframes e árvores de decisão
