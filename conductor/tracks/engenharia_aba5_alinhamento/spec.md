# Especificação da Track: Engineering Wizard Aba 5 - Alinhamento

## Visão Geral
**Track ID:** engenharia_aba5_alinhamento
**Tipo:** Feature
**Prioridade:** High
**Complexidade:** High
**Data de Criação:** 2026-01-13
**Estimativa:** 2-3 dias

## Descrição Detalhada

Implementar o widget de **Alinhamento (Aba 5)** do Engineering Wizard, que permite sobrepor o arquivo Gerber no mosaico capturado do stencil, fornecendo controles manuais para ajuste fino (translação, rotação, escala) e funcionalidade de auto-tuning usando template matching dos fiduciais.

## Contexto e Motivação

### Fluxo do Engineering Wizard
O Engineering Wizard é um sistema de 7 abas para criar programas de inspeção AOI:
1. **Aba 1:** Dados do Programa
2. **Aba 2:** Carregar Gerber
3. **Aba 3:** Definir Fiduciais
4. **Aba 4:** Capturar Mosaico
5. **Aba 5:** Alinhamento ⭐ **ESTA TRACK**
6. **Aba 6:** Janelas de Inspeção
7. **Aba 7:** Confirmar e Salvar

### Problema a Resolver
Após capturar o mosaico do stencil físico, o engenheiro precisa alinhar o arquivo Gerber (design virtual) sobre a imagem capturada. Este alinhamento é crítico para que o sistema de inspeção saiba onde posicionar as janelas de verificação.

O alinhamento manual é trabalhoso e sujeito a erros. O sistema deve oferecer:
- Controles manuais precisos (translação, rotação, escala)
- Auto-tuning automatizado usando template matching
- Feedback visual em tempo real
- Validação do alinhamento

## Objetivos

### Primário
1. Implementar preview interativo com mosaico + Gerber overlay
2. Fornecer controles manuais de transformação (translação X/Y, rotação, escala)
3. Implementar auto-tuning usando template matching dos fiduciais
4. Calcular e exibir score de alinhamento
5. Validar alinhamento (score ≥ 70% OU fiduciais encontrados)
6. Emitir sinais para integração com Engineering Wizard

### Secundário
1. Oferecer feedback visual intuitivo (cores, indicadores)
2. Implementar controles finos (opacidade, drag & move)
3. Suportar zoom e pan para inspeção detalhada
4. Manter desempenho adequado mesmo com Gerbers complexos

## Alcance (Scope)

### INCLUÍDO
✅ Widget `AlignmentWidget` com preview interativo
✅ `AlignmentImageView` customizado com zoom/pan
✅ Controles manuais (translação X/Y, rotação, escala)
✅ Slider de opacidade do overlay (0-100%)
✅ Drag & move do overlay
✅ Auto-tuning com template matching
✅ Score de alinhamento (0-100%) com indicador visual
✅ Validação automática (score ≥ 70% OU fiduciais encontrados)
✅ Reset com confirmação
✅ Signals: `validationChanged(bool)`, `alignmentApplied(dict)`
✅ Testes unitários completos (≥34 testes)
✅ Cobertura de código ≥80%
✅ Documentação de uso

### EXCLUÍDO
❌ Captura de mosaico (Track 4)
❌ Definição de fiduciais (Track 3)
❌ Parse de Gerber (Track 2)
❌ Renderização inicial de Gerber (usar `GerberRenderer` existente)
❌ Salvamento de programa (Track 7)

## Requisitos Funcionais

### RF1. Preview Interativo
**Prioridade:** Alta
**Descrição:** Widget deve exibir mosaico capturado com overlay do Gerber renderizado

**Criterios:**
- [x] Mosaico exibido como background
- [x] Gerber renderizado sobre mosaico com opacidade ajustável
- [x] Transformações aplicadas em tempo real
- [x] Zoom (10%-500%) com scroll do mouse
- [x] Pan com clique do meio ou Ctrl+clique
- [x] Ajuste à janela (fit to view)

### RF2. Controles Manuais
**Prioridade:** Alta
**Descrição:** Controles para ajuste fino do alinhamento

**Criterios:**
- [x] Translação X: spinbox (-1000 a 1000 px, passo 1.0)
- [x] Translação Y: spinbox (-1000 a 1000 px, passo 1.0)
- [x] Rotação: spinbox (-180° a 180°, passo 0.1°)
- [x] Escala: spinbox (0.1 a 10.0, passo 0.01)
- [x] Atualização em tempo real do overlay
- [x] Valores iniciais em 0/0/0°/1.0

### RF3. Controles Finos
**Prioridade:** Média
**Descrição:** Controles adicionais para facilitar ajustes

**Criterios:**
- [x] Slider de opacidade (0-100%)
- [x] Drag & move do overlay (clique e arraste)
- [x] Indicador visual de score (verde/laranja/vermelho)
- [x] Exibição de zoom atual (porcentagem)

### RF4. Auto-Tuning
**Prioridade:** Alta
**Descrição:** Alinhamento automático usando template matching

**Criterios:**
- [x] Buscar fiduciais usando templates capturados
- [x] Calcular transformação ótima (translação + rotação + escala)
- [x] Aplicar transformação nos controles manuais
- [x] Calcular score de matching (média dos fiduciais)
- [x] Tratamento de erros (fiduciais não encontrados)
- [x] Feedback visual ao usuário

### RF5. Score de Alinhamento
**Prioridade:** Alta
**Descrição:** Métrica numérica e visual da qualidade do alinhamento

**Criterios:**
- [x] Score calculado automaticamente (0-100%)
- [x] Estimativa baseada em transformação aplicada
- [x] Indicador visual:
  - Verde (≥90%): Alinhamento excelente
  - Laranja (70-90%): Aceitável
  - Vermelho (<70%): Ruim
- [x] Exibição em porcentagem

### RF6. Validação
**Prioridade:** Alta
**Descrição:** Verificação automática se alinhamento é válido

**Criterios:**
- [x] Critério: score ≥ 70% OU fiduciais encontrados
- [x] Signal `validationChanged(bool)` emitido na mudança
- [x] Botão "Aplicar" habilitado apenas se válido
- [x] Aviso visual se score baixo (<70%)

### RF7. Reset
**Prioridade:** Média
**Descrição:** Voltar ao estado inicial

**Criterios:**
- [x] Volta aos valores iniciais (tx=0, ty=0, angle=0, scale=1)
- [x] Confirmação do usuário antes de resetar
- [x] Preserva dados carregados (mosaico, Gerber, templates)

### RF8. Aplicação
**Prioridade:** Alta
**Descrição:** Coletar dados do alinhamento e emitir sinal

**Criterios:**
- [x] Coleta dados completos (transform, score, fiducials_found)
- [x] Signal `alignmentApplied(dict)` emitido
- [x] Confirmação visual ao usuário
- [x] Aviso se score baixo (<70%)

## Requisitos Não-Funcionais

### RNF1. Performance
- Preview deve atualizar em <100ms com transformações
- Auto-tuning deve completar em <5 segundos
- Zoom/pan devem ser suaves (60 FPS)

### RNF2. Usabilidade
- Interface intuitiva com feedback visual imediato
- Controles agrupados logicamente
- Atalhos de teclado para zoom (scroll), pan (clique do meio)

### RNF3. Confiabilidade
- Tratamento robusto de erros (Gerber inválido, fiduciais não encontrados)
- Valores padrão seguros para todos os controles
- Sem crashes em cenários normais

### RNF4. Manutenibilidade
- Código bem documentado (docstrings)
- Type hints em todos os métodos públicos
- Separação clara de responsabilidades (view, state, controls)

## Requisitos de Testes

### Testes Unitários (34 testes)
- [x] Inicialização (4 testes)
- [x] Carregamento de dados (4 testes)
- [x] Controles de transformação (5 testes)
- [x] Controles finos (2 testes)
- [x] Auto-tuning (3 testes)
- [x] Reset (2 testes)
- [x] Validação (4 testes)
- [x] Aplicação (3 testes)
- [x] Visualização (5 testes)
- [x] Estado (2 testes)

### Cobertura de Código
- [x] Cobertura ≥80% para alignment_widget.py
- [x] Todos os caminhos principais testados
- [x] Tratamento de erros testado

## Dependências

### Dependências de Código
- `aoi_lib.fiducial_alignment.FiducialAligner`: Template matching
- `aoi_lib.gerber_renderer.GerberRenderer`: Renderização de Gerber
- `PyQt6.QtWidgets`: Framework GUI
- `numpy`: Processamento de arrays
- `cv2`: OpenCV para conversões de formato

### Dependências de Dados (entradas)
- **Mosaico Image** (np.ndarray): Imagem BGR capturada na Track 4
- **Gerber Data** (dict):
  ```python
  {
      'parsed': ParsedGerber,
      'fiducial_positions': [(x1, y1), (x2, y2)]  # mm
  }
  ```
- **Fiducial Templates** (list): Templates capturados na Track 3
  ```python
  [
      {
          'name': str,
          'image': np.ndarray,  # 50x50 template
          'position': (x, y)  # posição no mosaico (pixels)
      },
      ...
  ]
  ```

### Dependências de Tracks
- **Track 2 (Gerber):** Fornece gerber_data
- **Track 3 (Fiduciais):** Fornece fiducial_templates
- **Track 4 (Mosaico):** Fornece mosaic_image

## Entregáveis (Deliverables)

### Arquivos de Código
1. `consumo_lib/widgets/engenharia/alignment_widget.py` (1019 linhas)
   - `AlignmentWidget` (widget principal)
   - `AlignmentImageView` (view customizado)
   - `AlignmentState` (dataclass para estado)

2. `tests/unit/widgets/engenharia/test_alignment_widget.py` (633 linhas)
   - 34 testes unitários
   - Fixtures para pytest
   - Mocks para dependências

### Arquivos de Documentação
1. `docs/guides/ALIGNMENT_WIDGET_USAGE.md`
   - Visão geral
   - Instalação
   - Uso básico e avançado
   - API reference
   - Exemplos práticos
   - Solução de problemas

### Metadados
1. `conductor/tracks/engenharia_aba5_alinhamento/spec.md` (este arquivo)
2. `conductor/tracks/engenharia_aba5_alinhamento/plan.md`
3. `conductor/tracks/engenharia_aba5_alinhamento/metadata.json`

## Critérios de Sucesso

- [x] Widget `AlignmentWidget` implementado e funcional
- [x] Preview interativo com zoom/pan funcionando
- [x] Controles manuais operacionais
- [x] Auto-tuning funcionando
- [x] Score calculado e exibido corretamente
- [x] Validação automática funcionando
- [x] Signals emitidos corretamente
- [x] 34/34 testes passando (100%)
- [x] Cobertura de código ≥80%
- [x] Documentação completa
- [x] Integração com Engineering Wizard possível

## Riscos e Mitigações

### Risco 1: Performance na renderização
**Descrição:** Gerbers com muitos apertures podem ser lentos para renderizar
**Probabilidade:** Média
**Impacto:** Alto
**Mitigação:** Cache de renderização, renderizar apenas região visível

### Risco 2: Template matching falhando
**Descrição:** Fiduciais de baixa qualidade podem não ser encontrados
**Probabilidade:** Média
**Impacto:** Alto
**Mitigação:** Validação de qualidade, permitir ajuste manual

### Risco 3: Transformações complexas
**Descrição:** Usuários podem ter dificuldade com rotação + escala
**Probabilidade:** Baixa
**Impacto:** Médio
**Mitigação:** Interface intuitiva, preview em tempo real

## Aprovações

- [x] Especificação aprovada por: Claude Code (Sonnet 4.5)
- [x] Data de aprovação: 2026-01-13
- [x] Implementação concluída: 2026-01-13

---

**Autor:** Claude Code (Sonnet 4.5)
**Data:** 2026-01-13
**Versão:** 1.0
**Status:** ✅ COMPLETO
