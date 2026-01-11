# 🚀 Comandos de Barra do Claude Conductor

Sistema completo de comandos de barra para gerenciamento de projetos no Claude Code.

## 📋 Lista de Comandos

### 1. `/conductor-setup`
Inicializa o sistema Conductor com entrevistas estruturadas.

```bash
/conductor-setup
```

**Parâmetros:**
- `reconfigure` (bool) - Reconfigurar mesmo se setup já existe

**O que faz:**
- 4 entrevistas estruturadas (produto, diretrizes, stack, workflow)
- Gera 5 documentos base em `conductor/`
- Configura o sistema para o projeto

**Arquivos gerados:**
- `conductor/product.md`
- `conductor/product-guidelines.md`
- `conductor/tech-stack.md`
- `conductor/workflow.md`
- `conductor/tracks.md`

---

### 2. `/conductor-status`
Mostra status de todas as tracks com progresso.

```bash
/conductor-status
```

**Parâmetros:**
- `verbose` (bool) - Mostrar informações detalhadas

**Exibe:**
- Total de tracks (ativas, completadas, arquivadas)
- Status de cada track (pending, in-progress, complete)
- Porcentagem de progresso
- Fase e tarefa atual

**Exemplo de saída:**
```
======================================================================
CONDUCTOR TRACK STATUS
======================================================================

Summary:
  Total Tracks: 2
  Active: 1
  Completed: 0
  Archived: 0

1.  feature_implement_operator_workflow_20260111
   Status: in-progress
   Type: Feature
   Priority: High
   Progress: Phase 1/3 | Tasks: 5/30 complete

Overall Progress: 33.3%
```

---

### 3. `/conductor-new`
Cria nova track (feature/bugfix/refactor/experiment).

```bash
/conductor-new
```

**Parâmetros:**
- `type` (string) - Tipo da track: feature, bugfix, refactor, experiment

**Processo:**
1. Entrevista com 13 perguntas estruturadas
2. Gera `spec.md` (especificação completa)
3. Gera `plan.md` (plano com fases e tarefas)
4. Cria diretório em `conductor/tracks/{track_id}/`

**Perguntas da entrevista:**
1. Tipo da track
2. Título
3. Descrição detalhada
4. Prioridade
5. Complexidade
6. Dependências
7. Critérios de aceitação
8. Requisitos de teste
9. Necessidades de documentação
10. Impacto na performance
11. Considerações de segurança
12. Requisitos de migração
13. Plano de rollback

---

### 4. `/conductor-implement`
Executa track automaticamente com TDD (Red-Green-Refactor).

```bash
/conductor-implement track=feature_implement_operator_workflow_20260111
```

**Parâmetros:**
- `track` (obrigatório) - ID da track
- `start_phase` (opcional) - Fase inicial para retomar
- `auto_mode` (opcional) - Executar sem interação do usuário

**Workflow TDD automático:**
1. Parse do `plan.md`
2. Para cada tarefa incompleta:
   - **RED**: Escreve teste falhando
   - **GREEN**: Implementa código mínimo
   - **REFACTOR**: Melhora qualidade do código
   - **COVERAGE**: Verifica cobertura (>80%)
   - **COMMIT**: Commit com mensagem convencional
   - **NOTE**: Adiciona git note detalhado
3. Ao final de cada fase: Cria checkpoint

**Exemplo de uso:**
```bash
# Iniciar implementação
/conductor-implement track=feature_user_auth

# Retomar da fase 2
/conductor-implement track=feature_user_auth start_phase=2

# Modo automático (sem confirmações)
/conductor-implement track=feature_user_auth auto_mode=true
```

---

### 5. `/conductor-revert`
Reverte track, fase ou tarefa usando git reset.

```bash
# Reverter track inteira
/conductor-revert track=feature_implement_operator_workflow_20260111

# Reverter até fase específica
/conductor-revert track=feature_x phase=2

# Auto-confirmar
/conductor-revert track=feature_x --confirm
```

**Parâmetros:**
- `track` (obrigatório) - ID da track
- `phase` (opcional) - Número da fase para reverter
- `confirm` (opcional) - Pular confirmação

**O que faz:**
- Usa `git reset --hard` para voltar ao checkpoint
- Remove commits após o checkpoint
- Atualiza `plan.md` para refletir estado anterior

**⚠️ Aviso:** Operação destrutiva - commits após o checkpoint serão perdidos!

---

### 6. `/conductor-update`
Atualiza documentação base das respostas do setup.

```bash
# Atualizar todos os documentos
/conductor-update

# Atualizar documento específico
/conductor-update doc=product
```

**Parâmetros:**
- `doc` (string) - Documento: product, tech-stack, workflow, all
- `confirm` (bool) - Pular confirmação

**Documentos atualizados:**
- `conductor/product.md` - Visão do produto
- `conductor/tech-stack.md` - Stack tecnológica
- `conductor/workflow.md` - Preferências de workflow

**O que faz:**
- Lê `conductor/setup_state.json`
- Regenera documentos dos templates
- Cria backups antes de sobrescrever (.bak)

---

### 7. `/conductor-archive`
Arquiva track completada.

```bash
/conductor-archive track=feature_implement_operator_workflow_20260111

# Auto-confirmar
/conductor-archive track=feature_x --confirm
```

**Parâmetros:**
- `track` (obrigatório) - ID da track
- `confirm` (opcional) - Pular confirmação

**O que faz:**
- Move track para `conductor/archive/{track_id}/`
- Atualiza `conductor/tracks.md` (status: archived)
- Cria `archive_summary.md` com histórico

**Antes:**
```
conductor/tracks/{track_id}/
```

**Depois:**
```
conductor/archive/{track_id}/
```

---

## 🎯 Fluxo de Trabalho Completo

### Exemplo 1: Criar e Implementar Feature

```bash
# 1. Inicializar sistema (primeira vez)
/conductor-setup

# 2. Verificar status atual
/conductor-status

# 3. Criar nova feature
/conductor-new

# Responder 13 perguntas:
# - Tipo: feature
# - Título: Implement user authentication
# - Descrição: Add OAuth2 with Google and GitHub
# - Prioridade: High
# - Complexidade: Medium
# ... (demais perguntas)

# 4. Implementar automaticamente
/conductor-implement track=feature_implement_user_auth_20260111

# O sistema vai:
# - Executar TDD para cada tarefa
# - Fazer commits automáticos
# - Adicionar git notes
# - Criar checkpoints

# 5. Verificar progresso
/conductor-status

# 6. Arquivar quando completar
/conductor-archive track=feature_implement_user_auth_20260111
```

### Exemplo 2: Retomar Trabalho Interrompido

```bash
# 1. Verificar status
/conductor-status

# 2. Identificar onde parou
# Output mostra: Phase 2/3, Task 15/30

# 3. Retomar implementação
/conductor-implement track=feature_x start_phase=3

# Continua da fase 3 em diante
```

### Exemplo 3: Reverter se Precisar

```bash
# Algo deu errado na fase 3
# Reverter para final da fase 2
/conductor-revert track=feature_x phase=2

# Verificar que voltou
/conductor-status

# Retomar da fase 2
/conductor-implement track=feature_x start_phase=2
```

---

## 📂 Estrutura de Diretórios

```
.claude/skills/                    # Skills do Claude Code
├── conductor/                     # Skill principal
│   ├── skill.json
│   └── skill.md
├── conductor-setup/
│   ├── skill.json
│   └── skill.md
├── conductor-status/
│   ├── skill.json
│   └── skill.md
├── conductor-new/
│   ├── skill.json
│   └── skill.md
├── conductor-implement/
│   ├── skill.json
│   └── skill.md
├── conductor-revert/
│   ├── skill.json
│   └── skill.md
├── conductor-update/
│   ├── skill.json
│   └── skill.md
└── conductor-archive/
    ├── skill.json
    └── skill.md

conductor/                         # Dados gerados
├── product.md                     # Visão do produto
├── tech-stack.md                  # Stack tecnológica
├── workflow.md                    # Workflow TDD
├── tracks.md                      # Registro de tracks
├── tracks/                        # Tracks ativas
│   └── {track_id}/
│       ├── spec.md
│       ├── plan.md
│       └── metadata.json
└── archive/                       # Tracks arquivadas
    └── {track_id}/
```

---

## 🔧 Troubleshooting

### Comando não aparece?
- Reinicie o Claude Code
- Verifique se `.claude/skills/{command}/skill.json` existe
- Confirme que está no diretório raiz do projeto

### Erro ao executar?
- Use o script Python diretamente:
  ```bash
  python claude-conductor/conductor.py <comando>
  ```

### Verificar skills instalados:
```bash
ls .claude/skills/
```

### Testar comando individual:
```bash
# Status
python claude-conductor/support_commands.py status

# New (requer interação)
python claude-conductor/conductor.py new
```

---

## 📚 Referência Rápida

| Comando | Descrição | Parâmetros Principais |
|---------|-----------|----------------------|
| `/conductor-setup` | Inicializar sistema | `reconfigure` |
| `/conductor-status` | Ver status das tracks | `verbose` |
| `/conductor-new` | Criar nova track | `type` |
| `/conductor-implement` | Executar track | `track`, `start_phase` |
| `/conductor-revert` | Reverter track | `track`, `phase` |
| `/conductor-update` | Atualizar docs | `doc` |
| `/conductor-archive` | Arquivar track | `track` |

---

## ✅ Status do Sistema

- ✅ 7 comandos de barra criados
- ✅ Skills funcionais
- ✅ Documentação completa
- ✅ 2 tracks existentes
- ✅ Sistema pronto para uso

**Versão:** 1.0.0
**Data:** 2026-01-11
**Autor:** Claude Sonnet 4.5

---

## 🚀 Começar Agora

```bash
# Ver status atual
/conductor-status

# Ou criar nova track
/conductor-new

# Ou implementar track existente
/conductor-implement track=feature_implement_operator_workflow_20260111
```

**Sistema 100% funcional!** 🎉
