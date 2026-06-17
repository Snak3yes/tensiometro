# Recent Changes

## Build atual

- Em 2026-06-17 foi gerado novo pacote externo com o programa e config atuais:
  `..\tensiometro_build_20260617_config_atual`.
- O build foi validado por existencia do executavel e conferencia do `config/aoi_config.json`
  copiado para o pacote.

## Integracao SFCS

- Consulta de dados do stencil usa o servidor final `147.1.0.100`:
  `http://147.1.0.100:3075/sfcs-print/stencil/{codigo_barras}`.
- Envio de resultado de tensao permanece no servidor de homologacao `147.1.0.85`:
  `http://147.1.0.85:3075/sfcs-print/stencil/stencil_tensiometro`.
- Consulta de usuario/DRT tambem usa homologacao `147.1.0.85`.
- O dialog admin de integracao agora permite ativar/desativar o envio final e aceita URL vazia quando o envio esta desabilitado.

## Simulacao com stencil real

- Codigo `32B01A642723416` foi consultado com sucesso no endpoint final.
- Resposta incluiu `idstencil=9`, grid `3x3`, status `DISPONIVEL` e descricao `S145IKB (i3) MB`.
- O grid `3x3` foi resolvido para o padrao local `Teste1_V14_V5`.
- A medicao simulada aprovou 9 pontos.
- O envio real para a rota de homologacao configurada retornou HTTP 404.
- Com envio desabilitado em memoria, a simulacao concluiu e pulou o POST final.

## Medicao, relatorio e calibracao

- Leituras `0.00` do tensiometro agora passam por retentativa e reteste fisico do ponto antes de falhar.
- Relatorio automatico de tensao e acionado apos salvar medicao quando a opcao estiver habilitada.
- Pastas padrao de relatorio foram ajustadas para nomes PT-BR.
- Fluxo de calibracao automatica liga e zera o medidor apos home inicial e retorna para home no final.
