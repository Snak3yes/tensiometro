# Recent Changes

## Integracao externa de tensao

- Foi enviado um teste virtual aprovado para o stencil `75B01A849403741`.
- Endpoint usado: `http://147.1.0.100:3075/sfcs-print/stencil/stencil_tensiometro`
- Resposta do envio: HTTP `201`
- `idstencilTensiometro`: `227`
- Payload salvo em `tension_routines/integration_payloads/external_tension_payload_75B01A849403741_20260513_160821_446900.json`
- Log salvo em `tension_routines/integration_send_logs/tension_send_attempts_20260513.jsonl`

## Campo de linha no payload externo

- `consumo_lib/services/tension_external_payload_service.py` foi ajustado para enviar sempre `"nmlinha": null`.
- O parametro `line_name` continua aceito na assinatura para compatibilidade das chamadas atuais.
- Foi adicionado teste em `tests/unit/test_stencil_code_normalization.py` garantindo que `nmlinha` seja `None` mesmo quando uma linha for informada.

## GSD

- GSD CLI global detectado em `C:\Users\FelipeRobert-Digiboa\AppData\Roaming\npm\gsd.ps1`.
- Versao instalada: `2.82.0`.
- Projeto inicializado com `.gsd/`.
- `.gsd/PREFERENCES.md` criado com `unique_milestone_ids: true`.
- `.gitignore` atualizado para ignorar runtime local do GSD, como `gsd.db`, `runtime/`, logs e reports.

## Atencao

- O worktree ja tinha varias alteracoes abertas antes deste snapshot.
- Nao reverter alteracoes existentes sem confirmacao explicita.
- `.bg-shell/` apareceu como nao rastreado e nao foi inspecionado nem alterado neste snapshot.

