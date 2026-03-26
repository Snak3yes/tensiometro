# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Tensiometro** - Sistema AOI industrial para inspeção de stencils de pasta de solda em manufatura SMT.

**Funcionalidades:**
- Medição de tensão superficial via tensiômetro AS-120N (RS-232)
- Inspeção visual de aberturas de stencil (OpenCV)
- Controle CNC via Delta PLC (Modbus TCP)
- Rastreabilidade com SQLite e relatórios PDF

**Status:** ~99% completo | **Versão:** 0.4.0 | **Tech:** Python 3.x + PyQt6 + OpenCV + SQLite

**Filosofia:** SOLID, TDD, documentação como fonte de verdade.

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
│   └── database/      # Persistência SQLite
│
├── consumo_lib/       # GUI PyQt6 (~166 files, ~48k lines)
│   ├── tabs/          # Abas principais
│   ├── widgets/       # Componentes UI
│   ├── dialogs/       # Diálogos
│   └── ui/            # Design System
│
└── main.py            # Entry point
```

### Critical Rules

| Regra | Descrição |
|-------|-----------|
| **Separação** | Business logic → `aoi_lib/`, UI → `consumo_lib/` |
| **Main Window** | É ORQUESTRADOR apenas - NUNCA adicionar lógica de negócio |
| **Design System** | PROIBIDO estilo inline/hardcoded - usar tokens |

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
| `tabs/` | 8 abas principais (Câmera, Tensão, Inspeção, etc.) |
| `dialogs/` | Diálogos modais, Engineering Wizard |
| `widgets/` | Componentes reutilizáveis |
| `ui/` | **Design System** (tokens, componentes padrão) |

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

❌ **PROIBIDO:** `.setStyleSheet()`, valores hardcoded (`#4CAF50`, `45px`), `QFont()` manual

✅ **OBRIGATÓRIO:** Tokens (`COLORS.*`, `TYPO.*`, `DIM.*`, `SPACE.*`) e componentes padrão (`StandardButton`, etc.)

### Exemplos

```python
# ❌ ERRADO
btn.setStyleSheet("background-color: #4CAF50;")
btn.setMinimumHeight(45)

# ✅ CORRETO
from consumo_lib.ui import COLORS, DIM
from consumo_lib.ui.widget_standards import StandardButton

btn = StandardButton("Salvar", variant="primary-green")
```

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
- `docs/features/` - Features documentadas
- `conductor/workflow.md` - Protocolo de desenvolvimento
- `README.md` - Visão geral do projeto

**SOLID Reports:**
- `docs/reports/SOLID_SCORE_FINAL_PHASE2.md` - Score 97/100

---

**Last Updated:** 2026-03-26 | **Version:** 0.4.0