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
- A consulta de stencil deve usar o endpoint final `147.1.0.100`.
- O envio final de aprovado/reprovado deve permanecer configuravel e pode ser desabilitado por ADMIN.
- Quando o envio estiver desabilitado, o dialog de configuracao nao deve exigir URL valida.
- Autenticacao por DRT e envio externo devem usar homologacao `147.1.0.85` enquanto nao houver novo endpoint confirmado.

## Regras recentes de medicao

- Leituras `0.00` do tensiometro nao devem ser aceitas como medida valida.
- Se a leitura continuar `0.00` apos tentativas, o sistema deve subir/descer Z e retestar o ponto uma vez.
- Se o reteste automatico tambem retornar `0.00`, a medicao deve falhar com erro explicito.
- A calibracao automatica deve terminar com o equipamento em home.
