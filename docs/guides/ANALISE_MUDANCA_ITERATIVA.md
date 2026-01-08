# Análise de Mudanças - Fluxo de Inspeção Iterativa

**Data:** 2026-01-08
**Status:** 🔄 Em Análise
**Solicitado por:** Cliente

---

## 📋 MUDANÇAS SOLICITADAS

### Mudança 1: 3 Status de Aprovação (em vez de 2)

**ANTES (2 status):**
- ✅ Aprovado (Verde)
- ❌ Reprovado (Vermelho)

**DEPOIS (3 status):**
- ✅ **Aprovado Automático** (Verde vibrante #4CAF50)
  - Sistema aprovou sem intervenção do usuário
  - Todos os pontos dentro da especificação
  - Sem defeitos identificados

- ✅ **Aprovado com Julgamento** (Verde-amarelo #CDDC39)
  - Sistema identificou defeitos
  - Usuário julgou como "falhas falsas"
  - Override do sistema pelo operador
  - Fica registrado no histórico

- ❌ **Reprovado** (Vermelho #F44336)
  - Sistema identificou defeitos
  - Usuário confirmou como "defeitos reais"
  - Usuário NÃO corrigiu durante a sessão
  - Operação finalizada com reprovação

**Impacto:**
- Distinção clara entre aprovação automática e aprovada por intervenção
- Melhor rastreabilidade de decisões humanas
- Maior controle de qualidade

---

### Mudança 2: Inspeção Iterativa com Correção e Reteste

**CONCEITO CHAVE:**
Uma sessão de inspeção (ex: "Limpeza XPTO") pode ter múltiplas iterações de correção e reteste ANTES de ser finalizada.

**FLUXO NOVO:**

```
INÍCIO da Sessão de Inspeção "XPTO"
    ↓
Executar Inspeção Completa (1ª iteração)
    ↓
Sistema Identifica N Defeitos
    ↓
Usuário Percorre Cada Defeito

PARA CADA DEFEITO, o usuário pode:
    ├─ OPÇÃO A: "Falha Falsa"
    │   → Marca como aprovado (override)
    │   → Ponto sai da lista de defeitos
    │   → Registra no histórico
    │   ↓
    │   Continua para próximo defeito
    │
    ├─ OPÇÃO B: "Defeito Real - Confirmar"
    │   → Marca como defeito confirmado
    │   → Registra no histórico
    │   ↓
    │   Continua para próximo defeito
    │
    └─ OPÇÃO C: "Corrigir e Retestar" ⭐ NOVA
        → Permite correção do problema
        → PAUSA a inspeção
        ↓
        Usuário realiza correção:
        - Limpa o ponto novamente
        - Ajusta parâmetro
        - Outra ação corretiva
        ↓
        Sistema RETESTA apenas os pontos marcados
        (NÃO precisa medir tudo de novo)
        ↓
        Sistema reavalia os pontos retestados
        ↓
        Para cada ponto retestado:
        - Se APROVADO → Sai da lista de defeitos
        - Se REPROVADO → Volta para lista de defeitos
        ↓
        Usuário julga novamente os pontos retestados
        ↓
        Loop continua até:
        - Usuário aprovar todos
        - Usuário reprovar definitivamente
        - Usuário finalizar sessão
    ↓
FIM da Sessão de Inspeção
    ↓
Resultado Final:
- Se todos aprovados → Status: ✅ Aprovado (Automático ou com Julgamento)
- Se defeitos confirmados sem correção → Status: ❌ Reprovado
```

---

## 🔍 ANÁLISE DE IMPACTO

### Componentes Afetados

#### 1. Tela de Análise Visual Humana (Wireframe 06)

**MUDANÇAS NECESSÁRIAS:**

**Adicionar botão:**
```
┌──────────────────────────────────────┐
│  [🔄 Corrigir e Retestar Este Ponto] │
└──────────────────────────────────────┘
```

**Adicionar indicador de iteração:**
```
Iteração: 1 de 3
Última correção: 15/12/2025 14:35
```

**Adicionar histórico do ponto:**
```
Histórico de Iterações:
  Iteração 1: 14:30 - Bloqueado (85% aberto)
    → Julgamento: Defeito real confirmado
    → Ação: Corrigir e Retestar
  Iteração 2: 14:45 - Bloqueado (95% aberto)
    → Julgamento: Corrigir e Retestar novamente
  Iteração 3: 15:00 - Aberto (100% aberto)
    → Julgamento: Aprovado
```

**Modificar botões de julgamento:**
```
ANTES:
  [✓ Confirmar como Defeito]
  [✓ Aprovar (Falha Falsa)]

DEPOIS:
  [✓ Confirmar como Defeito Real]
  [✓ Aprovar (Falha Falsa)]
  [🔄 Corrigir e Retestar] ← NOVO
  [❌ Reprovar Sessão] ← NOVO (finaliza com reprovação)
```

#### 2. Tela de Histórico (Wireframe 07)

**MUDANÇAS NECESSÁRIAS:**

**Adicionar 3ª coluna de status:**
```
ANTES:
  Status: ✅ Aprovado | ❌ Reprovado

DEPOIS:
  Status:
    ✅ Aprovado (Auto) - Verde vibrante
    ✅ Aprovado (User) - Verde-amarelo
    ❌ Reprovado - Vermelho
```

**Adicionar informações de iteração:**
```
Detalhes da Sessão:
  Iterações: 3
  Defeitos iniciais: 5
  Defeitos corrigidos: 4
  Defeitos confirmados: 1
  Status Final: Reprovado
```

**Adicionar indicador visual:**
```
Código do Status: A-auto / A-user / R
```

#### 3. Documento de Fluxo do Usuário

**ATUALIZAÇÕES NECESSÁRIAS:**

- Seção 5 (Tela de Resultados) - Adicionar 3º status
- Seção 6 (Análise Visual Humana) - Adicionar fluxo de correção
- Seção 7 (Histórico) - Adicionar informações de iteração
- Diagrama de estado - Adicionar loop de correção

#### 4. Questionário (fluxo_usuario_questionario.md)

**PERGUNTAS A ATUALIZAR:**

**Q36** (atual) - Sobre status de aprovação
- RESPOSTA ATUAL: 2 status (aprovado/reprovado)
- NOVA RESPOSTA: 3 status (automático/com julgamento/reprovado)

**Q40-Q45** (atual) - Sobre análise visual
- Adicionar pergunta sobre fluxo de correção
- Adicionar pergunta sobre múltiplas iterações

**NOVAS PERGUNTAS:**

**Q41a:** Quando o usuário identifica um defeito real, quais ações ele pode tomar?
- [ ] Confirmar como defeito (reprovar)
- [ ] Aprovar (falha falsa)
- [ ] Corrigir e retestar o ponto
- [ ] Outro: _____

**Q41b:** Quantas vezes o usuário pode corrigir e retestar um ponto na mesma sessão?
- [ ] Apenas 1 vez
- [ ] Até 3 vezes
- [ ] Ilimitado
- [ ] Até aprovar ou reprovar definitivamente

**Q41c:** Quando o usuário escolhe "Corrigir e Retestar", o que acontece?
- [ ] Sistema permite pausa para correção
- [ ] Sistema retesta apenas os pontos marcados
- [ ] Sistema retesta todos os pontos
- [ ] Sistema reinicia a inspeção do zero

---

## 📊 MODELO DE DADOS

### Estrutura de Dados - Iteração

```json
{
  "session_id": "XPTO-2025-12-15-001",
  "stencil_code": "STENCIL-ABC-123",
  "session_type": "Limpeza XPTO",
  "start_time": "2025-12-15T14:30:00",
  "end_time": "2025-12-15T15:15:00",
  "iterations": [
    {
      "iteration_number": 1,
      "timestamp": "2025-12-15T14:30:00",
      "defects_found": 5,
      "defects": [
        {
          "defect_id": "D001",
          "position": {"x": 125, "y": 78},
          "type": "blocked",
          "area_expected": 2.3,
          "area_observed": 0.6,
          "percentage_open": 26,
          "image_path": "/data/sessions/XPTO-2025-12-15-001/iter1/D001.png",
          "judgment": "confirmed_real",
          "action": "correction_and_retest"
        }
      ]
    },
    {
      "iteration_number": 2,
      "timestamp": "2025-12-15T14:45:00",
      "defects_retested": 1,
      "defects": [
        {
          "defect_id": "D001",
          "position": {"x": 125, "y": 78},
          "type": "blocked",
          "area_expected": 2.3,
          "area_observed": 1.9,
          "percentage_open": 82,
          "image_path": "/data/sessions/XPTO-2025-12-15-001/iter2/D001.png",
          "judgment": "confirmed_real",
          "action": "correction_and_retest"
        }
      ]
    },
    {
      "iteration_number": 3,
      "timestamp": "2025-12-15T15:00:00",
      "defects_retested": 1,
      "defects": [
        {
          "defect_id": "D001",
          "position": {"x": 125, "y": 78},
          "type": "ok",
          "area_expected": 2.3,
          "area_observed": 2.3,
          "percentage_open": 100,
          "image_path": "/data/sessions/XPTO-2025-12-15-001/iter3/D001.png",
          "judgment": "approved",
          "action": "approved"
        }
      ]
    }
  ],
  "final_status": "approved_with_judgment",
  "total_corrections": 3,
  "defects_confirmed": 0,
  "operator": "João Silva"
}
```

---

## 🎨 WIREFRAMES A ATUALIZAR

### 1. 06_analise_visual_humana.svg

**Adicionar:**
- Botão "Corrigir e Retestar"
- Histórico de iterações do ponto
- Contador de iteração
- Botão "Reprovar Sessão"

**Modificar:**
- Layout para acomodar informações de iteração
- Lista de defeitos para mostrar estado de iteração

### 2. 07_tela_historico.svg

**Adicionar:**
- 3ª coluna de status (3 opções)
- Informações de iteração
- Indicador visual de tipo de aprovação
- Estatísticas de correções

**Modificar:**
- Cores de status para diferenciar aprovação automática vs julgamento
- Layout para acomodar novas informações

---

## 🔄 ATUALIZAÇÕES NECESSÁRIAS

### Arquivos a Atualizar

1. ✅ `docs/guides/ANALISE_MUDANCA_ITERATIVA.md` (este arquivo)
2. ⏳ `docs/guides/fluxo_usuario_questionario.md` - Atualizar respostas
3. ⏳ `docs/guides/fluxo_usuario_operador.md` - Atualizar fluxo
4. ⏳ `docs/wireframes/svg/06_analise_visual_humana.svg` - Atualizar wireframe
5. ⏳ `docs/wireframes/svg/07_tela_historico.svg` - Atualizar wireframe
6. ⏳ `docs/guides/plano_implementacao_interface.md` - Atualizar plano

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Atualizar Documentação
- [x] Criar documento de análise
- [ ] Atualizar questionário (Q36, Q41a-c)
- [ ] Atualizar fluxo do usuário
- [ ] Atualizar plano de implementação

### Fase 2: Atualizar Wireframes
- [ ] Atualizar wireframe 06 (Análise Visual)
- [ ] Atualizar wireframe 07 (Histórico)

### Fase 3: Implementar (futuro)
- [ ] Adicionar 3º status no banco de dados
- [ ] Implementar loop de correção e reteste
- [ ] Adicionar histórico de iterações
- [ ] Atualizar interface para mostrar iterações

---

## 📝 DECISÕES PENDENTES

### Para o Cliente

1. **Limite de Iterações:**
   - Pergunta: Existe um limite máximo de iterações por sessão?
   - Opções:
     - [ ] Ilimitado
     - [ ] Máximo 3 iterações
     - [ ] Máximo 5 iterações
     - [ ] Definir por configuração

2. **Reteste Parcial vs Total:**
   - Pergunta: Ao retestar, medir apenas os pontos marcados ou todos?
   - Recomendação: Apenas os pontos marcados (mais eficiente)
   - Confirmar com cliente

3. **Pausa para Correção:**
   - Pergunta: O sistema deve pausar automaticamente ou usuário indica quando pronto?
   - Recomendação: Usuário indica quando pronto (botão "Retestar Agora")

4. **Notificação de Reteste:**
   - Pergunta: Sistema deve avisar quando ready para retestar?
   - Recomendação: Sim, com indicador visual e som

---

## 🎯 PRÓXIMOS PASSOS

1. **Validar com cliente** as decisões pendentes
2. **Atualizar questionário** com novas respostas
3. **Atualizar wireframes** 06 e 07
4. **Atualizar fluxo do usuário** com loop de correção
5. **Apresentar novamente** para aprovação

---

**Documento criado em:** 2026-01-08
**Versão:** 1.0
**Status:** ⏳ Aguardando validação das decisões pendentes
