# Engineering Wizard - Guia do Usuário

**Versão:** 1.0
**Data:** 2026-01-13
**Autor:** Claude Code (Sonnet 4.5)

---

## Índice

1. [Introdução](#introdução)
2. [Conceitos Básicos](#conceitos-básicos)
3. [Fluxo de Trabalho](#fluxo-de-trabalho)
4. [Detalhamento das Abas](#detalhamento-das-abas)
5. [Atalhos de Teclado](#atalhos-de-teclado)
6. [Solução de Problemas](#solução-de-problemas)
7. [Melhores Práticas](#melhores-práticas)

---

## Introdução

O **Engineering Wizard** é uma ferramenta passo-a-passo para criar programas de inspeção de stencil. O wizard guia você através de 7 etapas, desde os dados básicos do programa até a configuração final das janelas de inspeção.

### O que você pode criar:

- **Programas de Inspeção**: Configurações completas para inspeção visual de stencil
- **Recipes**: Configurações compatíveis com o sistema RecipeManager legado
- **Mosaicos**: Imagens compostas de múltiplas capturas da área do stencil
- **Alinhamentos**: Transformações precisas entre Gerber e imagem real

---

## Conceitos Básicos

### Arquivo Gerber

Arquivo no formato **RS-274X** (Extended Gerber) que contém o design vetorial do stencil. Inclui:
- **Apertures**: Aberturas do stencil (círculos, retângulos, obrounds)
- **Dimensões**: Tamanho total do stencil
- **Coordenadas**: Posição de cada elemento

**Exemplo de uso:**
```
Nome: STENCIL-ABC-123.ger
Formato: RS-274X
Tamanho típico: 50 KB - 500 KB
```

### Fiduciais

Marcas de referência usadas para alinhamento. Geralmente são marcas circulares nos cantos do stencil.

**Função:**
- Permitir alinhamento preciso entre design (Gerber) e imagem real
- Corrigir rotação, translação e escala
- Essencial para inspeção precisa

**Requisitos:**
- **Mínimo:** 2 fiduciais
- **Recomendado:** 3-4 fiduciais (para redundância)
- **Tamanho típico:** 1-2 mm de diâmetro

### Mosaico

Imagem composta de múltiplas capturas em grid, cobrindo uma área maior que o campo de visão da câmera.

**Parâmetros:**
- **Grid:** Tamanho (ex: 3x3, 5x5)
- **Sobreposição:** 10-20% entre imagens adjacentes
- **Delay:** 200-500ms entre capturas (para estabilização)

### Janelas de Inspeção

Grupos de aperturas com parâmetros de inspeção comuns.

**Configuração por grupo:**
- **Tipo de aperturas:** Círculos, retângulos, obrounds
- **Threshold OK:** % mínima de pixels claros (ex: 90%)
- **Threshold Partial:** % mínima para aviso (ex: 70%)

---

## Fluxo de Trabalho

```
┌─────────────────────────────────────────────────────────────┐
│                    ENGINEERING WIZARD                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Dados do Programa  →  Nome, código, versão             │
│         ↓                                                   │
│  2. Carregar Gerber    →  Arquivo RS-274X                  │
│         ↓                                                   │
│  3. Definir Fiduciais  →  Capturar 2+ marcas               │
│         ↓                                                   │
│  4. Capturar Mosaico   →  Grid de imagens                  │
│         ↓                                                   │
│  5. Alinhamento        →  Template matching                 │
│         ↓                                                   │
│  6. Janelas de Insp.   →  Grupos e thresholds              │
│         ↓                                                   │
│  7. Confirmar e Salvar →  Revisão e conclusão              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Dependências entre Abas

- **Aba 1:** Sem dependências (ponto de partida)
- **Aba 2:** Requer Aba 1 completa
- **Aba 3:** Requer Aba 2 (Gerber carregado)
- **Aba 4:** Requer Aba 3 (2+ fiduciais capturados)
- **Aba 5:** Requer Aba 4 (mosaico capturado)
- **Aba 6:** Requer Aba 5 (alinhamento concluído)
- **Aba 7:** Requer todas as anteriores completas

---

## Detalhamento das Abas

### Aba 1: Dados do Programa

**Objetivo:** Definir metadados do programa de inspeção.

**Campos:**

| Campo | Descrição | Exemplo | Obrigatório |
|-------|-----------|---------|-------------|
| **Código do Stencil** | Identificador único do stencil | `STENCIL-ABC-123` | Sim |
| **Nome do Programa** | Nome descritivo | `Inspeção Stencil ABC-123` | Sim |
| **Descrição** | Detalhes adicionais | `Primeira inspeção` | Não |
| **Versão** | Controle de versão | `v1.0` | Sim |
| **Criado por** | Nome do operador | `João Silva` | Sim |

**Dicas:**
- Use códigos de stencil padronizados
- Inclua data no nome do programa se criar múltiplas versões
- Use versionamento semântico (v1.0, v1.1, v2.0)

**Validação:**
✓ Todos os campos obrigatórios preenchidos
✓ Código do stencil não vazio
✓ Versão no formato correto

---

### Aba 2: Carregar Gerber

**Objetivo:** Carregar arquivo de design do stencil.

**Passos:**

1. Clique em **"Carregar Arquivo Gerber"**
2. Navegue até o arquivo `.ger` ou `.gtl`
3. Aguarde processamento

**Informações Exibidas:**

- **Nome do arquivo:** `STENCIL-ABC-123.ger`
- **Dimensões:** `400.0 x 300.0 mm`
- **Número de aperturas:** `1,234`
- **Fiduciais detectados:** `2`

**Dicas:**
- Use arquivos no formato RS-274X (Extended Gerber)
- Verifique se as dimensões estão corretas
- Confirme se os fiduciais foram detectados

**Validação:**
✓ Arquivo carregado com sucesso
✓ Dimensões válidas (> 0)
✓ Aperturas detectadas (> 0)

---

### Aba 3: Definir Fiduciais

**Objetivo:** Capturar templates dos fiduciais para alinhamento.

**Passos:**

1. Mova a câmera para o primeiro fiducial
2. Clique em **"Capturar Fiducial"** (ou pressione `F`)
3. Repita para o segundo fiducial
4. (Opcional) Capture fiduciais adicionais para redundância

**Interface:**

- **Preview da câmera:** Mostra imagem em tempo real
- **Lista de fiduciais:** Exibe fiduciais capturados
- **Status:** "0/2 fiduciais capturados" → "2/2 fiduciais capturados ✓"

**Dicas:**
- Use boa iluminação (backlight recomendado)
- Centralize o fiducial no frame
- Garanta que o fiducial está em foco
- Capture fiduciais em cantos opostos do stencil

**Validação:**
✓ Mínimo de 2 fiduciais capturados
✓ Templates com qualidade adequada

---

### Aba 4: Capturar Mosaico

**Objetivo:** Capturar múltiplas imagens em grid para cobrir área de inspeção.

**Parâmetros:**

| Parâmetro | Descrição | Valor Típico |
|-----------|-----------|--------------|
| **Canto 1 (X1, Y1)** | Posição inicial | `0.0, 0.0` mm |
| **Canto 2 (X2, Y2)** | Posição final | `300.0, 200.0` mm |
| **Linhas** | Número de linhas do grid | `3-5` |
| **Colunas** | Número de colunas do grid | `3-5` |
| **Sobreposição** | Sobreposição entre imagens | `10-20%` |
| **Delay** | Tempo de espera entre capturas | `200-500` ms |

**Passos:**

1. Configure a área do mosaico (use dimensões do Gerber)
2. Defina tamanho do grid
3. Clique em **"Capturar Mosaico"** (ou pressione `M`)
4. Aguarde conclusão (progresso indicado na barra)

**Dicas:**
- Comece com grid 3x3 para teste
- Use sobreposição de 10-15% para economia
- Aumente delay se imagens estiverem tremidas
- Dimensões do Gerber são boa referência

**Validação:**
✓ Área definida (X1, Y1, X2, Y2)
✓ Grid configurado (rows, cols)
✓ Mosaico capturado com sucesso

---

### Aba 5: Alinhamento

**Objetivo:** Alinhar design (Gerber) com imagem real usando fiduciais.

**Processo:**

1. Sistema busca automaticamente fiduciais na imagem do mosaico
2. Calcula transformação:
   - **Translação (TX, TY):** Deslocamento em X e Y
   - **Rotação (Angle):** Ângulo de rotação em graus
   - **Escala (Scale):** Fator de escala (geralmente próximo a 1.0)
3. Exibe overlay do Gerber sobre a imagem
4. Calcula **score de alinhamento** (0-100%)

**Resultados Exibidos:**

```
Translação: TX = 1.2 mm, TY = -0.8 mm
Rotação: 0.5°
Escala: 1.005
Score: 92.3% ✓
```

**Interpretação do Score:**

- **> 90%:** Excelente alinhamento ✓
- **70-90%:** Alinhamento aceitável ⚠
- **< 70%:** Alinhamento ruim, recapture fiduciais ❌

**Dicas:**
- Verifique visualmente se o overlay está correto
- Se score < 70%, recapture os fiduciais
- Garanta boa iluminação ao capturar fiduciais
- Use fiduciais em corners opostos para melhor precisão

**Validação:**
✓ Score de alinhamento > 50%
✓ Transformação calculada com sucesso

---

### Aba 6: Janelas de Inspeção

**Objetivo:** Configurar grupos de aperturas e thresholds de inspeção.

**Conceitos:**

**Grupo de Inspeção:** Conjunto de aperturas com parâmetros comuns.

**Thresholds:**
- **OK:** Abertura >= threshold (limpo)
- **PARTIAL:** Abertura parcialmente bloqueada (aviso)
- **BLOCKED:** Abertura bloqueada (falha)

**Exemplo de Configuração:**

```
Grupo 1: 0.5mm Círculos
├─ Aperturas: 150
├─ Threshold OK: 90%
├─ Threshold Partial: 70%
└─ Confirmado: Sim

Grupo 2: 0.8mm Obrounds
├─ Aperturas: 80
├─ Threshold OK: 85%
├─ Threshold Partial: 65%
└─ Confirmado: Sim
```

**Passos:**

1. Clique em **"Adicionar Grupo"** (ou pressione `G`)
2. Selecione tipo de aperturas do Gerber
3. Configure thresholds
4. Marque "Confirmado" quando satisfatório
5. Repita para outros grupos

**Dicas:**
- Agrupe aperturas similares (mesmo tamanho/tipo)
- Use thresholds mais conservadores para aperturas críticas
- Teste diferentes thresholds e inspecione amostras
- Salve thresholds que funcionam bem como "receita"

**Validação:**
✓ Pelo menos 1 grupo criado
✓ Thresholds definidos
✓ Grupos confirmados

---

### Aba 7: Confirmar e Salvar

**Objetivo:** Revisar configuração e salvar o programa.

**Resumo Exibido:**

```
PROGRAMA DE INSPEÇÃO
═══════════════════════════════════════════
Nome: Inspeção Stencil ABC-123
Código: STENCIL-ABC-123
Versão: v1.0
Criado por: João Silva

ARQUIVO GERBER
═══════════════════════════════════════════
Arquivo: STENCIL-ABC-123.ger
Dimensões: 400.0 x 300.0 mm
Aperturas: 1,234

FIDUCIAIS
═══════════════════════════════════════════
Capturados: 2/2 ✓

MOSAICO
═══════════════════════════════════════════
Grid: 4x4
Área: (0.0, 0.0) → (300.0, 200.0) mm
Imagens: 16

ALINHAMENTO
═══════════════════════════════════════════
Score: 92.3% ✓
Transformação: TX=1.2, TY=-0.8, Angle=0.5°

JANELAS DE INSPEÇÃO
═══════════════════════════════════════════
Grupos: 2
- 0.5mm Círculos (150 aperturas)
- 0.8mm Obrounds (80 aperturas)
```

**Opções:**

- **✓ Criar Recipe:** Também cria Recipe compatível com RecipeManager
- **⏭ Salvar Apenas:** Salva apenas programa de inspeção

**Ao Salvar:**

1. Programa salvo em: `data/inspection_programs/`
2. Se marcado, Recipe criada em: `recipes/`
3. Programa disponível para uso imediato

**Dicas:**
- Revise cuidadosamente todos os dados
- Verifique se o alinhamento está correto (score > 70%)
- Confirme se os thresholds são adequados
- Salve uma Recipe para uso rápido futuro

**Validação:**
✓ Todas as abas anteriores completas
✓ Dados consistentes
✓ Pronto para salvar

---

## Atalhos de Teclado

### Navegação

| Atalho | Ação | Descrição |
|--------|------|-----------|
| `Ctrl + →` | Próxima aba | Avança para próxima etapa |
| `Ctrl + ←` | Aba anterior | Volta para etapa anterior |
| `Tab` | Próximo campo | Avança para próximo campo de formulário |
| `Shift + Tab` | Campo anterior | Volta para campo anterior |

### Ações Específicas

| Atalho | Ação | Contexto |
|--------|------|----------|
| `F` | Capturar fiducial | Aba 3 (Definir Fiduciais) |
| `M` | Capturar mosaico | Aba 4 (Capturar Mosaico) |
| `A` | Executar alinhamento | Aba 5 (Alinhamento) |
| `G` | Adicionar grupo | Aba 6 (Janelas de Inspeção) |
| `Ctrl + Enter` | Concluir e salvar | Aba 7 (Confirmar e Salvar) |
| `Esc` | Cancelar | Qualquer aba |

### Dicas

- Use `Ctrl + →` para navegação rápida
- Pressione `Esc` para cancelar wizard (com confirmação)
- Atalhos de ação só funcionam na aba correspondente

---

## Solução de Problemas

### Erro: "Câmera Desconectada"

**Sintoma:**
- Mensagem: "⚠️ Erro na Câmera - A câmera foi desconectada"
- Preview está preto

**Soluções:**

1. Verifique se a câmera está conectada via USB
2. Reconecte o cabo USB
3. Reinicie o aplicativo
4. Teste com outra aplicação (ex: Camera app do Windows)

---

### Erro: "PLC Não Responde"

**Sintoma:**
- Mensagem: "⚠️ Erro no PLC - O PLC não está respondendo"
- Movimento não ocorre

**Soluções:**

1. Verifique se o PLC está ligado
2. Confirme conexão de rede (cabo Ethernet)
3. Ping no IP do PLC: `ping 192.168.1.5`
4. Reinicie o PLC se necessário

---

### Erro: "Score de Alinhamento Muito Baixo"

**Sintoma:**
- Score < 70%
- Overlay não corresponde à imagem

**Soluções:**

1. Recapture os fiduciais com melhor iluminação
2. Garanta que os fiduciais estão em foco
5. Use fiduciais em corners opostos
6. Verifique se o stencil está posicionado corretamente

---

### Erro: "Não Foi Possível Capturar Imagem"

**Sintoma:**
- Mensagem durante captura de mosaico
- Algumas imagens falham

**Soluções:**

1. Aumente o delay entre capturas (ex: 200ms → 500ms)
2. Verifique iluminação (backlight ligado)
3. Reduza velocidade de movimento do PLC
4. Verifique se há vibração no sistema

---

### Erro: "Arquivo Gerber Inválido"

**Sintoma:**
- Não consegue carregar arquivo `.ger`
- Erro de parsing

**Soluções:**

1. Verifique se o arquivo está no formato RS-274X
2. Tente abrir em outro visualizador de Gerber
3. Verifique se o arquivo não está corrompido
4. Exporte novamente do software CAD

---

## Melhores Práticas

### 1. Organização de Programas

**Nomenclatura Consistente:**
```
STENCIL-CÓDIGO_versão_descrição
Ex: STENCIL-ABC-123_v1.0_inicial
```

**Versionamento:**
- `v1.0`: Versão inicial
- `v1.1`: Pequenas correções
- `v2.0`: Mudanças maiores

### 2. Captura de Fiduciais

**Recomendações:**
- Use iluminação consistente (backlight)
- Capture fiduciais limpos (sem resíduos)
- Centralize o fiducial no frame
- Use janela de captura apropriada (50px para 1-2mm)

### 3. Configuração de Mosaico

**Grid Size:**
- **Pequeno (3x3):** Áreas pequenas, teste rápido
- **Médio (5x5):** Áreas médias, equilíbrio
- **Grande (8x8+):** Áreas grandes, mais tempo

**Sobreposição:**
- **10%:** Econômico, menor tempo
- **15%:** Balanceado (recomendado)
- **20%+:** Alta qualidade, mais tempo

### 4. Thresholds de Inspeção

**Conservador (Mais estrito):**
- OK: 95%
- Partial: 85%

**Moderado (Balanceado):**
- OK: 90%
- Partial: 70%

**Liberal (Mais flexível):**
- OK: 85%
- Partial: 65%

**Recomendação:** Comece com moderado e ajuste baseado em resultados.

### 5. Validação de Alinhamento

**Score Excelente (> 90%):**
- Prosseguir com inspeção
- Transformação confiável

**Score Aceitável (70-90%):**
- Verifique visualmente o overlay
- Pode prosseguir, mas com cautela

**Score Ruim (< 70%):**
- Recapture fiduciais
- Verifique iluminação
- Não prossiga até corrigir

---

## Referências

### Documentos Relacionados

- [TESTING.md](../testing_guide.md) - Guia de teste
- [ANALISE_INTEGRACAO_MOVEMENT_CONTROLS.md](../architecture/ANALISE_INTEGRACAO_MOVEMENT_CONTROLS.md) - Integração de Controles de Movimento

### Arquivos de Configuração

- `config/aoi_config.json` - Configuração do sistema
- `data/inspection_programs/` - Programas salvos
- `recipes/` - Recipes criadas

### Logs e Debug

**Localização de Logs:**
- Windows: `%APPDATA%/Tensiometro/logs/`
- Linux: `~/.local/share/Tensiometro/logs/`

**Informações Úteis:**
- Erros de hardware: Procure por "❌"
- Informações de debug: Procure por "🔍"
- Conclusões bem-sucedidas: Procure por "✅"

---

## Suporte

### Contato

Em caso de problemas ou dúvidas:
1. Consulte a seção [Solução de Problemas](#solução-de-problemas)
2. Verifique os logs para detalhes técnicos
3. Entre em contato com o suporte técnico

### Feedback

Sugestões para melhoria do Engineering Wizard são bem-vindas!

**Version History:**
- v1.0 (2026-01-13): Versão inicial com 7 abas completas
- Planejado: v1.1 - Melhorias de performance e UX adicional

---

**Fim do Guia do Usuário do Engineering Wizard**

Para mais informações, consulte a documentação técnica em `docs/architecture/`.
