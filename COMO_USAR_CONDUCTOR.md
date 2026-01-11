# 🚀 Claude Conductor - Como Usar

## Sistema de Gerenciamento de Projetos para Claude Code

O **Claude Conductor** está instalado e pronto para usar! Abaixo estão as duas formas de usar o sistema:

---

## 📋 Formas de Uso

### Opção 1: Comando de Barra (quando disponível)

Quando o skill `/conductor` estiver disponível no Claude Code, você poderá usar:

```
/conductor setup
/conductor status
/conductor new
/conductor implement track=feature_x
/conductor revert track=feature_x phase=2
/conductor update
/conductor archive track=feature_x
```

### Opção 2: Script Python (disponível agora)

Use o script wrapper diretamente:

```bash
python claude-conductor/conductor.py <comando> [opções]
```

---

## 🎯 Comandos Disponíveis

### 1. **setup** - Inicializar Sistema

Inicializa o Conductor com 4 entrevistas estruturadas:

```bash
python claude-conductor/conductor.py setup
```

**O que faz:**
- Entrevista sobre produto, diretrizes, stack e workflow
- Cria documentos em `conductor/`
- Configura o sistema para o projeto

**Arquivos gerados:**
- `conductor/product.md`
- `conductor/product-guidelines.md`
- `conductor/tech-stack.md`
- `conductor/workflow.md`
- `conductor/tracks.md`

---

### 2. **status** - Ver Status das Tracks

Mostra todas as tracks com progresso:

```bash
python claude-conductor/conductor.py status
```

**Exemplo de saída:**
```
======================================================================
CONDUCTOR TRACK STATUS
======================================================================

Summary:
  Total Tracks: 2
  Active: 0
  Completed: 0
  Archived: 0

1.  feature_implement_operator_workflow_20260111
   Status: planning
   Type: Feature
   Priority: High
   Created: 2026-01-11
   Progress: Phase 0/3 | Tasks in plan: 30

2.  refactor_recipe_manager_20260110
   Status: new
   Type: Refactor
   Priority: N/A
   Created: 2026-01-10
   Progress: Phase 2/3 | Tasks in plan: 2

======================================================================
Overall Progress: 2/6 phases completed
Completion: 33.3%
======================================================================
```

---

### 3. **new** - Criar Nova Track

Cria uma nova track (feature/bugfix/refactor):

```bash
python claude-conductor/conductor.py new
```

**Processo:**
1. Faz 13 perguntas estruturadas sobre a track
2. Gera `spec.md` (especificação completa)
3. Gera `plan.md` (plano com fases e tarefas)
4. Cria diretório em `conductor/tracks/{track_id}/`

**Perguntas incluem:**
- Tipo (feature/bugfix/refactor/experiment)
- Título e descrição
- Prioridade e complexidade
- Dependências
- Critérios de aceitação
- Requisitos de teste
- Documentação necessária
- Impacto na performance
- Segurança
- Migração
- Rollback
- Métricas de sucesso
- Data alvo

**Exemplo de saída:**
```
======================================================================
✅ Track criada com sucesso!
======================================================================
Track ID: feature_implement_user_auth_20260111
Spec: conductor/tracks/feature_implement_user_auth_20260111/spec.md
Plan: conductor/tracks/feature_implement_user_auth_20260111/plan.md

Para começar a implementar, use:
  python claude-conductor/conductor.py implement track=feature_implement_user_auth_20260111
```

---

### 4. **implement** - Executar Track

Implementa track automaticamente com TDD:

```bash
python claude-conductor/conductor.py implement track=feature_x
```

**Workflow TDD automático:**
1. Parse do `plan.md`
2. Para cada tarefa:
   - **RED**: Escreve teste falhando
   - **GREEN**: Implementa código mínimo
   - **REFACTOR**: Melhora qualidade
   - Verifica cobertura (>80%)
   - Commit com mensagem convencional
   - Adiciona git note detalhado
3. Ao final de cada fase: Cria checkpoint

**Parâmetros:**
- `track=ID` (obrigatório): ID da track
- Exemplo: `track=feature_implement_operator_workflow_20260111`

---

### 5. **revert** - Reverter Track/Fase

Reverte track ou fase específica:

```bash
# Reverter track inteira
python claude-conductor/conductor.py revert track=feature_x

# Reverter até fase específica
python claude-conductor/conductor.py revert track=feature_x phase=2

# Sem confirmar (auto-confirm)
python claude-conductor/conductor.py revert track=feature_x --confirm
```

**O que faz:**
- Usa git reset para reverter commits
- Mantém histórico seguro
- Pede confirmação (a menos que use `--confirm`)

---

### 6. **update** - Atualizar Documentação

Atualiza documentos base do Conductor:

```bash
# Atualizar todos os documentos
python claude-conductor/conductor.py update

# Atualizar documento específico
python claude-conductor/conductor.py update doc=product
```

**Opções de `doc`:**
- `product` - Atualiza product.md
- `tech-stack` - Atualiza tech-stack.md
- `workflow` - Atualiza workflow.md
- `all` - Atualiza todos (padrão)

---

### 7. **archive** - Arquivar Track

Arquiva track completada:

```bash
python claude-conductor/conductor.py archive track=feature_x

# Sem confirmar
python claude-conductor/conductor.py archive track=feature_x --confirm
```

**O que faz:**
- Move track para `conductor/archive/`
- Remove da lista ativa
- Mantém histórico completo

---

## 📖 Exemplo de Fluxo Completo

### 1. Inicializar Sistema
```bash
python claude-conductor/conductor.py setup
```

### 2. Verificar Status
```bash
python claude-conductor/conductor.py status
```

### 3. Criar Nova Feature
```bash
python claude-conductor/conductor.py new
```

Responda as perguntas:
- Tipo: **feature**
- Título: **Implement user authentication**
- Descrição: **Add OAuth2 authentication with Google and GitHub**
- Prioridade: **alta**
- Complexidade: **media**
- ... (demais perguntas)

### 4. Implementar
```bash
python claude-conductor/conductor.py implement track=feature_implement_user_auth_20260111
```

O sistema vai:
- Executar cada tarefa do plan.md
- Seguir ciclo Red-Green-Refactor
- Verificar cobertura (>80%)
- Fazer commits automáticos
- Adicionar git notes

### 5. Monitorar Progresso
```bash
python claude-conductor/conductor.py status
```

### 6. Se Precisar Reverter
```bash
python claude-conductor/conductor.py revert track=feature_implement_user_auth_20260111 phase=2
```

---

## 📂 Estrutura de Diretórios

```
claude-conductor/                    # Código do sistema
├── conductor.py                     # Script CLI (use este!)
├── setup_agent.py                   # Setup
├── planning_agent.py                # Criação de tracks
├── implementation_agent.py          # Implementação TDD
├── support_commands.py              # Comandos de suporte
├── interview_templates/             # Templates JSON
├── templates/                       # Templates Markdown
├── README.md                        # Documentação técnica
└── QUICKSTART.md                    # Guia rápido

conductor/                           # Dados gerados
├── product.md                       # Visão do produto
├── tech-stack.md                    # Stack tecnológica
├── workflow.md                      # Workflow TDD
├── tracks.md                        # Registro de tracks
└── tracks/                          # Tracks ativas
    └── {track_id}/
        ├── spec.md                  # Especificação
        ├── plan.md                  # Plano (fases/tarefas)
        └── metadata.json            # Metadados
```

---

## 🔧 Troubleshooting

### Comando `/conductor` não aparece?
Use o script Python diretamente:
```bash
python claude-conductor/conductor.py <comando>
```

### Erro "ModuleNotFoundError"?
Execute a partir do diretório raiz do projeto:
```bash
cd E:\PycharmProjects\Tensiometro
python claude-conductor/conductor.py status
```

### Verificar tracks criadas
```bash
ls conductor/tracks/
```

### Ver documentação gerada
```bash
cat conductor/product.md
cat conductor/workflow.md
```

---

## 📚 Documentação Adicional

- **README técnico:** `claude-conductor/README.md`
- **Guia rápido:** `claude-conductor/QUICKSTART.md`
- **Arquitetura completa:** `claude-conductor/CONDUCTOR_ARCHITECTURE_PROPOSAL.md`

---

## ✅ Status do Sistema

- ✅ Setup completo (4 fases implementadas)
- ✅ Planejamento de tracks
- ✅ Implementação TDD automática
- ✅ Comandos de suporte (status, revert, update, archive)
- ✅ CLI wrapper funcional
- ✅ 2 tracks criadas

**Progresso geral:** 33.3% (2/6 fases de tracks completadas)

---

**Criado em:** 2026-01-11
**Versão:** 1.0.0
