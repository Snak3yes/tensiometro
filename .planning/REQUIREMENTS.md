# Requirements

## Regras praticas do projeto

- Preservar funcionamento sem hardware conectado sempre que possivel.
- Nao sobrescrever configuracoes locais sensiveis sem pedido explicito.
- Nao criar `build/` ou `dist/` dentro do worktree.
- Usar `resources/app_icon.ico` e `resources/app_icon.png` no primeiro build de aplicacao.
- Consultar `MAPA.txt` antes de qualquer alteracao relacionada ao PLC.
- Commits devem iniciar com prefixos como `Feat:`, `Fix:`, `Refactor:`, `Docs:`, `Test:`, `Style:` ou `Chore:`.

## Regras recentes de integracao

- O payload externo de tensao deve incluir `aprovado`.
- O payload externo de tensao deve enviar `nmlinha` como `null`.
- Medicoes NOK tambem sao elegiveis para envio externo, com `aprovado: false`.
- Medicoes sem pontos nao devem ser enviadas.

