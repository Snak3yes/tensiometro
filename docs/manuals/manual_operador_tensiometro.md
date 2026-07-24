# Manual do Operador - Tensiômetro

**Público-alvo:** operadores de produção treinados para medir tensão de stencils.
**Objetivo após a leitura:** operar a rotina de medição, registrar o resultado correto e saber quando chamar engenharia ou manutenção.
**Atualizado em:** 2026-07-10

## 1. Visão geral

O Tensiômetro é o software usado para controlar a máquina de medição de tensão superficial de stencils. A aplicação movimenta o conjunto CNC, aciona o medidor AS-120N, coleta os valores de tensão e registra o histórico do stencil.

A tela principal é a tela de **Medição de Tensão**. Ela mostra a lista de stencils, filtros de busca, status, últimas medições e um painel resumido de resultados.

## 2. Responsabilidades do operador

O operador deve:

- confirmar que o stencil correto está posicionado na máquina;
- selecionar o stencil correto na lista;
- iniciar a medição somente quando a máquina estiver livre e segura;
- acompanhar o progresso até o fim;
- gerar ou consultar relatórios quando necessário;
- parar a operação em caso de risco, peça fora de posição ou comportamento anormal.

O operador não deve:

- alterar critérios globais de aprovação;
- alterar configurações de CLP, calibração, comunicação ou autenticação;
- criar padrões de medição sem orientação da engenharia;
- ignorar falhas de comunicação, leituras zeradas ou movimentos inesperados.

## 3. Cuidados antes de medir

> Atenção: nunca inicie uma medição se houver risco de colisão, stencil solto, eixo em movimento inesperado ou emergência ativa. Em situação insegura, pare a máquina e chame suporte.

Antes de iniciar uma medição:

1. Verifique se não há objetos soltos na área de movimento.
2. Confirme que o stencil está limpo, apoiado e fixado corretamente.
3. Confirme que o código do stencil corresponde ao item selecionado no software.
4. Verifique se o medidor de tensão está fisicamente posicionado e sem dano aparente.
5. Confirme que a máquina não está em emergência.
6. Se houver mensagem de falha de conexão, chame engenharia ou manutenção antes de continuar.

Em qualquer risco de colisão, movimento incorreto ou peça mal posicionada, use o recurso físico de parada de emergência da máquina.

## 4. Abrindo o sistema

1. Inicie o aplicativo Tensiômetro.
2. Aguarde o carregamento inicial.
3. Faça login quando o sistema solicitar usuário e senha.
4. Verifique se a tela principal abriu com o título de medição de tensão.

Se o sistema estiver configurado com login automático, ele pode abrir direto no perfil padrão. Nesse caso, confirme se o perfil exibido é adequado para a operação.

## 5. Tela principal

A tela principal contém:

- **Busca:** filtra stencils por código ou descrição.
- **Período:** limita a lista por histórico recente.
- **Status:** filtra por condição do stencil.
- **Lista de stencils:** mostra código, descrição, status, tensão média, última medição e ações disponíveis.
- **Medir stencil:** inicia a rotina de medição para o stencil selecionado.
- **Painel de detalhes:** mostra informações e histórico resumido do stencil selecionado.

Para evitar erro de rastreabilidade, sempre selecione o stencil antes de iniciar a medição.

## 6. Conectando a máquina

A conexão principal da máquina é feita pelo menu **Ferramentas > Conexões...**.

Use essa opção quando:

- o sistema informar que o CLP está desconectado;
- a máquina foi reiniciada;
- o cabo de rede foi reconectado;
- a aplicação foi aberta antes da máquina terminar de iniciar.

Após conectar, retorne à tela principal e confirme que não há mensagem de falha de hardware.

## 7. Medindo um stencil

> Atenção: durante a medição, não toque no stencil, no sensor ou em partes móveis. A interferência manual pode invalidar a medição e causar dano mecânico.

Fluxo normal:

1. Posicione e fixe o stencil na máquina.
2. Na tela principal, localize o stencil pela busca ou pela lista.
3. Selecione o stencil correto.
4. Clique em **Medir stencil**.
5. Confirme os dados exibidos na tela de medição.
6. Inicie a rotina.
7. Acompanhe o progresso ponto a ponto.
8. Aguarde a conclusão.
9. Verifique o resultado final.
10. Confirme o salvamento no histórico.

Durante a medição, o sistema movimenta os eixos, posiciona o sensor, aguarda estabilização e registra a leitura. Não mova o stencil e não interfira no sensor durante esse processo.

## 8. Interpretando resultados

Os resultados são classificados conforme critérios globais definidos pela engenharia.

| Estado | Significado | Ação esperada |
| --- | --- | --- |
| OK | Valores dentro da faixa esperada | Registrar e liberar conforme procedimento interno. |
| Alerta | Valores próximos dos limites ou com variação relevante | Seguir procedimento de qualidade e, se necessário, chamar engenharia. |
| NOK/Reprovado | Valores fora dos limites definidos | Não liberar sem tratativa autorizada. |
| Erro | Ponto não medido corretamente, falha de leitura ou comunicação | Verificar condição da máquina e repetir somente após corrigir a causa. |

Quando o resultado for alerta ou reprovado, siga o procedimento interno de qualidade. Não aprove manualmente um stencil fora do critério sem autorização.

## 9. Relatórios

O menu **Relatórios** permite consultar ou gerar documentos de medição:

- **Relatório de Tensão:** gera relatório da medição de tensão.
- **Relatório do Stencil:** gera relatório do histórico do stencil selecionado.
- **Consultar por Período:** consulta medições em uma faixa de datas.
- **Configurações de Relatório:** opção restrita para ajuste de aparência e geração automática.

Quando a geração automática estiver habilitada pela engenharia, o PDF pode ser criado ao fim da medição sem ação manual.

## 10. Rastreabilidade

Use **Ferramentas > Rastreabilidade...** quando precisar consultar ou confirmar informações de identificação do stencil.

A rastreabilidade registra medições associadas ao stencil, operador e horário. Por isso, não execute medições com usuário incorreto ou stencil selecionado incorretamente.

## 11. Quando parar a operação

Pare a operação imediatamente quando ocorrer:

- stencil solto ou fora de posição;
- sensor tocando fora da área correta;
- movimento inesperado dos eixos;
- ruído mecânico anormal;
- leitura repetida igual a zero;
- falha de comunicação com CLP ou medidor;
- acionamento de emergência;
- qualquer risco ao equipamento ou ao operador.

Depois de parar, não reinicie a rotina antes de identificar a causa.

## 12. Problemas comuns

| Sintoma | Ação do operador |
| --- | --- |
| CLP desconectado | Abrir **Ferramentas > Conexões...** e tentar reconectar. Se persistir, chamar manutenção. |
| Medidor sem leitura | Verificar cabo e posição do medidor. Se persistir, chamar engenharia. |
| Leitura zero | Confirmar contato do sensor e presença do stencil. Não aprovar sem validação. |
| Stencil não aparece na lista | Confirmar código. Se não estiver cadastrado, chamar engenharia. |
| Relatório não gerado | Verificar se a medição foi salva. Se persistir, chamar engenharia. |
| Movimento não inicia | Verificar emergência, conexão do CLP e permissões. |
| Software travou | Não desligar a máquina em movimento. Acione parada segura e chame suporte. |

## 13. O que informar ao suporte

Ao chamar engenharia, manutenção ou TI, informe:

- código do stencil;
- usuário logado;
- horário aproximado;
- etapa em que o problema ocorreu;
- mensagem exibida na tela;
- se a máquina estava conectada ao CLP;
- se o medidor estava respondendo;
- se houve parada de emergência.

Essas informações reduzem o tempo de diagnóstico e ajudam a preservar a rastreabilidade.
