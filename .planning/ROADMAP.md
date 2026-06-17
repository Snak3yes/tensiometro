# Roadmap

## Proximos passos imediatos

1. Confirmar com o time SFCS se a rota de envio em `147.1.0.85` deve existir como `/sfcs-print/stencil/stencil_tensiometro`, pois o POST real retornou HTTP 404.
2. Rodar o conjunto focado de testes antes de cada novo commit de integracao/medicao.
3. Confirmar se o endpoint de autenticacao DRT deve continuar em homologacao `147.1.0.85`.
4. Criar um milestone no GSD quando houver uma especificacao clara para o proximo ciclo.
5. Manter `.planning/` como snapshot manual enquanto o usuario pedir esse formato.

## Verificacoes recomendadas antes de finalizar entrega

- Revisar alteracoes em `config/aoi_config.json` para separar dados locais de mudancas de produto.
- Confirmar que payloads externos continuam aceitos pelo servidor de teste.
- Validar textos PT-BR alterados para evitar mojibake.
- Quando gerar build, confirmar que a saida continua fora do worktree.
