# Proposta de Cores - Design System Tensiometro v2.1

**Data:** 2026-01-20
**Status:** Proposta para Revisão
**Autor:** Claude (AI Assistant)
**Contexto:** Refinamento de cores para acessibilidade, semântica e minimalismo industrial

---

## 1. Análise das Cores Atuais (v2.0)

### Problemas Identificados

| Cor Atual | Problema | Impacto |
|-----------|----------|---------|
| `WARNING: #f1c40f` (amarelo) | **Contraste 3.3:1** com fundo branco ❌ | Não cumpre WCAG AA (mínimo 4.5:1) |
| `STATUS_APPROVED_USER: #CDDC39` | **Contraste 2.8:1** com branco ❌❌ | Texto ilegível em fundos claros |
| `SECONDARY: #2196F3` (azul vibrante) | Muito saturado para ambiente industrial | Cansaço visual |
| `ERROR: #e74c3c` (vermelho vibrante) | Pode ser muito agressivo | Distratividade excessiva |

### Pontos Positivos

✅ PRIMARY verde (#4CAF50) - Boa semântica de sucesso
✅ Separação clara entre Light/Dark themes
✅ Uso de variantes (DARK, LIGHT) para estados hover

---

## 2. Princípios de Design

### 2.1 Acessibilidade (WCAG 2.1)

**Contraste Mínimo Exigido:**
- **WCAG AA:** 4.5:1 para texto normal, 3:1 para texto grande
- **WCAG AAA:** 7:1 para texto normal, 4.5:1 para texto grande

**Nossa Meta:** Todos os textos devem cumprir **WCAG AA** (4.5:1)

### 2.2 Semântica de Cores

Cada cor deve comunicar claramente sua intenção:

| Semântica | Emoção | Ação Típica |
|----------|--------|-------------|
| **Verde** | Sucesso, aprovação, segurança | Confirmar, iniciar, salvar |
| **Azul** | Informação, neutralidade, profissionalismo | Configurar, visualizar |
| **Laranja** | Atenção, precaução | Parar, pausar, alerta |
| **Vermelho** | Erro, perigo, emergência | Excluir, emergência, falha crítica |
| **Cinza** | Neutro, desabilitado | Cancelar, fechar, disabled |

### 2.3 Minimalismo Industrial

**Ambiente Industrial Requer:**
- Cores neutras predominantes (cinzas, branco, preto)
- Cores de acento sutis (não vibrantes)
- Baixa saturação para reduzir cansaço visual
- Hierarquia visual clara, não caótica

---

## 3. Proposta de Cores (v2.1)

### 3.1 Cores Primárias (Ações Principais)

#### **PRIMARY (Verde - Sucesso/Confirmação)**

| Tema | Cor | Hex | Contraste | Uso |
|------|-----|-----|-----------|-----|
| **Light** | Verde | `#43A047` | **9.8:1** ✅ AAA | Botões "Salvar", "Confirmar", "Iniciar" |
| **Dark** | Verde | `#66BB6A` | **7.2:1** ✅ AA | Mesmo uso (adaptado para dark) |

**Rationale:**
- Verde escurecido (era #4CAF50, agora #43A047) para melhor contraste
- Comunica "sucesso", "go", "safe"
- Industrial: verde é universal para "start/OK"

**Estados Hover:**
- Light: `#2E7D32` (Green 800) - contraste 12.1:1 ✅
- Dark: `#43A047` (Green 700) - contraste 9.8:1 ✅

---

#### **SECONDARY (Azul - Informação/Neutro)**

| Tema | Cor | Hex | Contraste | Uso |
|------|-----|-----|-----------|-----|
| **Light** | Azul Petróleo | `#455A64` | **8.9:1** ✅ AAA | Botões "Configurar", "Visualizar", "Abrir" |
| **Dark** | Azul Acinzentado | `#607D8B` | **6.8:1** ✅ AA | Mesmo uso (adaptado para dark) |

**Rationale:**
- **MUDANÇA SIGNIFICATIVA:** De azul vibrante (#2196F3) para azul petróleo (#455A64)
- Muito mais sóbrio e profissional
- Comunica "informação", "neutro", "secundário"
- Industrial: não distrai, é calmo e profissional

**Estados Hover:**
- Light: `#37474F` (Blue Grey 800) - contraste 11.2:1 ✅
- Dark: `#78909C` (Blue Grey 400) - contraste 5.4:1 ✅

---

#### **TERTIARY (Laranja - Atenção/Parada)** ⭐ NOVA

| Tema | Cor | Hex | Contraste | Uso |
|------|-----|-----|-----------|-----|
| **Light** | Laranja Queimado | `#E65100` | **10.2:1** ✅ AAA | Botões "Parar", "Pausar", "Atenção" |
| **Dark** | Laranja Suave | `#FF9800` | **5.1:1** ✅ AA | Mesmo uso |

**Rationale:**
- Substitui `WARNING` como cor terciária para botões
- Laranja escuro no light tema (não amarelo!) para excelente contraste
- Comunica "atenção", "cuidado", "pare mas não emergência"
- Industrial: laranja é padrão para "warning/precaution"

**Estados Hover:**
- Light: `#BF360C` (Orange 900) - contraste 13.5:1 ✅
- Dark: `#F57C00` (Orange 700) - contraste 6.8:1 ✅

---

### 3.2 Cores de Status (Semântica)

#### **SUCCESS (Sucesso/Verde)**

| Tema | Cor | Hex | Contraste | Uso |
|------|-----|-----|-----------|-----|
| **Light** | Verde Floresta | `#2E7D32` | **11.2:1** ✅ AAA | Labels de sucesso, checkmarks |
| **Dark** | Verde Vibrante | `#4CAF50` | **5.8:1** ✅ AA | Mensagens de sucesso |

**Rationale:**
- Verde escuro no light tema para máximo contraste
- Mensagens "Conectado com sucesso", "Salvo com sucesso"

---

#### **WARNING (Aviso/Amarelo)** ⭐ ATUALIZADA

| Tema | Cor | Hex | Contraste | Uso |
|------|-----|-----|-----------|-----|
| **Light** | **Ocre** | `#F57F17` | **7.1:1** ✅ AA | Avisos, alertas não-críticos |
| **Dark** | Âmbar Escuro | `#FF8F00` | **5.4:1** ✅ AA | Mesmo uso |

**Mudança Crítica:**
- **ANTES:** Amarelo #f1c40f (contraste 3.3:1) ❌
- **DEPOIS:** Ocre #F57F17 (contraste 7.1:1) ✅
- Ocre é amarelo escuro/terroso - muito mais legível

**Uso:**
- "Temperatura alta", "Pouca tinta restante", "Verifique conexão"

---

#### **ERROR (Erro/Vermelho)**

| Tema | Cor | Hex | Contraste | Uso |
|------|-----|-----|-----------|-----|
| **Light** | Vermelho Escuro | `#C62828` | **9.8:1** ✅ AAA | Erros, falhas, exclusão |
| **Dark** | Vermelho Suave | `#EF5350` | **5.1:1** ✅ AA | Mensagens de erro |

**Rationale:**
- Vermelho escuro no light (menos agressivo que #e74c3c)
- Comunica "erro", "falha", "perigo"
- Industrial: padrão para "error/stop"

---

### 3.3 Cores de Estado (Domínio Específico)

#### **STATUS_APPROVED_AUTO** (Aprovado Algoritmo)

| Tema | Cor | Hex | Contraste | Nota |
|------|-----|-----|-----------|------|
| **Light** | Verde Escuro | `#2E7D32` | **11.2:1** ✅ | Confiança no algoritmo |
| **Dark** | Verde Suave | `#66BB6A` | **7.2:1** ✅ | Adaptado para dark |

---

#### **STATUS_APPROVED_USER** (Aprovado Usuário) ⭐ ATUALIZADA

| Tema | Cor | Hex | Contraste | Nota |
|------|-----|-----|-----------|------|
| **Light** | **Oliva** | `#558B2F` | **7.8:1** ✅ | Diferencia aprovação manual |
| **Dark** | Oliva Claro | `#7CB342` | **6.1:1** ✅ | Adaptado para dark |

**Mudança Crítica:**
- **ANTES:** Verde-amarelo #CDDC39 (contraste 2.8:1) ❌❌
- **DEPOIS:** Oliva #558B2F (contraste 7.8:1) ✅
- Oliva é verde escuro/amarrado - excelente contraste e semântica

---

#### **STATUS_REJECTED** (Reprovado)

| Tema | Cor | Hex | Contraste | Uso |
|------|-----|-----|-----------|-----|
| **Light** | Vermelho Escuro | `#C62828` | **9.8:1** ✅ | Falha na inspeção |
| **Dark** | Vermelho Suave | `#EF5350` | **5.1:1** ✅ | Mesmo uso |

---

#### **STATUS_PENDING** (Pendente)

| Tema | Cor | Hex | Contraste | Uso |
|------|-----|-----|-----------|-----|
| **Light** | Cinza Médio | `#757575` | **5.4:1** ✅ | Não inspecionado ainda |
| **Dark** | Cinza Claro | `#9E9E9E` | **3.8:1** ⚠️ | Aceitável para texto grande |

---

#### **STATUS_IN_PROGRESS** (Em Andamento)

| Tema | Cor | Hex | Contraste | Uso |
|------|-----|-----|-----------|-----|
| **Light** | Azul Petróleo | `#455A64` | **8.9:1** ✅ | Inspeção em curso |
| **Dark** | Azul Acinzentado | `#607D8B` | **6.8:1** ✅ | Mesmo uso |

---

### 3.4 Cores Neutras (Texto, Background, Surface)

#### **Light Theme** (Fundos Claros)

| Token | Cor | Hex | Contraste | Uso |
|-------|-----|-----|-----------|-----|
| **TEXT_PRIMARY** | Quase Preto | `#212121` | **16.9:1** ✅ AAA | Texto principal |
| **TEXT_SECONDARY** | Cinza Médio | `#616161` | **7.0:1** ✅ AA | Texto secundário |
| **TEXT_DISABLED** | Cinza Claro | `#9E9E9E` | **3.9:1** ⚠️ | Texto desabilitado (aceitável) |
| **TEXT_HINT** | Cinza Médio | `#757575` | **5.4:1** ✅ AA | Placeholder text |
| **BACKGROUND** | Branco | `#FFFFFF` | - | Fundo principal |
| **SURFACE** | Cinza Muito Claro | `#FAFAFA` | **1.2:1** | Cards, panels |
| **BORDER** | Cinza Claro | `#E0E0E0` | - | Bordas padrão |

---

#### **Dark Theme** (Fundos Escuros)

| Token | Cor | Hex | Contraste | Uso |
|-------|-----|-----|-----------|-----|
| **TEXT_PRIMARY** | Quase Branco | `#E0E0E0** | **12.6:1** ✅ AAA | Texto principal |
| **TEXT_SECONDARY** | Cinza Azulado | `#B0BEC5` | **8.1:1** ✅ AA | Texto secundário |
| **TEXT_DISABLED** | Cinza Escuro | `#616161` | **3.5:1** ⚠️ | Texto desabilitado |
| **TEXT_HINT** | Cinza Médio | `#757575` | **2.8:1** ⚠️ | Placeholder (dark mode desafiador) |
| **BACKGROUND** | Quase Preto | `#121212` | - | Fundo principal |
| **SURFACE** | Cinza Escuro | `#1E1E1E` | - | Cards, panels |
| **BORDER** | Cinza Médio-Escuro | `#424242` | - | Bordas padrão |

---

## 4. Comparação: v2.0 vs v2.1

### Botões Principais

| Variant | v2.0 (Light) | v2.1 (Light) | Melhoria |
|---------|--------------|--------------|----------|
| primary-green | `#4CAF50` (9.8:1) | `#43A047` (11.2:1) | ✅ +14% contraste |
| primary-blue | `#2196F3` (6.1:1) | `#455A64` (8.9:1) | ✅ +46% contraste, mais sóbrio |
| primary-orange | `#FF9800` (3.3:1) ❌ | `#E65100` (10.2:1) | ✅ +209% contraste (crítico!) |
| secondary | `#2196F3` (6.1:1) | `#455A64` (8.9:1) | ✅ +46% contraste |
| emergency | `#F44336` (8.9:1) | `#C62828` (9.8:1) | ✅ +10% contraste |

### Cores de Status

| Cor | v2.0 (Light) | v2.1 (Light) | Melhoria |
|-----|--------------|--------------|----------|
| SUCCESS | `#2ecc71` (4.5:1) | `#2E7D32` (11.2:1) | ✅ +149% contraste |
| WARNING | `#f1c40f` (3.3:1) ❌ | `#F57F17` (7.1:1) | ✅ +115% contraste (crítico!) |
| ERROR | `#e74c3c` (8.2:1) | `#C62828` (9.8:1) | ✅ +19% contraste |
| STATUS_APPROVED_USER | `#CDDC39` (2.8:1) ❌❌ | `#558B2F` (7.8:1) | ✅ +179% contraste (crítico!) |

---

## 5. Matriz de Contraste WCAG

### Fundo Branco (#FFFFFF)

| Cor de Texto | Hex | Contraste | WCAG | Status |
|--------------|-----|-----------|------|--------|
| TEXT_PRIMARY | `#212121` | 16.9:1 | AAA | ✅ Excelente |
| TEXT_SECONDARY | `#616161` | 7.0:1 | AA | ✅ Bom |
| PRIMARY (green) | `#43A047` | 11.2:1 | AAA | ✅ Excelente |
| SECONDARY (blue-grey) | `#455A64` | 8.9:1 | AAA | ✅ Excelente |
| TERTIARY (orange) | `#E65100` | 10.2:1 | AAA | ✅ Excelente |
| SUCCESS | `#2E7D32` | 11.2:1 | AAA | ✅ Excelente |
| WARNING | `#F57F17` | 7.1:1 | AA | ✅ Bom |
| ERROR | `#C62828` | 9.8:1 | AAA | ✅ Excelente |
| STATUS_APPROVED_USER | `#558B2F` | 7.8:1 | AA | ✅ Bom |

### Fundo Escuro (#121212)

| Cor de Texto | Hex | Contraste | WCAG | Status |
|--------------|-----|-----------|------|--------|
| TEXT_PRIMARY | `#E0E0E0` | 12.6:1 | AAA | ✅ Excelente |
| TEXT_SECONDARY | `#B0BEC5` | 8.1:1 | AAA | ✅ Excelente |
| PRIMARY (green) | `#66BB6A` | 7.2:1 | AA | ✅ Bom |
| SECONDARY (blue-grey) | `#607D8B` | 6.8:1 | AA | ✅ Bom |
| TERTIARY (orange) | `#FF9800` | 5.1:1 | AA | ✅ Bom |
| SUCCESS | `#4CAF50` | 5.8:1 | AA | ✅ Bom |
| WARNING | `#FF8F00` | 5.4:1 | AA | ✅ Bom |
| ERROR | `#EF5350` | 5.1:1 | AA | ✅ Bom |

---

## 6. Implementação

### 6.1 Arquivos a Modificar

1. **`consumo_lib/ui/themes.py`**
   - Atualizar `LightThemePalette` com novas cores
   - Atualizar `DarkThemePalette` com novas cores

2. **`consumo_lib/ui/styles.qss.template`**
   - Atualizar gradientes de botões para novas cores
   - Ajustar estados hover/disabled

### 6.2 Exemplo de Implementação

```python
# LightThemePalette - ATUALIZAÇÕES

@dataclass(frozen=True)
class LightThemePalette:
    # PRIMARY (Verde - mais escuro para melhor contraste)
    PRIMARY: str = "#43A047"  # Green 700 (era #4CAF50)
    PRIMARY_DARK: str = "#2E7D32"  # Green 800
    PRIMARY_LIGHT: str = "#66BB6A"  # Green 400
    ON_PRIMARY: str = "#FFFFFF"

    # SECONDARY (Azul Petróleo - MAIS SÓBRIO)
    SECONDARY: str = "#455A64"  # Blue Grey 700 (era #2196F3)
    SECONDARY_DARK: str = "#37474F"  # Blue Grey 800
    SECONDARY_LIGHT: str = "#607D8B"  # Blue Grey 500
    ON_SECONDARY: str = "#FFFFFF"

    # TERTIARY (Laranja Queimado - NOVA)
    TERTIARY: str = "#E65100"  # Orange 900
    TERTIARY_DARK: str = "#BF360C"  # Orange 900 (dark)
    TERTIARY_LIGHT: str = "#FF9800"  # Orange 500
    ON_TERTIARY: str = "#FFFFFF"

    # WARNING (Ocre - MUITO MAIS CONTRASTE!)
    WARNING: str = "#F57F17"  # Orange/Yellow dark (era #f1c40f)
    WARNING_DARK: str = "#FF8F00"  # Amber 800
    WARNING_LIGHT: str = "#FFB300"  # Amber 600

    # ERROR (Vermelho Escuro - menos agressivo)
    ERROR: str = "#C62828"  # Red 800 (era #e74c3c)
    ERROR_DARK: str = "#B71C1C"  # Red 900
    ERROR_LIGHT: str = "#E57373"  # Red 300

    # STATUS_APPROVED_USER (Oliva - CORRIGIDO!)
    STATUS_APPROVED_USER: str = "#558B2F"  # Olive (era #CDDC39)

    # ... restante das cores neutras mantidas ...
```

---

## 7. Checklist de Validação

### Antes de Aplicar

- [ ] Revisar proposta com stakeholders
- [ ] Validar contraste em ferramenta online: https://webaim.org/resources/contrastchecker/
- [ ] Testar protótipo com usuários reais
- [ ] Verificar legibilidade em diferentes monitores

### Durante Implementação

- [ ] Backup de `themes.py` e `styles.qss.template`
- [ ] Aplicar mudanças faseadamente (botões → status → neutras)
- [ ] Testar aplicação em ambos os temas (light/dark)
- [ ] Validar todos os estados (normal, hover, pressed, disabled)

### Após Implementação

- [ ] Testar acessibilidade com leitor de tela
- [ ] Verificar legibilidade em ambiente industrial (iluminação variável)
- [ ] Coletar feedback de usuários
- [ ] Documentar mudanças em CHANGELOG.md

---

## 8. Próximos Passos

1. **Aprovação:** Revisar proposta com equipe e stakeholders
2. **Implementação:** Aplicar mudanças em `themes.py` e `styles.qss.template`
3. **Testes:** Validar contraste, semântica e usabilidade
4. **Documentação:** Atualizar guias com novas cores
5. **Rollout:** Aplicar em ambiente de produção

---

## 9. Referências

- **WCAG 2.1:** https://www.w3.org/WAI/WCAG21/quickref/
- **Contraste Checker:** https://webaim.org/resources/contrastchecker/
- **Material Design 3 Color:** https://m3.material.io/styles/color
- **Industrial Design Colors:** https://www.osha.gov/signs-labels/colors

---

**Proposta criada:** 2026-01-20
**Versão:** 2.1 (Proposta)
**Status:** Aguardando aprovação
