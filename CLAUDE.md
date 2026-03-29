# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Tensiometro** - Sistema AOI industrial para inspeção de stencils de pasta de solda em manufatura SMT.

**Funcionalidades:**
- Medição de tensão superficial via tensiômetro AS-120N (RS-232)
- Inspeção visual de aberturas de stencil (OpenCV)
- Controle CNC via Delta PLC (Modbus TCP)
- Rastreabilidade com SQLite e relatórios PDF

**Status:** ~99% completo | **Versão:** 0.5.0 (release/v0.5-tension) | **Tech:** Python 3.x + PyQt6 + OpenCV + SQLite

**Branch atual:** `test/ui-adjustments-70-30` - Ajustes de UI para matching com proposta SVG

**Filosofia:** SOLID, TDD, documentação como fonte de verdade.

---

## Release v0.5-tension (2026-03-29)

**Objetivo:** Versão de entrega para cliente com funcionalidade de medição de tensão apenas.

### Alterações Principais

| Item | Status |
|------|--------|
| Aba "Posições e Rotinas" | REMOVIDA |
| Groupbox "Ações Rápidas" | REMOVIDO |
| Groupbox "Conexão" (janela principal) | REMOVIDA → Diálogo dedicado |
| Aba "Movimento" | Dialog não-modal (Ctrl+M) |
| Aba "Monitor CLP" | Dialog não-modal (Ctrl+L) |
| Aba "Conexões" (em Preferências) | REMOVIDA |
| **Aba "Rastreabilidade"** | **REMOVIDA → Dialog não-modal (Ctrl+R)** |
| **QTabWidget** | **REMOVIDO - TensionMeasurementTab diretamente na janela** |
| Menu Receitas | REMOVIDO (funcionalidade não implementada) |
| Campo "Stencil Atual" (menu Cadastros) | REMOVIDO |
| Emojis na UI | TODOS REMOVIDOS |
| Diálogo "Preferências" | Renomeado para "Preferências do Sistema" |
| TabFactory | REMOVIDO da inicialização (MainUIBuilder cria tab diretamente) |

### UI Adjustments - Aba "Medição de Tensão" (2026-03-29)

**Branch:** `test/ui-adjustments-70-30`

Ajustes para matching com proposta SVG (`docs/ui_proposals/proposta_1_revisada_70_30_real.svg`):

| Componente | Antes | Depois |
|------------|-------|--------|
| Tree header | Altura padrão | 24px min-height, 11px font |
| Tree items | 45px altura | 20px min-height, 4px padding |
| Filter bar | Altura variável | 36px fixo, campos 20px |
| Groupbox "Critérios" | QHBoxLayout 1 linha | QGridLayout 3 linhas |
| Spinboxes | 26px (global) | 50x14px com setas CSS |
| Botão "Receita" | Fixo 60px | Ocupa toda largura |

**Notas técnicas:**
- Spinboxes usam CSS borders para setas visíveis (triângulos)
- Global stylesheet `min-height: 26px` sobrescrito inline
- QGridLayout para melhor distribuição dos campos

### Novos Arquivos

- `consumo_lib/dialogs/movement_dialog.py` - Diálogo de controle CNC (não-modal, Ctrl+M)
- `consumo_lib/dialogs/plc_monitor_dialog.py` - Diálogo de monitoramento PLC (não-modal, Ctrl+L)
- `consumo_lib/dialogs/connection_dialog.py` - Diálogo de conexão PLC (não-modal)
- `consumo_lib/dialogs/tracking_dialog.py` - Diálogo de rastreabilidade (não-modal, Ctrl+R)
- `consumo_lib/dialogs/tension_criteria_dialog.py` - Diálogo de critérios de tensão globais
- `consumo_lib/managers/tension_criteria_manager.py` - Gerenciador de critérios globais
- `tools/populate_test_stencils.py` - Script para popular stencils de teste no banco

### Menu Consolidado (5 menus)

| Menu | Items |
|------|-------|
| **Arquivo** | Sair |
| **Cadastros** | Gerenciar Stencils, Novo Stencil |
| **Relatórios** | Tensão, Stencil, Período, Configurações |
| **Ferramentas** | Rastreabilidade (Ctrl+R), Nova Medição de Tensão, Critérios de Tensão, Controle de Movimento (Ctrl+M), Monitor CLP (Ctrl+L), Calibração CNC, Conexões, Preferências (Ctrl+,) |
| **Sistema** | Configurações de Autenticação, Configurações de Tema, Verificar Permissões, Sobre |

### Conexão PLC

**IMPORTANTE:** A conexão PLC agora é feita via diálogo dedicado:
- **Menu:** Ferramentas → Conexões...
- **Características:** Não-modal, permanece no topo, permite operar janela principal
- **Groupbox "Conexão":** Removido da janela principal (era redundante)
- **Aba "Conexões" em Preferências:** Removida (configurações redundantes + câmera não usada)

### Branches

| Branch | Propósito |
|--------|-----------|
| `main` | Desenvolvimento principal (com inspeção visual) |
| `release/v0.5-tension` | Release para cliente (medição de tensão apenas) |
| `test/ui-adjustments-70-30` | Ajustes de UI para matching com proposta SVG |

**Ver detalhes:** `docs/reports/RELEASE_v0.5-tension.md`

---

## Git Remotes (Push Duplo)

**⚠️ IMPORTANTE:** Sempre que executar `git push`, o código será enviado para **dois repositórios automaticamente**:

| Remote | URL | Tipo |
|--------|-----|------|
| **origin** (push 1) | `https://github.com/RONALDBUZAGLO/tensiometro.git` | GitHub (HTTPS) |
| **origin** (push 2) | `https://gitlab.com/visao-computacional/DGB-Visao-Computacional.git` | GitLab (HTTPS) |
| **gitlab** | `https://gitlab.com/visao-computacional/DGB-Visao-Computacional.git` | GitLab (alternativo) |

### Comandos Git

```bash
# Push para ambos (automático)
git push origin main

# Push para apenas um repositório (se necessário)
git push gitlab main  # Apenas GitLab
```

### Autenticação GitLab
- **HTTPS:** Usa Personal Access Token (não senha)
- Para criar token: GitLab → Settings → Access Tokens → scopes: `write_repository`

---

## Quick Start

```bash
# Executar aplicação
.venv/Scripts/python.exe main.py

# Testes
pytest tests/ -v                           # Todos
pytest tests/ -v -m "not slow and not hardware"  # Rápidos

# Cobertura
pytest tests/ --cov=aoi_lib --cov=consumo_lib --cov-report=html:htmlcov
```

**Dependências principais:** PyQt6, opencv-python, pymodbus, pyserial, reportlab, matplotlib, pytest

---

## Architecture Overview

### Two-Package Architecture

```
tensiometro/
├── aoi_lib/           # Core business logic (~106 files, ~30k lines)
│   ├── tensiometer/   # Medição de tensão
│   ├── plc/           # Controle PLC (interfaces + controllers)
│   ├── gerber_core/   # Parser Gerber RS-274X (MVC)
│   ├── auth/          # Autenticação
│   ├── database/      # Persistência SQLite
│   ├── report/        # Geração de relatórios PDF
│   ├── reports/       # Configurações de relatórios
│   └── utils/         # Utilitários compartilhados
│
├── consumo_lib/       # GUI PyQt6 (~166 files, ~48k lines)
│   ├── tabs/          # Abas principais
│   ├── widgets/       # Componentes UI
│   ├── dialogs/       # Diálogos
│   ├── ui/            # Design System
│   ├── controllers/   # Controladores MVC
│   ├── coordinators/  # Orquestradores de fluxo
│   ├── facades/       # Fachadas de acesso
│   ├── factories/     # Fábricas de objetos
│   ├── handlers/      # Manipuladores de eventos
│   ├── interfaces/    # Interfaces/contratos
│   ├── managers/      # Gerenciadores de estado
│   ├── models/        # Modelos de dados
│   ├── services/      # Serviços de aplicação
│   ├── threads/       # Workers QThread
│   ├── ui_builders/   # Construtores de UI
│   └── utils/         # Utilitários GUI
│
└── main.py            # Entry point
```

### Critical Rules

| Regra | Descrição |
|-------|-----------|
| **Separação** | Business logic → `aoi_lib/`, UI → `consumo_lib/` |
| **Main Window** | É ORQUESTRADOR apenas - NUNCA adicionar lógica de negócio |
| **Design System** | PROIBIDO estilo inline/hardcoded - usar tokens |
| **Window Size** | Tamanho FIXO 1200×800px - monitor predefinido da máquina |

### Main Window Dimensions

**REGRA FIXA:** A janela principal deve ter tamanho **1200×800 pixels**.

| Restrição | Valor | Motivo |
|-----------|-------|--------|
| Largura | 1200px (fixo) | Monitor industrial predefinido |
| Altura | 800px (fixo) | Monitor industrial predefinido |
| Redimensionamento | **Desabilitado** | Máquina dedicada |

**⚠️ NÃO adicionar `setMinimumSize()` menor que 1200×800 ou permitir resize.**

---

## Hardware Integration

### PLC (Modbus TCP)
- **Endereço:** 192.168.1.5:502
- **X/Y Interpolation:** Ambos usam coil M1050 (NÃO separados)
- **Eixos:** X (M1000, D3000), Y (M500, D3200), Z (M1500, D3400)

### Tensiômetro AS-120N
- **Serial:** RS-232, 2400 baud, 8N1
- **Protocolo:** Request `0x20`, Response 9 bytes

### Câmera
- USB OpenCV, FOV fixo ~34mm x 34mm

### Conversões
```python
# Pulso → mm
pulses_per_mm = 800 / 10.0  # = 80.0

# Pixel → mm (FOV calibration)
mm_per_pixel_x = 34.0 / 640  # ≈ 0.053
```

---

## Key Modules

### aoi_lib - Core

| Módulo | Propósito | Status SOLID |
|--------|-----------|--------------|
| `tensiometer/` | Medição, protocolo serial, orquestração | 96/100 |
| `plc/` | Interfaces + Controllers segregados | 97/100 |
| `gerber_core/` | Parser + MVC + Command Pattern | 100/100 |
| `fiducial_*` | Alinhamento, matching, transformações | 96/100 |
| `auth/` | Autenticação com roles | - |
| `database/` | Repository Pattern (SQLite) | - |

### consumo_lib - GUI

| Módulo | Propósito |
|--------|-----------|
| `tabs/` | TensionMeasurementTab (única aba, colocada diretamente na janela) |
| `dialogs/` | Diálogos modais e não-modais (Tracking, Movement, PLC Monitor, etc.) |
| `widgets/` | Componentes reutilizáveis |
| `ui/` | **Design System** (tokens, componentes padrão) |

### Interface Principal (v0.5-tension)

**Janela principal sem QTabWidget:**
- `TensionMeasurementTab` colocada diretamente no layout
- `StencilIdentificationWidget` acessível via `TrackingDialog` (Ctrl+R)
- `MovementControlWidget` oculto, acessível via `MovementDialog` (Ctrl+M)

---

## Data Flows Principais

### Medição de Tensão
```
Stencil → Recipe → Grid de pontos → CNC move → Tensiômetro mede → Classifica OK/WARN/NOK
```

### Inspeção Visual
```
Gerber → Fiduciais → Mosaico → Alinha → Renderiza máscaras → Compara → Classifica OK/PARTIAL/BLOCK
```

### Click-to-Move
```
Click → Pixel → mm (FOV) → pulsos → PLC move_absolute
```

---

## Design System (CRÍTICO)

**VER DOCUMENTAÇÃO COMPLETA:** `docs/design_system/`

### Regra Zero Tolerância

❌ **PROIBIDO:** `.setStyleSheet()` em botões, valores hardcoded (`#4CAF50`, `45px`), `QFont()` manual

✅ **OBRIGATÓRIO:** Tokens (`COLORS.*`, `TYPO.*`, `DIM.*`, `SPACE.*`) e componentes padrão (`StandardButton`, etc.)

### StandardButton - Uso Correto (v4.0 Microsoft Style)

```python
from consumo_lib.ui.widget_standards import StandardButton

# Botões de diálogo
btn_confirm = StandardButton("Confirmar", variant="primary-green", semantic_size="dialog-primary")
btn_cancel = StandardButton("Cancelar", variant="secondary", semantic_size="dialog-secondary")

# Botões de ação emergência
btn_stop = StandardButton("Parar", variant="emergency", semantic_size="dialog-primary")

# Botões de movimento
btn_up = StandardButton("↑", semantic_size="directional")
btn_z = StandardButton("Z+", semantic_size="z-axis")

# Botões inline
btn_action = StandardButton("Aplicar", variant="primary-blue", semantic_size="inline-primary")
```

### Variantes de Botão

| Variante | Uso |
|----------|-----|
| `primary-green` | Confirmação, ações principais |
| `primary-blue` | Ações genéricas/secundárias |
| `secondary` | Cancelamento, ações alternativas |
| `emergency` | Stop, emergência, ações destrutivas |

### Semantic Sizes (v4.0 - Microsoft Style Compact)

| Size | Dimensões | Uso |
|------|-----------|-----|
| `dialog-primary` | 28×90px | Botões principais de diálogo |
| `dialog-secondary` | 24×80px | Botões secundários de diálogo |
| `directional` | 32×32px | Botões direcionais (↑↓←→) |
| `z-axis` | 24×32px | Botões eixo Z (Z+, Z-) |
| `inline-primary` | 24×60px | Botões inline |
| `inline-secondary` | 22×55px | Botões inline menores |

### Tokens Principais
```python
COLORS.PRIMARY, COLORS.ERROR, COLORS.SUCCESS, COLORS.WARNING
TYPO.medium(14), TYPO.bold(16)
SPACE.SM (8px), SPACE.MD (16px), SPACE.LG (24px)
DIM.BUTTON_HEIGHT_MD (40px), DIM.RADIUS_MD (8px)
```

---

## Development Patterns

### Error Handling
- Hardware disconnection = **estado esperado**, não exceção
- Return safe defaults, log errors, NEVER raise

### Thread Safety (PyQt6)
- Worker threads → signals → UI updates
- NUNCA atualizar UI diretamente de thread

### Logging
```python
logger.info("✅ PLC conectado")
logger.warning("⚠️ Timeout eixo X")
logger.error("❌ Falha tensiômetro")
```

---

## Configuration

**Arquivo principal:** `config/aoi_config.json`

| Seção | Propósito |
|-------|-----------|
| `cnc` | Parâmetros CNC (steps_per_unit: 80.0) |
| `connections` | PLC host/port, auto_connect |
| `authentication` | Login on startup, default role |
| `engineering_wizard` | Free navigation mode (dev only) |

---

## Testing

- **PLC:** Requer hardware real
- **Tensiômetro:** `python tools/Leitura_Continua.py COM3`
- **Câmera:** Usar vídeo/imagem ao invés de câmera real

---

## Debugging

```python
# Ativar debug
logging.basicConfig(level=logging.DEBUG)

# Verificar hardware
plc.is_connected
camera.is_connected
tensio.is_connected
```

---

## References

**Documentação:**
- `docs/design_system/` - Design System completo
- `docs/architecture/` - Análises de arquitetura
- `docs/guides/` - Guias de desenvolvimento
- `docs/reports/` - Relatórios de progresso
- `conductor/workflow.md` - Protocolo de desenvolvimento
- `README.md` - Visão geral do projeto

**SOLID Reports:**
- `docs/reports/SOLID_SCORE_FINAL_PHASE2.md` - Score 97/100

---

**Last Updated:** 2026-03-29 | **Version:** 0.5.0 | **Branch:** test/ui-adjustments-70-30