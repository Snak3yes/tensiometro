# Manual Técnico de Engenharia - Tensiômetro

**Público-alvo:** time de desenvolvimento, engenharia, manutenção e suporte técnico.
**Objetivo após a leitura:** manter, configurar, diagnosticar e evoluir o sistema sem quebrar a rotina operacional de medição de tensão.
**Atualizado em:** 2026-07-10

## 1. Escopo do sistema

O Tensiômetro é uma aplicação desktop industrial em Python e PyQt6 para medição de tensão superficial de stencils. A versão atual do fluxo principal é centrada na medição de tensão, rastreabilidade, controle de movimento, comunicação com CLP, medidor AS-120N e geração de relatórios.

O sistema deve continuar degradando com segurança quando algum hardware estiver indisponível. Falha de CLP, câmera, porta serial ou medidor deve ser tratada como condição operacional esperada, não como motivo para derrubar a aplicação.

## 2. Componentes principais

O projeto é separado em duas camadas principais:

- **aoi_lib:** domínio, hardware, persistência, cálculo, leitura serial, controle de CLP, rastreabilidade e relatórios.
- **consumo_lib:** interface PyQt6, janelas, diálogos, controladores, coordenadores, serviços, gerenciadores e composição da aplicação.

O ponto de entrada inicializa a aplicação Qt, aplica identidade visual, pré-carrega módulos críticos e abre a janela principal.

## 3. Fluxo de inicialização

Ordem conceitual de boot:

1. Inicialização do processo Python.
2. Pré-carregamento de módulos críticos para reduzir interferência de antivírus na primeira execução.
3. Criação do QApplication.
4. Aplicação de ícone e identidade do aplicativo.
5. Inicialização do sistema de tema.
6. Criação da janela principal.
7. Composição de managers, controllers, coordinators, handlers, facades e serviços.
8. Exibição da tela principal.

Mudanças de inicialização devem preservar essa ordem, especialmente a criação do QApplication e a inicialização do tema antes da construção dos widgets principais.

## 4. Arquitetura de UI

A janela principal ainda funciona como superfície de compatibilidade e orquestração de alto nível. Evite adicionar regra de negócio diretamente nela.

Preferência de localização para novas mudanças:

- regra de domínio e hardware: camada de domínio;
- fluxo entre componentes: coordenadores;
- ações de tela e sinais de UI: controladores;
- composição de dependências: fábricas;
- estado reutilizável e serviços de aplicação: managers e services;
- aparência visual: sistema de UI e tokens.

O sistema usa uma tela unificada de medição de tensão com lista de stencils, filtros, seleção, painel de detalhes e ação de medição.

## 5. Menus e permissões

Menus principais existentes:

- **Login:** troca de usuário e saída.
- **Relatórios:** relatório de tensão, relatório do stencil, consulta por período e configurações.
- **Ferramentas:** rastreabilidade, padrões de medição, critérios de tensão, controle de movimento, monitor CLP, calibração do medidor, calibração CNC, conexões e preferências.
- **Sistema:** autenticação, endpoints de integração, tema, permissões e informações do sistema.

Perfis usuais:

- **operator:** executa a operação diária.
- **engineering:** altera parâmetros técnicos e configurações de processo.
- **quality:** consulta e valida dados conforme política local.
- **admin:** acessa funções administrativas, exclusões autorizadas e integrações restritas.

Novas ações de risco devem respeitar o modelo de permissões existente.

## 6. Medição de tensão

O fluxo de medição usa:

- padrões de medição para definir grade, alturas Z, velocidade, estabilização e pontos;
- serviço de cálculo de grade com percurso em zig-zag;
- thread de medição para manter a UI responsiva;
- leitura serial do medidor AS-120N;
- classificação por critérios globais;
- persistência no histórico do stencil;
- geração opcional de relatório automático;
- payload de integração externa quando configurado.

Parâmetros importantes:

| Parâmetro | Uso | Risco se configurado incorretamente |
| --- | --- | --- |
| Ponto inicial e final da grade | Define a área medida no stencil | Medição fora da região útil ou colisão. |
| Tamanho da grade NxN | Define quantidade de pontos | Tempo de ciclo excessivo ou baixa amostragem. |
| Altura segura de movimento | Altura usada entre pontos | Risco de arrasto ou colisão. |
| Altura de medição | Altura de contato/leitura | Leitura inválida ou dano ao sensor. |
| Tempo de estabilização | Espera antes da leitura | Variação de leitura por vibração ou contato instável. |
| Velocidade de movimento | Feed dos deslocamentos | Perda de precisão, impacto mecânico ou ciclo lento. |
| Porta serial e timeout | Comunicação com AS-120N | Falha de leitura ou demora excessiva. |
| Critérios de tensão | Classificação OK/Alerta/NOK | Aprovação indevida ou reprovação indevida. |

Não altere esses valores em produção sem validar colisão mecânica, repetibilidade, tempo de ciclo e impacto na aprovação de qualidade.

## 7. Hardware

### CLP Delta

> Atenção: alterações de CLP, homing, registradores, memórias, entradas, saídas e movimento devem ser feitas somente com a máquina em condição segura e com referência no mapa técnico local.

A comunicação com o CLP usa Modbus TCP. Antes de alterar endereços, memórias, registradores, homing, movimentação, entradas ou saídas, consulte o mapa local de CLP mantido no repositório.

Regras de manutenção:

- não assumir que um endereço de memória está livre;
- validar qualquer mudança de pulso, velocidade ou limite com a máquina em condição segura;
- registrar alterações de ladder ou endereçamento;
- preservar comandos de parada e estados seguros.

### Medidor AS-120N

O medidor de tensão usa comunicação serial RS-232, tipicamente 2400 baud, 8N1, com comando de requisição e quadro de resposta esperado.

Falhas comuns:

- porta COM incorreta;
- cabo/adaptador sem driver;
- medidor desligado;
- timeout curto demais;
- leitura inválida ou zerada por contato incorreto.

### Câmera

A base do projeto ainda contém integração de câmera e inspeção visual, mas a rotina atual prioriza a medição de tensão. Alterações nessa área devem confirmar se a tela ou fluxo correspondente está ativo na versão em uso.

## 8. Lacunas técnicas declaradas

As informações abaixo não devem ser inventadas no manual sem evidência de campo ou documentação do fabricante:

- diagrama elétrico completo da máquina;
- desenho mecânico com curso útil e limites físicos;
- procedimento formal de calibração rastreável do medidor;
- política oficial de qualidade para liberação de stencils em alerta;
- plano de manutenção preventiva com periodicidade aprovada;
- credenciais reais, tokens, senhas ou endpoints privados de produção.

## 9. Dados e persistência

Dados principais:

- configurações de runtime;
- padrões de medição;
- histórico de stencils;
- sessões de medição de tensão;
- relatórios PDF;
- payloads de integração externa;
- logs operacionais.

Configurações de máquina são específicas do ambiente. Não sobrescreva IP de CLP, calibração, câmera, portas, fatores de conversão ou defaults de autenticação sem solicitação explícita e validação local.

Medições de tensão recentes são persistidas em JSON de sessão e também associadas ao histórico do stencil. Alguns nomes antigos de arquivo podem existir por compatibilidade; trate-os como legado se não forem o caminho primário da versão atual.

## 10. Relatórios e integração

O sistema pode gerar:

- relatório da medição de tensão;
- relatório histórico de stencil;
- consulta por período;
- relatório automático após medição, se habilitado.

A integração externa monta payload com código do stencil, pontos medidos, usuário, linha, status e aprovação. Falha no envio não deve apagar a medição local. A trilha local deve continuar disponível para auditoria.

## 11. Configuração técnica

Áreas de configuração relevantes:

- conexão do CLP;
- autenticação e perfil padrão;
- critérios globais de tensão;
- endpoints de integração;
- relatórios;
- calibração CNC;
- calibração do medidor;
- tema e aparência.

Preferências acessíveis ao operador devem ser mínimas. Configurações que alteram movimento, aprovação, integração ou segurança devem exigir engenharia ou admin.

## 12. Desenvolvimento local

Fluxo básico:

1. Ativar ambiente Python do projeto.
2. Instalar dependências declaradas.
3. Executar a aplicação pelo ponto de entrada principal.
4. Usar hardware real somente em bancada segura.
5. Para testes sem hardware, validar importação, serviços puros, managers e fluxos de UI sem iniciar movimento real.

Sempre considerar que:

- testes automatizados podem não cobrir hardware real;
- CLP e medidor exigem validação física;
- interface PyQt6 pode exigir teste manual;
- mudanças de relatório devem ser validadas abrindo o PDF gerado;
- mudanças de texto em português devem ser revisadas contra mojibake.

## 13. Testes recomendados

Antes de entregar uma mudança:

- executar testes automatizados disponíveis;
- validar importação dos módulos afetados;
- abrir a aplicação quando a mudança tocar UI ou boot;
- testar com hardware desconectado quando a mudança tocar conexão;
- testar com hardware conectado em bancada quando a mudança tocar movimento ou medição;
- gerar relatório quando a mudança tocar dados de medição ou PDF;
- revisar permissões quando a mudança tocar menus, exclusão ou configuração.

Para mudanças de medição, valide pelo menos:

- cálculo da grade;
- ordem dos pontos;
- altura segura de movimento;
- timeout de leitura;
- classificação OK/Alerta/NOK;
- salvamento no histórico;
- geração de relatório;
- comportamento ao interromper a rotina.

## 14. Build e distribuição

Builds e executáveis não devem ser gerados dentro do checkout do repositório. Use a automação de build existente e direcione saídas para pasta irmã ou pai do projeto.

Na primeira geração de aplicação distribuível, use os ativos oficiais de marca do repositório para ícone e logo quando suportado pelo processo de build.

Antes de distribuir:

- confirmar versão/branch correta;
- verificar se configurações locais sensíveis não foram empacotadas indevidamente;
- testar abertura em máquina limpa;
- validar comunicação com CLP e medidor na máquina alvo;
- abrir relatório PDF gerado;
- confirmar que atalhos e menus críticos funcionam.

## 15. Boas práticas para manutenção

- Mantenha regra de negócio fora dos widgets.
- Não aumente a responsabilidade da janela principal sem necessidade.
- Use serviços, managers e coordenadores existentes antes de criar nova arquitetura.
- Preserve comportamento sem hardware.
- Não faça mudanças em endereços de CLP sem consultar o mapa técnico local.
- Não altere critérios globais sem alinhamento com qualidade.
- Não remova compatibilidade de dados legados sem plano de migração.
- Use o sistema de tema e tokens para UI.
- Evite textos sem acentuação quando forem visíveis ao usuário, salvo limitação técnica real.

## 16. Diagnóstico rápido

| Sintoma | Área provável | Verificações |
| --- | --- | --- |
| Aplicação não abre | boot/UI/dependências | ambiente Python, dependências, importações, tema, PyQt6 |
| CLP não conecta | rede/Modbus/configuração | IP, porta, cabo, energia, permissões de rede |
| Movimento não ocorre | CLP/eixo/comando | estado de emergência, homing, endereço, modo do CLP |
| Medidor não responde | serial/AS-120N | porta COM, baudrate, cabo, timeout, alimentação |
| Medição salva sem relatório | configuração de relatório | geração automática, pasta de saída, permissões |
| Stencil não aparece | rastreabilidade/cadastro | origem dos dados, filtros, consulta externa |
| Critério parece incorreto | configuração de qualidade | limites globais e faixa de alerta |
| PDF com texto quebrado | encoding/fonte | strings em UTF-8, fonte, geração do PDF |

## 17. Critérios de aceite para mudanças técnicas

Uma mudança só deve ser considerada pronta quando:

- o comportamento pretendido foi validado no nível adequado;
- erros esperados foram tratados de forma visível e segura;
- dados de medição não são perdidos silenciosamente;
- permissões continuam coerentes;
- textos de UI em português estão legíveis;
- documentação afetada foi atualizada;
- qualquer limitação de teste com hardware foi registrada.
