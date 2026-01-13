# 🌍 Instalação Global do Claude Conductor

Guia para instalar o Claude Conductor globalmente e usar em qualquer projeto.

## 📍 O que foi instalado

### Diretório Global
```
C:\Users\sense\.claude\
├── skills/                    # Skills globais do Claude Code
│   ├── conductor/            # Skill principal
│   ├── conductor-setup/
│   ├── conductor-status/
│   ├── conductor-new/
│   ├── conductor-implement/
│   ├── conductor-revert/
│   ├── conductor-update/
│   └── conductor-archive/
│
└── conductor/                 # Código global do Conductor
    ├── conductor_global.py   # Script principal global
    ├── conductor.bat         # Wrapper Windows
    ├── conductor.sh          # Wrapper Unix/Linux/Mac
    ├── setup_agent.py
    ├── planning_agent.py
    ├── implementation_agent.py
    ├── support_commands.py
    ├── interview_templates/
    ├── templates/
    └── README.md
```

## 🚀 Como Usar (Globalmente)

### Opção 1: Via Comandos de Barra do Claude Code

Os comandos de barra agora estão disponíveis GLOBALMENTE em qualquer projeto:

```bash
/conductor-setup
/conductor-status
/conductor-new
/conductor-implement track=feature_x
/conductor-revert track=feature_x phase=2
/conductor-update
/conductor-archive track=feature_x
```

**Funciona em qualquer projeto!** Não precisa estar no diretório Tensiometro.

### Opção 2: Via Linha de Comando

#### Windows
Adicione ao PATH ou use o caminho completo:

```bash
# Usando o caminho completo
python %USERPROFILE%\.claude\conductor\conductor_global.py status

# Ou se adicionar ao PATH:
conductor status
```

#### Unix/Linux/Mac
```bash
# Usando o caminho completo
python3 ~/.claude/conductor/conductor_global.py status

# Ou se adicionar ao PATH:
conductor status
```

## 🔧 Configuração do PATH (Opcional)

### Windows

1. **Copie o arquivo batch:**
   ```bash
   copy C:\Users\sense\.claude\conductor\conductor.bat C:\Users\sense\conductor.bat
   ```

2. **Adicione C:\Users\sense ao PATH:**
   - Pressione Win + R
   - Digite: `sysdm.cpl`
   - Aba "Avançado"
   - "Variáveis de Ambiente"
   - Em "Variáveis do Sistema", edite "Path"
   - Adicione: `C:\Users\sense`
   - OK

3. **Reinicie o terminal e teste:**
   ```bash
   conductor status
   ```

### Unix/Linux/Mac

1. **Torne executável:**
   ```bash
   chmod +x ~/.claude/conductor/conductor.sh
   ```

2. **Crie symlink:**
   ```bash
   ln -s ~/.claude/conductor/conductor.sh ~/conductor
   ```

3. **Adicione ao PATH (~/.bashrc ou ~/.zshrc):**
   ```bash
   export PATH="$HOME:$PATH"
   ```

4. **Recarregue e teste:**
   ```bash
   source ~/.bashrc
   conductor status
   ```

## ✅ Testar Instalação Global

### Teste 1: Ver Skills Globais
```bash
ls ~/.claude/skills/
```

Deve mostrar 8 diretórios conductor*.

### Teste 2: Testar Comando de Barra
Em qualquer projeto (não precisa ser o Tensiometro):

```bash
# Entre em qualquer outro projeto
cd ~/outro-projeto

# Execute
/conductor-status
```

Deve mostrar status do Conductor para aquele projeto.

### Teste 3: Testar via Terminal
```bash
python ~/.claude/conductor/conductor_global.py status
```

## 📂 Estrutura de Projetos com Conductor

Qualquer projeto pode usar o Conductor:

```
qualquer-projeto/
├── conductor/              # Criado automaticamente pelo setup
│   ├── product.md
│   ├── tech-stack.md
│   ├── workflow.md
│   ├── tracks.md
│   └── tracks/
│       └── {track_id}/
│           ├── spec.md
│           ├── plan.md
│           └── metadata.json
│
└── (seus arquivos de projeto)
```

## 🔄 Atualizar Instalação Global

Para atualizar o Conductor globalmente:

```bash
# Entre no projeto Tensiometro (onde está o código fonte)
cd E:\PycharmProjects\Tensiometro

# Copiar atualizações para o global
cp -r claude-conductor/* ~/.claude/conductor/
cp -r .claude/skills/conductor* ~/.claude/skills/
```

## 🗑️ Desinstalar

Para remover a instalação global:

```bash
# Remover skills
rm -rf ~/.claude/skills/conductor*

# Remover código
rm -rf ~/.claude/conductor

# Remover do PATH (se adicionou)
# Editar ~/.bashrc, ~/.zshrc ou variáveis de ambiente do Windows
```

## 📖 Comandos Disponíveis

| Comando de Barra | Comando CLI | Descrição |
|-----------------|-------------|-----------|
| `/conductor-setup` | `conductor setup` | Inicializa o sistema |
| `/conductor-status` | `conductor status` | Mostra status das tracks |
| `/conductor-new` | `conductor new` | Cria nova track |
| `/conductor-implement` | `conductor implement` | Executa track |
| `/conductor-revert` | `conductor revert` | Reverte track |
| `/conductor-update` | `conductor update` | Atualiza docs |
| `/conductor-archive` | `conductor archive` | Arquiva track |

## 🎯 Exemplo de Uso em Novo Projeto

```bash
# 1. Entre em um novo projeto
cd ~/novo-projeto

# 2. Inicialize o Conductor
/conductor-setup

# Responda às perguntas...

# 3. Crie uma nova track
/conductor-new

# 4. Implemente
/conductor-implement track=feature_xyz

# 5. Verifique progresso
/conductor-status
```

## 💡 Dicas

1. **Comandos de barra vs CLI:**
   - Comandos de barra (`/conductor-*`) funcionam apenas no Claude Code
   - Comando CLI (`conductor`) funciona em qualquer terminal
   - Ambos usam o código global

2. **Projetos existentes:**
   - O Conductor funciona em projetos existentes
   - Apenas execute `/conductor-setup` para iniciar
   - Não interfere em seus arquivos existentes

3. **Múltiplos projetos:**
   - Cada projeto tem seu próprio `conductor/`
   - O código é compartilhado globalmente
   - Skills funcionam em todos os projetos

## ✅ Status da Instalação

- ✅ Skills globais instalados: 8 comandos
- ✅ Código global copiado
- ✅ Wrappers criados (Windows e Unix)
- ✅ Testado e funcionando

**Versão:** 1.0.0
**Data:** 2026-01-11
**Local:** `C:\Users\sense\.claude\`

---

**O Claude Conductor agora está instalado globalmente!** 🎉

Use em qualquer projeto com `/conductor-*` ou `conductor <comando>`.
