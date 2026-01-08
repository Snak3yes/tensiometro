# Análise de Viabilidade - Integração do MovementControlsWidget

**Data:** 2026-01-07
**Analista:** Claude Code
**Status:** ✅ **VIÁVEL COM ADAPTAÇÕES**

---

## 1. Resumo Executivo

O módulo `movement_controls_module/` é **viável para integração** no projeto Tensiômetro, mas requer adaptações para preservar funcionalidades específicas do projeto atual.

### Recomendação

**⚠️ INTEGRAÇÃO POR ADAPTAÇÃO** (não substituição direta)

- ✅ **Usar** o novo módulo como base para controles direcionais
- ✅ **Adicionar** funcionalidades específicas do Tensiômetro (Backlight, Go to Position, Keyboard)
- ✅ **Criar** classe adaptadora para MovementService
- ❌ **NÃO substituir** completamente o widget atual (muitas funcionalidades seriam perdidas)

---

## 2. Comparação Técnica

### 2.1 Módulo Novo (movement_controls_module)

| Característica | Detalhes |
|----------------|----------|
| **Linhas de código** | 710 linhas (312+280+118) |
| **Arquitetura** | Strategy Pattern (extensível) |
| **Dependências** | PyQt6 apenas (independente) |
| **Modos de posição** | "mm" (float) ou "pulses" (int) |
| **Sinais PyQt6** | 5 sinais bem definidos |
| **Origem** | Projeto Inspetor Periférico |
| **Testabilidade** | Alta (módulo independente) |

**Funcionalidades:**
- ✅ Botões direcionais X, Y, Z (6 botões)
- ✅ Modo Step (passo-a-passo)
- ✅ Modo Contínuo (jog)
- ✅ Feed rate configurável
- ✅ Step size configurável
- ✅ Botão STOP/RESET
- ✅ Go to Zero (home)
- ✅ Exibição de posição atual
- ✅ Strategy pattern para extensibilidade

**Sinais emitidos:**
```python
step_move_requested(axis: str, distance: float, feed: float)
jog_start(axis: str, direction: int)
jog_stop(axis: str)
go_to_zero_requested()
emergency_stop_toggled(engaged: bool)
```

### 2.2 Widget Atual (consumo_lib/widgets/movement_control.py)

| Característica | Detalhes |
|----------------|----------|
| **Linhas de código** | 671 linhas |
| **Arquitetura** | Widget monolítico |
| **Dependências** | MovementService, AOIConfigManager, PLCAxisController |
| **Integração** | Totalmente integrado ao projeto |
| **Modos de posição** | mm (float) - convertidos internamente para pulses |
| **Origem** | Desenvolvido para Tensiômetro |
| **Testabilidade** | Média (acoplado ao projeto) |

**Funcionalidades:**
- ✅ Todas as do módulo novo
- ✅ **Botão Backlight** (controle de iluminação Y0.7 do PLC)
- ✅ **Botão Go to Position** (movimento para coordenadas específicas WPos)
- ✅ **Checkbox Keyboard Control** (habilita controle por teclado)
- ✅ **Validação inteligente de feed rate** (ajusta $110, $111 automaticamente)
- ✅ **Suporte GRBL e PLC**
- ✅ **Salva step/feed no JSON** automaticamente
- ✅ **Diálogo Go to Position** com validação

---

## 3. Análise de Diferenças

### 3.1 Funcionalidades Únicas do Widget Atual

| Funcionalidade | Descrição | Impacto se perdida |
|----------------|-----------|-------------------|
| **Backlight** | Controle de iluminação Y0.7 do PLC | 🔴 **ALTO** - Essencial para inspeção visual |
| **Go to Position** | Movimento para coordenadas X,Y específicas | 🟡 **MÉDIO** - Útil para posicionamento preciso |
| **Keyboard Control** | Habilita/desabilita controle por teclado | 🟡 **MÉDIO** - Facilita operação |
| **Feed Rate Auto-Adjust** | Ajusta $110/$111 se feed exceder limite | 🟢 **BAIXO** - Convenience feature |
| **JSON Auto-Save** | Salva step/feed automaticamente | 🟢 **BAIXO** - Já implementado em outro lugar |

### 3.2 Diferenças de Arquitetura

| Aspecto | Módulo Novo | Widget Atual |
|---------|-------------|--------------|
| **Separação de responsabilidades** | ✅ Strategy Pattern | ❌ Monolítico |
| **Testabilidade** | ✅ Alta (independente) | 🟡 Média (acoplado) |
| **Extensibilidade** | ✅ Alta (padrões GOF) | 🟡 Média (herança) |
| **Manutenibilidade** | ✅ Alta (modular) | 🟡 Média (arquivo grande) |
| **Integração com MovementService** | ❌ Não existe | ✅ Completa |

### 3.3 Compatibilidade de Sinais

| Sinal Módulo Novo | Handler Widget Atual | Compatível? |
|-------------------|---------------------|-------------|
| `step_move_requested(axis, distance, feed)` | `MovementService.start_step_move()` | ⚠️ **Requer adaptação** |
| `jog_start(axis, direction)` | `MovementService.start_jog()` | ⚠️ **Requer adaptação** |
| `jog_stop(axis)` | `MovementService.stop_jog()` | ⚠️ **Requer adaptação** |
| `go_to_zero_requested()` | `MovementService.go_to_zero()` | ✅ **Compatível** |
| `emergency_stop_toggled(engaged)` | `on_emergency_stop_toggle()` | ⚠️ **Requer adaptação** |

---

## 4. Estratégias de Integração

### 4.1 Estratégia A: Substituição Completa ❌ **NÃO RECOMENDADA**

**Descrição:** Remover `movement_control.py` e usar apenas `MovementControlsWidget`.

**Vantagens:**
- ✅ Código mais limpo (Strategy Pattern)
- ✅ Módulo independente
- ✅ Redução de linhas

**Desvantagens:**
- ❌ Perda de funcionalidades críticas (Backlight, Go to Position, Keyboard)
- ❌ Reimplementar 200+ linhas de código específico
- ❌ Maior risco de regressão
- ❌ Não aproveita investimentos anteriores

**Conclusão:** ❌ **NÃO RECOMENDADA** - Perda de funcionalidades essenciais.

---

### 4.2 Estratégia B: Adaptação/Wrapper ✅ **RECOMENDADA**

**Descrição:** Criar `MovementControlsAdapter` que:
1. Herda de `MovementControlsWidget` (do módulo)
2. Adiciona funcionalidades específicas do Tensiômetro
3. Adapta sinais para `MovementService`

**Implementação:**

```python
# consumo_lib/widgets/movement_control_v2.py
from movement_controls_module import MovementControlsWidget
from consumo_lib.services import MovementService

class MovementControlsAdapter(MovementControlsWidget):
    """
    Adaptador que adiciona funcionalidades específicas do Tensiômetro
    ao MovementControlsWidget genérico.
    """

    def __init__(self, controller, config_manager, movement_service, parent=None):
        # Inicializa com módulo genérico (position_mode="mm")
        super().__init__(parent=parent, position_mode="mm")

        self.controller = controller
        self.config_manager = config_manager
        self.movement_service = movement_service

        # Adicionar botões específicos do Tensiômetro
        self._add_tensiometro_features()

        # Conectar sinais do módulo genérico ao MovementService
        self._connect_signals_to_service()

    def _add_tensiometro_features(self):
        """Adiciona botões específicos: Backlight, Go to Position, Keyboard"""
        # ... implementação ...

    def _connect_signals_to_service(self):
        """Adapta sinais do módulo genérico para MovementService"""
        self.step_move_requested.connect(self._on_step_move)
        self.jog_start.connect(self._on_jog_start)
        self.jog_stop.connect(self._on_jog_stop)
        self.go_to_zero_requested.connect(self._on_go_to_zero)
        self.emergency_stop_toggled.connect(self._on_emergency_stop)

    def _on_step_move(self, axis, distance, feed):
        """Adapta signal para MovementService"""
        self.movement_service.start_step_move(axis, 1 if distance > 0 else -1, abs(distance), feed)

    # ... demais handlers ...
```

**Vantagens:**
- ✅ Aproveita código testado do módulo (710 linhas)
- ✅ Preserva funcionalidades específicas do Tensiômetro
- ✅ Baixo risco de regressão
- ✅ Mantém compatibilidade com MovementService
- ✅ Pode coexistir com widget atual durante migração

**Desvantagens:**
- ⚠️ Requer criação de classe adaptadora (~150 linhas)
- ⚠️ Precisa testar integração cuidadosamente

**Conclusão:** ✅ **RECOMENDADA** - Melhor equilíbrio entre inovação e estabilidade.

---

### 4.3 Estratégia C: Integração por Composição 🟡 **ALTERNATIVA**

**Descrição:** Manter `movement_control.py` atual, mas refactorar para usar `BaseJogWidget` internamente.

**Implementação:**

```python
# consumo_lib/widgets/movement_control.py (refatorado)
from movement_controls_module import BaseJogWidget, StepContinuousJogStrategy

class MovementControlWidget(QWidget):
    def __init__(self, ...):
        # ... código existente ...

        # Substitui botões direcionais por BaseJogWidget
        self.jog_widget = BaseJogWidget()
        self.jog_widget.set_strategy(StepContinuousJogStrategy(...))

        # Mantém todos os botões específicos (Backlight, Go to Position, etc)
        self._add_tensiometro_controls()
```

**Vantagens:**
- ✅ Preserva 100% das funcionalidades atuais
- ✅ Aproveita Strategy Pattern para botões direcionais
- ✅ Menor risco de regressão
- ✅ Refactoring incremental

**Desvantagens:**
- 🟡 Benefício limitado (apenas botões direcionais)
- 🟡 Ainda mantém código monolítico

**Conclusão:** 🟡 **ACEITÁVEL** - Benefício limitado, mas seguro.

---

## 5. Análise de Esforço

### 5.1 Estratégia B (Adaptação/Wrapper)

| Tarefa | Estimativa | Observações |
|--------|------------|-------------|
| Criar MovementControlsAdapter | 2-3 horas | ~150 linhas de código |
| Adicionar botão Backlight | 1 hora | Já existe código para copiar |
| Adicionar botão Go to Position | 1-2 horas | Já existe código para copiar |
| Adicionar checkbox Keyboard | 0.5 hora | Simples |
| Adaptar sinais para MovementService | 2 horas | Testar cuidadosamente |
| Atualizar CNCControlTab | 1 hora | Trocar instância |
| Testes manuais | 2-3 horas | Validação completa |
| **TOTAL** | **9.5-12.5 horas** | ~2 dias de trabalho |

### 5.2 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Regressão em movimento CNC | 🟡 Médio | 🔴 Alto | Testes exaustivos com hardware real |
| Incompatibilidade de sinais | 🟢 Baixo | 🟡 Médio | Adapter layer bem testado |
| Perda de funcionalidade | 🟢 Baixo | 🔴 Alto | Checklist de features preservadas |
| Problemas de performance | 🟢 Baixo | 🟢 Baixo | Widget leve, sem impacto |

---

## 6. Plano de Implementação (Estratégia B)

### Fase 1: Preparação (1 hora)

```bash
# 1. Backup do widget atual
cp consumo_lib/widgets/movement_control.py consumo_lib/widgets/movement_control.py.backup

# 2. Criar novo arquivo
touch consumo_lib/widgets/movement_control_v2.py
```

### Fase 2: Adaptador Básico (2-3 horas)

```python
# consumo_lib/widgets/movement_control_v2.py
from movement_controls_module import MovementControlsWidget
from consumo_lib.services import MovementService
from aoi_lib.config_manager import AOIConfigManager

class MovementControlsAdapter(MovementControlsWidget):
    """Adaptador para integrar MovementControlsWidget com Tensiômetro"""

    def __init__(self, controller, config_manager, movement_service, parent=None):
        super().__init__(parent=parent, position_mode="mm")

        self.controller = controller
        self.config_manager = config_manager
        self.movement_service = movement_service

        # Carregar step/feed do config
        self._load_config()

        # Conectar sinais
        self._connect_signals()

        # Adicionar botões específicos
        self._add_backlight_button()
        self._add_goto_position_button()
        self._add_keyboard_checkbox()

    def _load_config(self):
        """Carrega step/feed do config manager"""
        step = self.config_manager.get("movement", "step_size", default=10.0)
        feed = self.config_manager.get("movement", "feed_rate", default=1000.0)
        # Atualiza widget base (herdado)
        self.ed_step.setText(f"{step:.2f}")
        self.ed_feed.setText(f"{feed:.0f}")

    def _connect_signals(self):
        """Conecta sinais do widget base ao MovementService"""
        self.step_move_requested.connect(self._on_step_move)
        self.jog_start.connect(self._on_jog_start)
        self.jog_stop.connect(self._on_jog_stop)
        self.go_to_zero_requested.connect(self._on_go_to_zero)
        self.emergency_stop_toggled.connect(self._on_emergency_stop)

    def _on_step_move(self, axis: str, distance: float, feed: float):
        """Handler para movimento passo-a-passo"""
        direction = 1 if distance >= 0 else -1
        step_abs = abs(distance)
        result = self.movement_service.start_step_move(axis, direction, step_abs, feed)
        if not result.success:
            # Mostrar erro ao usuário
            pass

    def _on_jog_start(self, axis: str, direction: int):
        """Handler para início de jog"""
        feed = self.feed_rate()
        result = self.movement_service.start_jog(axis, direction, feed)
        if not result.success:
            # Mostrar erro ao usuário
            pass

    def _on_jog_stop(self, axis: str):
        """Handler para parada de jog"""
        self.movement_service.stop_jog()

    def _on_go_to_zero(self):
        """Handler para homing"""
        self.movement_service.go_to_zero()

    def _on_emergency_stop(self, engaged: bool):
        """Handler para parada de emergência"""
        if engaged:
            self.controller.cnc.send_soft_reset()
        else:
            self.controller.cnc.unlock()

    def _add_backlight_button(self):
        """Adiciona botão de controle de backlight"""
        # Implementação similar ao widget atual
        pass

    def _add_goto_position_button(self):
        """Adiciona botão Go to Position"""
        # Implementação similar ao widget atual
        pass

    def _add_keyboard_checkbox(self):
        """Adiciona checkbox para controle por teclado"""
        # Implementação simples
        pass

    def update_position_from_cnc(self, x: float, y: float, z: float):
        """Atualiza display de posição (chamado por timer/ polling)"""
        self.update_position(x=x, y=y, z=z)
```

### Fase 3: Integração (1 hora)

```python
# consumo_lib/tabs/cnc_control_tab.py
from consumo_lib.widgets.movement_control_v2 import MovementControlsAdapter

class CNCControlTab(BaseTab):
    def build_ui(self):
        # ... código existente ...

        # Substituir MovementControlWidget por MovementControlsAdapter
        self.movement_widget = MovementControlsAdapter(
            self.controller,
            self.config_manager,
            self.movement_service
        )

        # ... resto do código ...
```

### Fase 4: Testes (2-3 horas)

**Checklist de testes:**

- [ ] Botões direcionais X+/X-/Y+/Y-/Z+/Z- funcionam
- [ ] Modo Step funciona corretamente
- [ ] Modo Contínuo (jog) funciona
- [ ] Botão STOP/RESET funciona
- [ ] Go to Zero funciona
- [ ] **Backlight liga/desliga** (funcionalidade crítica)
- [ ] **Go to Position funciona** (funcionalidade importante)
- [ ] **Keyboard Control funciona** (funcionalidade importante)
- [ ] Posição atualiza em tempo real
- [ ] Step/feed salvos no JSON
- [ ] Integração com MovementService OK
- [ ] Teste com hardware real (PLC)

### Fase 5: Documentação e Cleanup (1 hora)

- [ ] Atualizar docstrings
- [ ] Remover widget antigo (se testes OK)
- [ ] Atualizar __init__.py
- [ ] Commit com mensagem clara

---

## 7. Decisão Final

### ✅ **RECOMENDAÇÃO: Estratégia B (Adaptação/Wrapper)**

**Justificativa:**

1. **Preserva investimentos anteriores** - ~200 linhas de código específico do Tensiômetro não são perdidas
2. **Aproveita código testado** - 710 linhas do módulo novo já validadas
3. **Baixo risco de regressão** - Coexistência possível durante migração
4. **Melhora arquitetura** - Strategy Pattern, maior testabilidade
5. **Esforço razoável** - ~2 dias de trabalho (9.5-12.5 horas)

### Próximos Passos

1. **Aprovação do cliente** - Confirmar estratégia
2. **Backup completo** - Commit antes de começar
3. **Implementação faseada** - Seguir plano da Fase 2
4. **Testes exaustivos** - Validar com hardware real
5. **Documentar mudanças** - Atualizar CLAUDE.md

### Riscos Mitigados

| Risco | Mitigação |
|-------|-----------|
| Perda de funcionalidade | Checklist de features preservadas |
| Regressão em movimento | Testes com hardware real |
| Problemas de integração | Adapter layer bem definido |
| Aumento de complexidade | Módulo mantém independência |

---

## 8. Alternativa: Abordagem Híbrida

Se o cliente preferir uma abordagem mais conservadora:

**Manter widget atual + Refatorar gradualmente:**

1. **Fase 1:** Extrair lógica de botões direcionais para `BaseJogWidget`
2. **Fase 2:** Implementar Strategy Pattern para modos Step/Contínuo
3. **Fase 3:** Testar extensivamente
4. **Fase 4:** Repetir benefícios do módulo novo sem migração

**Vantagem:** Risco mínimo
**Desvantagem:** Benefício limitado (apenas botões direcionais)

---

## 9. Conclusão

O módulo `movement_controls_module/` é **viável para integração** no projeto Tensiômetro, mas a estratégia recomendada é **adaptação/wrapper** ao invés de substituição completa.

A abordagem proposta:
- ✅ Preserva funcionalidades críticas (Backlight, Go to Position, Keyboard)
- ✅ Aproveita código testado (710 linhas)
- ✅ Melhora arquitetura (Strategy Pattern)
- ✅ Mantém compatibilidade com MovementService
- ⚠️ Requer ~2 dias de trabalho
- ⚠️ Necessita testes exaustivos

**Decisão final aguarda aprovação do cliente.**

---

**Documento preparado por:** Claude Code
**Data:** 2026-01-07
**Versão:** 1.0
