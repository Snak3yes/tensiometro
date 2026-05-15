# Roadmap

## Proximos passos imediatos

1. Decidir se as alteracoes abertas no worktree pertencem ao mesmo pacote de entrega ou devem ser separadas.
2. Rodar os testes unitarios focados antes de qualquer commit.
3. Criar um milestone no GSD quando houver uma especificacao clara para o proximo ciclo.
4. Confirmar se `.planning/` deve ser mantido como snapshot manual ou migrado para o fluxo `.gsd/`.

## Verificacoes recomendadas antes de finalizar entrega

- Revisar alteracoes em `config/aoi_config.json` para separar dados locais de mudancas de produto.
- Confirmar que payloads externos continuam aceitos pelo servidor de teste.
- Validar textos PT-BR alterados para evitar mojibake.
- Verificar se `.bg-shell/` deve ser ignorado, removido ou mantido fora do controle de versao.

