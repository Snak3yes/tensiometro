# Backlog de Tarefas - Tensiometro

## Fluxo de Trabalho

### Estrutura de Arquivos
```
docs/
├── backlog/
│   ├── pending.md      # Tasks pendentes (aguardando execução)
│   ├── in_progress.md  # Tasks em execução (aprovadas, em desenvolvimento)
│   └── completed.md    # Tasks concluídas (aprovadas após testes)
```

### Processo

1. **Nova Task**: Adicionada neste arquivo com status `pending`
2. **Antes da Execução**:
   - Task é movida para `docs/backlog/in_progress.md`
   - Texto detalhado do entendimento é escrito e apresentado ao usuário
   - Usuário aprova ou faz ressalvas antes de iniciar
3. **Após Execução**:
   - Testes são realizados (manuais ou automatizados conforme aplicável)
   - Usuário valida que a task foi executada corretamente
4. **Conclusão**:
   - Task é movida para `docs/backlog/completed.md`
   - Data de conclusão é registrada

### Template de Task

```markdown
## Task #N

**Solicitação Original:** (preservar palavras exatas do usuário)

**Entendimento:** (descrição detalhada do que será feito, aguardando aprovação)

**Status:** pending | in_progress | completed

**Criada em:** YYYY-MM-DD

**Concluída em:** YYYY-MM-DD (quando aplicável)
```

### Definição de Testes para Validação

- **Teste Manual**: Usuário executa a aplicação e verifica visual/funcionalmente
- **Teste Unitário**: Quando aplicável, criar ou rodar testes automatizados
- **Critério de Aprovação**: Funcionalidade funciona conforme esperado pelo usuário

---

## Tasks Pendentes

*(Nenhuma task pendente no momento - verifique docs/backlog/in_progress.md)*

