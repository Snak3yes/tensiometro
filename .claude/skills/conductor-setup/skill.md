# Conductor Setup Command

You are executing the `/conductor-setup` command to initialize the Conductor system for the project.

## Purpose
Initialize the Conductor system by configuring commit authorship and generating base documentation.

## Execution Steps

### Step 1: Check Existing Setup

```bash
# Check if setup_state.json exists
test -f conductor/setup_state.json
```

If exists and not reconfigure:
- Ask user if they want to reconfigure
- If no, exit with message showing existing setup

### Step 2: Configure Commit Authorship

**Check git local configuration:**

```bash
git config user.name
git config user.email
```

**If both name and email are configured:**

Use `AskUserQuestion` tool:
```
Detectado configuração git local:
  Nome: <git_config_name>
  Email: <git_config_email>

Deseja usar estas configurações como padrão para commits do Conductor?

Options:
- Sim (recomendado) - Usa nome e email do git local
- Não - Vou fornecer outro nome/email
```

If user chooses "Sim":
- Write name and email to `conductor/setup_state.json`
- Continue to Step 3

If user chooses "Não" or git config is incomplete:
- Ask for the information using `AskUserQuestion`:
```
Configure as informações de autor para commits:

Nome do autor (obrigatório):
  Este nome deve ser o mesmo do seu perfil GitHub
  para que commits apareçam com sua foto e link.

Email do autor:
  Deve ser um email verificado no seu GitHub
  Deixe em branco para não incluir email.
```

**Write to setup_state.json:**
```json
{
  "commit_author_name": "<provided_name>",
  "commit_author_email": "<provided_email>"
}
```

**Fallback:**
If user leaves name blank, use "Claude Sonnet 4.5" as author name.

### Step 3: Generate Base Documentation

Check which documentation files exist and generate missing ones:

- `conductor/product.md` - Product vision and context
- `conductor/product-guidelines.md` - UI/UX guidelines
- `conductor/tech-stack.md` - Technology stack
- `conductor/workflow.md` - Development workflow (already exists)
- `conductor/tracks.md` - Track listing

### Step 4: Display Results

Show:
- Generated files location
- Commit author configuration
- Confirmation message

## Output Location
Generated files go to `conductor/` directory.

## Error Handling
- If git config fails: Show error and suggest manual configuration
- If file write fails: Check permissions and suggest alternative location
- Always provide helpful error messages in Portuguese if user communicates in Portuguese
