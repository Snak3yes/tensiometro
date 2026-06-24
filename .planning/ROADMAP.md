# Roadmap

## Proximos passos imediatos

1. Confirmar com o time SFCS qual servidor deve ficar como padrao definitivo para envio de aprovado/reprovado, ja que o usuario informou que `147.1.0.100` funcionou e `147.1.0.85` retornou HTTP 404.
2. Validar em campo a nova tela `Sistema > Endpoint de Consulta de Stencil...` com usuario ADMIN.
3. Gerar novo build quando a configuracao final dos servidores estiver consolidada.
4. Rodar o conjunto focado de testes antes de cada novo commit de integracao/medicao.
5. Confirmar se o endpoint de autenticacao DRT deve continuar em homologacao `147.1.0.85`.
6. Criar um milestone no GSD quando houver uma especificacao clara para o proximo ciclo.
7. Manter `.planning/` como snapshot manual enquanto o usuario pedir esse formato.

## Verificacoes recomendadas antes de finalizar entrega

- Revisar alteracoes em `config/aoi_config.json` para separar dados locais de mudancas de produto.
- Confirmar que payloads externos continuam aceitos pelo servidor escolhido.
- Validar textos PT-BR alterados para evitar mojibake.
- Quando gerar build, confirmar que a saida continua fora do worktree.
