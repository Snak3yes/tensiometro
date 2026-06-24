# Planning Snapshot

Snapshot atualizado em 2026-06-24 para preservar o estado atual do ambiente,
das integracoes, da configuracao de endpoints pela interface e do build entregue.

Esta pasta usa o nome legado `.planning` solicitado para consulta humana. A
instalacao atual do GSD CLI neste ambiente usa `.gsd/` como runtime canonico.

Arquivos principais:

- `PROJECT.md`: resumo operacional do projeto.
- `STATE.md`: estado atual do workspace, Git e GSD.
- `RECENT_CHANGES.md`: ultimas alteracoes conhecidas e pontos de atencao.
- `ENVIRONMENT.md`: dados do ambiente local.
- `ROADMAP.md`: proximos passos sugeridos.
- `REQUIREMENTS.md`: requisitos e restricoes praticas do projeto.

## Snapshot atual

- Branch: `frobert/ajuste_rotina_medicao`
- Consulta de stencil no SFCS final: `147.1.0.100`
- Consulta de stencil agora tem endpoint configuravel pela interface ADMIN.
- Consulta de stencil permanece sempre ativa.
- Envio/autenticacao seguem configurados em homologacao `147.1.0.85` no arquivo de configuracao atual.
- Build externo mais recente: `..\tensiometro_build_20260617_config_atual`
