# Task Manager - Sistema de Backlog

Sistema de gerenciamento de tarefas para o projeto Tensiometro. Permite adicionar, listar e executar tasks seguindo um fluxo estruturado com aprovações.

## Comandos Disponíveis

### `/task add "descrição"` - Adicionar Nova Task

**Propósito:** Adiciona uma nova tarefa ao backlog com status `pending`.

**Uso:**
```
/task add "descrição detalhada da tarefa"
```

**Execução:**
1. Ler `backlog.md` para obter o próximo número de task
2. Adicionar nova task ao final da seção "Tasks Pendentes"
3. Preservar texto exato do usuário no campo "Solicitação Original"
4. Confirmar criação com o ID da task

**Template de Task:**
```markdown
### Task #N

**Solicitação Original:**
{texto exato do usuário}

**Entendimento:** (a ser preenchido quando a task for movida para in_progress)

**Status:** pending

**Criada em:** YYYY-MM-DD
```

**Output:** Confirmação da task criada com ID

---

### `/task list` - Listar Tasks Pendentes

**Propósito:** Exibe todas as tasks pendentes no backlog.

**Uso:**
```
/task list
```

**Execução:**
1. Ler `backlog.md`
2. Extrair todas as tasks da seção "Tasks Pendentes"
3. Exibir formato resumido: ID, status, primeira linha da solicitação

**Output:** Lista formatada com:
```
#ID | Status   | Descrição (primeiros 50 chars)
----|----------|--------------------------------
#1  | pending  | precisamos mudar as cores...
#2  | pending  | implementar nova funcionalidade...
```

---

### `/task run #N` - Executar Task

**Propósito:** Executa o fluxo completo de uma task com aprovações.

**Uso:**
```
/task run #1
```

**Fluxo de Execução:**

1. **Preparação:**
   - Ler task de `backlog.md`
   - Mover task para `docs/backlog/in_progress.md`
   - Remover task de `backlog.md`

2. **Análise e Entendimento:**
   - Investigar código relacionado à solicitação
   - Preencher campo "Entendimento" com:
     - Localização do código
     - Problema identificado
     - Solução proposta
     - Arquivos afetados
   - Apresentar entendimento ao usuário
   - **AGUARDAR aprovação do usuário**

3. **Execução:**
   - Após aprovação, implementar mudanças
   - Usar tokens do Design System quando aplicável
   - Seguir padrões do projeto (CLAUDE.md)

4. **Validação:**
   - Executar aplicação para testar
   - Solicitar aprovação do usuário
   - **AGUARDAR aprovação do usuário**

5. **Conclusão:**
   - Após aprovação, mover task para `docs/backlog/completed.md`
   - Registrar data de conclusão
   - Limpar `docs/backlog/in_progress.md`

**Confirmações Obrigatórias:**
- Sempre aguardar aprovação antes de executar
- Sempre aguardar aprovação após executar

---

### `/task status` - Status de Todas as Tasks

**Propósito:** Exibe o status de todas as tasks em todos os arquivos.

**Uso:**
```
/task status
```

**Execução:**
1. Ler `backlog.md` (pendentes)
2. Ler `docs/backlog/in_progress.md` (em progresso)
3. Ler `docs/backlog/completed.md` (concluídas)

**Output:**
```
=== TASKS STATUS ===

PENDENTES (backlog.md):
  #2 - implementar nova funcionalidade...

EM PROGRESSO (in_progress.md):
  (nenhuma)

CONCLUÍDAS (completed.md):
  #1 - Ajustar Cores dos Visores de Posição (2026-03-28)

Total: 2 tasks (1 pendente, 0 em progresso, 1 concluída)
```

---

## Estrutura de Arquivos

```
tensiometro/
├── backlog.md                    # Tasks pendentes + documentação
└── docs/
    └── backlog/
        ├── pending.md            # (reserva)
        ├── in_progress.md        # Tasks sendo executadas
        └── completed.md          # Histórico de tasks concluídas
```

## Regras Importantes

1. **Preservar texto original:** Nunca alterar a "Solicitação Original"
2. **Aprovações obrigatórias:** Sempre aguardar aprovação do usuário
3. **Design System:** Usar COLORS.*, TYPO.*, etc. quando aplicável
4. **Commits:** Não fazer commit automático - aguardar solicitação
5. **Idioma:** Responder em português brasileiro

## Tratamento de Erros

Se ocorrer erro:
1. Exibir mensagem clara em português
2. Sugerir próximos passos
3. Manter task em `in_progress.md` para retomar depois