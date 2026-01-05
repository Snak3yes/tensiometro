# 📊 Análise de Melhorias de Qualidade de Código

**Data:** 03/01/2026
**Versão do Sistema:** 0.4.0
**Status:** ~99% funcional, necessita melhorias de manutenibilidade

---

## 🎯 Resumo Executivo

O código do Tensiômetro está **funcional e completo**, mas apresenta oportunidades significativas de melhoria em termos de:

1. **Manutenibilidade** - consumo_lib.py com 6.245 linhas
2. **Tratamento de Erros** - Muitos `except Exception` genéricos
3. **Type Safety** - Type hints incompletos
4. **Testabilidade** - Ausência de testes automatizados
5. **Documentação** - Docstrings incompletas
6. **Separação de Responsabilidades** - Widgets misturados com lógica de negócio

---

## 📊 Métricas Atuais

### Tamanho de Arquivos
```
consumo_lib.py                 6.245 linhas  🔴 CRÍTICO
stencil_tracker_ui.py          1.301 linhas  🟡 ALERTA
report_generator.py            1.366 linhas  🟡 ALERTA
stencil_tension.py             1.409 linhas  🟡 ALERTA
```

### Tratamento de Exceções
```
Total de except:               113 ocorrências
except Exception (genérico):    ~85%        🔴 RUIM
except Exception as e:         ~45%
except: (vazio)                ~10         🔴 CRÍTICO
```

### Type Hints
```
Arquivos com typing import:    19 de 29    ✅ BOM
Cobertura estimada:            ~60%        🟡 REGULAR
```

### Classes
```
Total de classes:              80
Média de linhas/classe:        ~270        🟡 ACEITÁVEL
```

---

## 🔧 Melhorias Prioritárias (Ordenadas por Impacto)

### 1. REFACTORING - Divisão do consumo_lib.py ⭐⭐⭐⭐⭐

**Problema:**
- 6.245 linhas em um único arquivo
- Difícil navegação e manutenção
- Múltiplas responsabilidades (UI + lógica + controllers)

**Solução Proposta:**

```
consumo_lib/                   # Novo pacote
├── __init__.py                # Exporta main window
├── main_window.py             # AOIControllerApp (~800 linhas)
├── tabs/
│   ├── __init__.py
│   ├── cnc_control_tab.py     # Aba Controle CNC (~400 linhas)
│   ├── tension_tab.py         # Aba Medição Tensão (~300 linhas)
│   ├── inspection_tab.py      # Aba Inspeção Visual (~400 linhas)
│   ├── tracking_tab.py        # Aba Rastreabilidade (~300 linhas)
│   └── map_tab.py             # Aba Mapa/Índice (~200 linhas)
├── widgets/
│   ├── __init__.py
│   ├── camera_preview.py      # CameraPreviewWidget
│   ├── movement_control.py    # MovementControlWidget
│   ├── tension_viz.py         # TensionVisualizationWidget
│   └── status_bar.py          # Widgets de status
├── dialogs/
│   ├── __init__.py
│   └── (diálogos específicos se houver)
└── utils/
    ├── __init__.py
    └── (helpers específicos da UI)
```

**Benefícios:**
- ✅ Arquivos menores e mais fáceis de entender
- ✅ Responsabilidades claras
- ✅ Melhor isolamento de mudanças
- ✅ Facilita testes unitários

**Estimativa:** 3-4 dias de trabalho
**Risco:** Médio (requer testes cuidadosos)

---

### 2. ERROR HANDLING - Sistema de Exceções Estruturado ⭐⭐⭐⭐⭐

**Problema Atual:**

```python
# ❌ RUIM - Muito genérico
except Exception as e:
    logger.error(f"Erro: {e}")

# ❌ PIOR - Silent failure
except:
    pass
```

**Solução Proposta:**

```python
# aoi_lib/exceptions.py (NOVO)
"""Exceções específicas do domínio."""

class TensiometroError(Exception):
    """Base exception para todas as exceções do sistema."""
    pass

# Hardware Errors
class HardwareError(TensiometroError):
    """Erro de comunicação com hardware."""
    pass

class ModbusConnectionError(HardwareError):
    """Falha na conexão Modbus TCP."""
    pass

class SerialConnectionError(HardwareError):
    """Falha na conexão serial."""
    pass

class CameraError(HardwareError):
    """Erro na câmera."""
    pass

# Business Logic Errors
class StencilNotFoundError(TensiometroError):
    """Stencil não encontrado no sistema."""
    pass

class RecipeNotFoundError(TensiometroError):
    """Receita não encontrada."""
    pass

class ValidationError(TensiometroError):
    """Erro de validação de dados."""
    pass

# Inspection Errors
class InspectionError(TensiometroError):
    """Erro durante inspeção visual."""
    pass

class FiducialAlignmentError(InspectionError):
    """Falha no alinhamento de fiduciais."""
    pass

class GerberParsingError(InspectionError):
    """Erro ao parsear arquivo Gerber."""
    pass
```

**Implementação:**

```python
# ✅ BOM - Específico e tratável
try:
    self plc.connect()
except ModbusConnectionError as e:
    logger.error(f"Falha ao conectar PLC {self.host}: {e}")
    self.show_error_dialog(
        "Conexão PLC",
        f"Não foi possível conectar ao PLC em {self.host}:{self.port}\n"
        f"Verifique se o equipamento está ligado."
    )
    raise  # Re-levanta para tratamento superior

# ✅ BOM - Com contexto
try:
    recipe = self.recipe_manager.load(recipe_name)
except RecipeNotFoundError:
    logger.warning(f"Receita {recipe_name} não existe, criando nova")
    recipe = self.recipe_manager.create_default(recipe_name)
```

**Benefícios:**
- ✅ Tratamento específico por tipo de erro
- ✅ Melhor logging e debugging
- ✅ Mensagens de erro mais claras para o usuário
- ✅ Facilita recovery (ex: retry de conexão)

**Estimativa:** 2-3 dias
**Risco:** Baixo

---

### 3. TYPE SAFETY - Type Hints Completos ⭐⭐⭐⭐

**Problema:**
- Type hints presentes mas incompletos
- Parâmetros sem tipagem em muitos métodos
- Retornos não declarados

**Solução Proposta:**

```python
# ❌ ATUAL
def calculate_transform(self, templates, matches):
    result = {}
    # ...
    return result

# ✅ MELHORADO
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class TransformResult:
    """Resultado do cálculo de transformação."""
    translation: Tuple[float, float]
    rotation: float
    scale: float
    confidence: float

def calculate_transform(
    self,
    templates: List[FiducialTemplate],
    matches: List[FiducialMatchResult]
) -> TransformResult:
    """
    Calcula matriz de transformação a partir de templates e matches.

    Args:
        templates: Lista de templates de fiduciais capturados
        matches: Lista de matches encontrados na imagem

    Returns:
        TransformResult com translação, rotação, escala e confiança

    Raises:
        ValueError: Se menos de 2 fiduciais fornecidos
        AlignmentError: Se confiança muito baixa
    """
    # ...
```

**Automação:**

```bash
# Usar mypy para checagem estática
pip install mypy

# mypy.ini (NOVO)
[mypy]
python_version = 3.10
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = False  # Progressivo
check_untyped_defs = True

[mypy-aoi_lib.*]
disallow_untyped_defs = False  # Começa permissivo

[mypy-consumo_lib]
ignore_errors = True  # Temporário durante refactoring
```

**Benefícios:**
- ✅ Detecção precoce de bugs em IDE
- ✅ Autocompletar mais preciso
- ✅ Documentação embutida no código
- ✅ Refactoring mais seguro

**Estimativa:** 3-4 dias
**Risco:** Baixo (pode ser feito progressivamente)

---

### 4. TESTING - Suite de Testes Unitários ⭐⭐⭐⭐

**Problema:**
- Zero testes automatizados
- Validação manual apenas
- Regressões difíceis de detectar

**Solução Proposta:**

```
tests/
├── __init__.py
├── conftest.py                 # Fixtures pytest
├── unit/
│   ├── __init__.py
│   ├── test_config_manager.py
│   ├── test_recipe_manager.py
│   ├── test_stencil_tracker.py
│   ├── test_fov_calibration.py
│   ├── test_fiducial_alignment.py
│   ├── test_plc_axis_controller.py
│   │   └── (mock de Modbus TCP)
│   └── test_stencil_inspector.py
├── integration/
│   ├── __init__.py
│   ├── test_gerber_pipeline.py
│   └── test_inspection_workflow.py
└── fixtures/
    ├── sample_gerber.gbr
    ├── sample_recipe.json
    └── sample_stencil.json
```

**Exemplos de Testes:**

```python
# tests/unit/test_fov_calibration.py
import pytest
from aoi_lib.fov_calibration import FOVCalibration, CameraFOVConverter

class TestFOVCalibration:
    """Testes para calibração FOV."""

    def test_fixed_camera_fov_constant(self):
        """FOV deve ser constante para câmera fixa."""
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=50.0,
            z0_height_mm=37.5
        )

        converter = CameraFOVConverter(fov)
        converter.set_frame_size(640, 480)
        converter.set_axis_calibration("X", 100.0)
        converter.set_axis_calibration("Y", 100.0)

        fov_z0 = converter.get_fov_at_z(0)
        fov_z100 = converter.get_fov_at_z(100)

        assert fov_z0 == fov_z100, "FOV deve ser constante"

    def test_click_to_movement_center(self):
        """Clique no centro não deve gerar movimento."""
        fov = FOVCalibration(0, 50.0, 37.5)
        converter = CameraFOVConverter(fov)
        converter.set_frame_size(640, 480)
        converter.set_axis_calibration("X", 100.0)
        converter.set_axis_calibration("Y", 100.0)

        dx, dy = converter.video_click_to_movement(
            320, 240,  # Centro
            640, 480,
            z_pulses=0
        )

        assert abs(dx) < 1, "dx deve ser ~0 no centro"
        assert abs(dy) < 1, "dy deve ser ~0 no centro"
```

**Mock de Hardware:**

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, MagicMock
from pymodbus.client import ModbusTcpClient

@pytest.fixture
def mock_plc():
    """Mock de PLC para testes sem hardware."""
    plc = Mock(spec=ModbusTcpClient)
    plc.connect.return_value = True
    plc.is_socket_open.return_value = True

    # Mock responses
    plc.read_holding_registers.return_value = MagicMock(
        registers=[1000, 2000, 500]
    )

    return plc

@pytest.fixture
def sample_recipe():
    """Receita de exemplo para testes."""
    return {
        "recipe_id": "TEST_001",
        "name": "Test Recipe",
        "stencil": {
            "width_mm": 400,
            "height_mm": 300,
            "thickness_mm": 0.12
        },
        # ...
    }
```

**Benefícios:**
- ✅ Regressões detectadas automaticamente
- ✅ Documentação viva do comportamento esperado
- ✅ Facilita refactoring seguro
- ✅ Confiança nas mudanças

**Estimativa:** 5-7 dias
**Risco:** Baixo (testes não afetam produção)

---

### 5. LOGGING - Sistema de Logging Estruturado ⭐⭐⭐

**Problema:**
- Logging inconsistente
- Prints misturados com logging
- Níveis de log inadequados

**Solução Proposta:**

```python
# aoi_lib/logging_config.py (NOVO)
"""Configuração centralizada de logging."""

import logging
import sys
from pathlib import Path

class ContextFilter(logging.Filter):
    """Adiciona contexto aos logs."""

    def filter(self, record):
        record.module_short = record.name.split(".")[-1]
        return True

def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_detailed: bool = False
) -> None:
    """
    Configura logging para toda a aplicação.

    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        log_file: Arquivo para salvar logs (opcional)
        format_detailed: Se True, usa formato mais detalhado
    """
    # Format
    if format_detailed:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
    else:
        fmt = "%(asctime)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(fmt)

    # Handler Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ContextFilter())

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Captura tudo
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Handler File (opcional)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduzir verbosidade de bibliotecas externas
    logging.getLogger("pymodbus").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

# Uso em consumo_lib.py
from aoi_lib.logging_config import setup_logging

setup_logging(
    level="INFO",
    log_file=Path("logs/tensiometro.log"),
    format_detailed=True
)
```

**Uso Consistente:**

```python
# ✅ BOM - Uso correto de níveis
logger.debug(f"Conectando ao PLC em {host}:{port}")  # Detalhe técnico
logger.info(f"Conectado ao PLC com sucesso")        # Evento importante
logger.warning(f"Timeout na leitura, retrying...")  # Problema recuperável
logger.error(f"Falha na conexão Modbus: {e}")      # Erro operacional
logger.critical(f"Corrupção no banco de dados")     # Erro grave

# ✅ BOM - Com contexto
logger.info(
    "Medição de tensão iniciada",
    extra={
        "stencil_code": stencil.code,
        "grid_size": f"{rows}x{cols}",
        "operator": operator_name
    }
)

# ❌ RUIM - Print statements
print("Erro:", e)  # Usar logger.error()
```

**Benefícios:**
- ✅ Troubleshooting mais fácil
- ✅ Logs estruturados para análise
- ✅ Controle de verbosidade
- ✅ Logs em arquivo para auditoria

**Estimativa:** 1-2 dias
**Risco:** Baixo

---

### 6. DOCUMENTATION - Docstrings Completas ⭐⭐⭐

**Problema:**
- Muitos métodos sem docstring
- Docstrings existentes inconsistentes
- Falta exemplos de uso

**Solução Proposta:**

```python
# ❌ ATUAL
def connect(self):
    """Connect."""
    # ...

# ✅ MELHORADO - Google Style
def connect(self, timeout: float = 5.0, retry: int = 3) -> bool:
    """
    Estabelece conexão Modbus TCP com o PLC.

    Tenta conectar ao PLC configurado, com retries automáticos em caso
    de falha. Atualiza o status da conexão e retorna sucesso.

    Args:
        timeout: Tempo de espera em segundos para cada tentativa.
        retry: Número de tentativas antes de desistir.

    Returns:
        True se conexão estabelecida com sucesso, False caso contrário.

    Raises:
        ModbusConnectionError: Se todas as tentativas falharem.

    Example:
        >>> plc = PLCAxisController("192.168.1.5")
        >>> if plc.connect(timeout=10.0):
        ...     print("Conectado!")
        ...     plc.move_absolute("X", 100)
    """
    # ...
```

**Modelo para Docstrings:**

```python
# aoi_lib/docs.py (NOVO - template)
"""
Padrão de docstrings para o projeto.

Estilo: Google Python Style Guide
https://google.github.io/styleguide/pyguide.html

Seções obrigatórias:
    - Summary (uma linha)
    - Args (se houver parâmetros)
    - Returns (se não for None)

Seções opcionais:
    - Raises (para exceções documentadas)
    - Example (para funções complexas)
    - Note (para detalhes importantes)
    - Todo (para melhorias futuras)
"""

def function_template(param1: str, param2: int) -> bool:
    """
    Resumo de uma linha do que a função faz.

    Descrição mais detalhada se necessário. Pode ter múltiplos
    parágrafos explicando o comportamento, algoritmo usado, etc.

    Args:
        param1: Descrição do parâmetro 1.
        param2: Descrição do parâmetro 2.

    Returns:
        True se sucesso, False caso contrário.

    Raises:
        ValueError: Se param2 < 0.
        ConnectionError: Se falhar na conexão.

    Example:
        >>> result = function_template("test", 42)
        >>> print(result)
        True

    Note:
        Esta função é thread-safe.

    Todo:
        - Adicionar suporte a param3
        - Otimizar para grandes volumes
    """
    pass
```

**Benefícios:**
- ✅ Autocompletar de IDE mais útil
- ✅ `help()` do Python funcional
- ✅ Documentação automática (Sphinx)
- ✅ Menos dúvidas sobre uso de APIs

**Estimativa:** 2-3 dias
**Risco:** Baixo (trabalho puramente aditivo)

---

### 7. CODE ORGANIZATION - Separação UI/Logic ⭐⭐⭐

**Problema:**
- Widgets PyQt6 com muita lógica de negócio
- Controllers misturados com UI
- Dificulta testes e reuso

**Solução Proposta:**

```python
# ❌ ATUAL - Tudo no Widget
class TensionVisualizationWidget(QWidget):
    def load_tension_file(self):
        # UI logic
        filename, _ = QFileDialog.getOpenFileName(self, "Abrir")

        # Business logic
        with open(filename) as f:
            data = json.load(f)

        # Validation
        if "measurements" not in data:
            QMessageBox.critical(self, "Erro", "Arquivo inválido")
            return

        # Processing
        self.measurements_data = data
        self.update_canvas()

# ✅ REFACTORED - Separação de responsabilidades
# aoi_lib/tension_loader.py (NOVO)
class TensionFileLoader:
    """Responsável APENAS por carregar/validar arquivos de tensão."""

    def load(self, filepath: Path) -> TensionData:
        """
        Carrega arquivo JSON de medição de tensão.

        Args:
            filepath: Caminho para o arquivo JSON

        Returns:
            TensionData com os dados validados

        Raises:
            ValidationError: Se arquivo inválido
            FileNotFoundError: Se arquivo não existe
        """
        if not filepath.exists():
            raise FileNotFoundError(filepath)

        with open(filepath) as f:
            raw = json.load(f)

        return self._validate_and_parse(raw)

    def _validate_and_parse(self, raw: dict) -> TensionData:
        # Validação e parsing
        pass

# aoi_lib/widgets/tension_viz.py (REFACTORED)
class TensionVisualizationWidget(QWidget):
    """Responsável APENAS pela visualização."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loader = TensionFileLoader()  # Dependency injection
        self.setup_ui()

    def load_tension_file(self):
        """Apenas orquestra UI + loader."""
        filename, _ = QFileDialog.getOpenFileName(self, "Abrir")
        if not filename:
            return

        try:
            data = self.loader.load(Path(filename))
            self.set_data(data)
        except ValidationError as e:
            QMessageBox.critical(self, "Erro", str(e))
        except Exception as e:
            logger.exception("Erro inesperado")
            QMessageBox.critical(self, "Erro", f"Erro: {e}")
```

**Benefícios:**
- ✅ Lógica de negócio testável sem PyQt6
- ✅ Reuso de lógica em outros contextos (CLI, API)
- ✅ Responsabilidades claras
- ✅ Mock fácil em testes

**Estimativa:** 4-5 dias
**Risco:** Médio

---

### 8. CONFIGURATION - Validação de Configurações ⭐⭐⭐

**Problema:**
- `aoi_config.json` sem validação
- Erros em tempo de execução por config inválida
- Difícil debugar

**Solução Proposta:**

```python
# aoi_lib/config_schema.py (NOVO)
"""Schema e validação de configurações."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import json

@dataclass
class CNCConfig:
    """Configurações de CNC."""
    system_type: str  # "corexy"
    max_feed: Dict[str, float]
    max_acc: Dict[str, float]
    pulses_per_rev: float
    fuso_pitch: float

    def validate(self) -> None:
        """Valida se os valores são consistentes."""
        if self.system_type not in ["corexy", "cartesian"]:
            raise ValueError(f"system_type inválido: {self.system_type}")

        if self.pulses_per_rev <= 0:
            raise ValueError("pulses_per_rev deve ser positivo")

@dataclass
class ConnectionConfig:
    """Configurações de conexão."""
    plc_host: str
    plc_port: int
    last_camera_id: str

    def validate(self) -> None:
        """Valida configurações de conexão."""
        if self.plc_port < 1 or self.plc_port > 65535:
            raise ValueError(f"plc_port inválido: {self.plc_port}")

@dataclass
class AOIConfig:
    """Configuração completa do sistema."""
    cnc: CNCConfig
    connections: ConnectionConfig
    # ... outras seções

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AOIConfig":
        """Carrega e valida do dicionário."""
        try:
            cnc = CNCConfig(**data["cnc"])
            cnc.validate()

            conn = ConnectionConfig(**data["connections"])
            conn.validate()

            return cls(cnc=cnc, connections=conn, ...)
        except (KeyError, TypeError) as e:
            raise ValueError(f"Configuração inválida: {e}")

    @classmethod
    def load(cls, filepath: Path) -> "AOIConfig":
        """Carrega de arquivo JSON com validação."""
        with open(filepath) as f:
            data = json.load(f)
        return cls.from_dict(data)

# Uso
try:
    config = AOIConfig.load(Path("aoi_config.json"))
except ValueError as e:
    logger.error(f"Configuração inválida: {e}")
    sys.exit(1)
```

**Benefícios:**
- ✅ Erros de config detectados na carga
- ✅ Mensagens de erro claras
- ✅ Type safety nas configs
- ✅ Autocompletar no código

**Estimativa:** 2 dias
**Risco:** Baixo

---

## 📋 Plano de Implementação Sugerido

### Fase 1: Fundamentos (Semana 1-2)
- [ ] Setup de mypy e pytest
- [ ] Sistema de exceções estruturado
- [ ] Configuração de logging centralizado
- [ ] Validação de configurações

### Fase 2: Testes (Semana 3-4)
- [ ] Tests de lógica de negócio (sem UI)
- [ ] Tests de gerber_parser, recipe_manager, stencil_tracker
- [ ] Mocks de hardware (Modbus, Serial, Camera)
- [ ] Integração no CI (GitHub Actions)

### Fase 3: Type Safety (Semana 5)
- [ ] Adicionar type hints em aoi_lib/* (prioritário)
- [ ] Configurar mypy estrito para novos códigos
- [ ] Corrigir warnings do mypy

### Fase 4: Documentação (Semana 6)
- [ ] Docstrings em módulos críticos (plc_axis_controller, stencil_tension)
- [ ] Exemplos de uso em docstrings
- [ ] Setup de Sphinx (opcional)

### Fase 5: Refactoring (Semana 7-10)
- [ ] Divisão de consumo_lib.py em módulos
- [ ] Separação UI/Logic em widgets
- [ ] Extração de controllers puros

---

## 🎯 Quick Wins (Melhorias Rápidas)

### 1. Remover `except:` vazios (1 dia)
```python
# Encontrar e corrigir
grep -rn "except:" aoi_lib/
```

### 2. Adicionar logger em todos os módulos (1 dia)
```python
# Padrão
import logging
logger = logging.getLogger(__name__)
```

### 3. Type hints em parâmetros públicos (2 dias)
```python
# Priorizar métodos públicos de classes principais
```

### 4. Docstrings em classes dataclass (1 dia)
```python
@dataclass
class Stencil:
    """Representa um stencil físico individual."""
    # ...
```

---

## 📊 Métricas de Sucesso

Antes vs Depois (alvos):

| Métrica | Atual | Alvo |
|---------|-------|------|
| consumo_lib.py linhas | 6.245 | <800 |
| Cobertura de testes | 0% | >60% |
| Type hints coverage | ~60% | >90% |
| `except Exception` | ~85% | <20% |
| `except:` vazio | ~10 | 0 |
| Classes sem docstring | ~40% | <10% |
| mypy errors | N/A | <50 |

---

## 🔧 Ferramentas Recomendadas

```bash
# Instalar ferramentas de qualidade
pip install \
    mypy          # Type checking
    pytest        # Testes
    pytest-cov    # Cobertura de testes
    pytest-qt     # Testes PyQt6
    black         # Formatação (opcional)
    isort         # Ordenação de imports (opcional)
    pylint        # Linting (opcional)
    bandit        # Segurança (opcional)

# Setup
cat > pyproject.toml << 'EOF'
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
check_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=aoi_lib --cov-report=html"
EOF
```

---

## 📝 Conclusão

O código do Tensiômetro é **funcional e robusto**, mas necessita de melhorias para:
- **Manutenibilidade a longo prazo**
- **Onboarding de novos desenvolvedores**
- **Confiança em mudanças**
- **Facilidade de debugging**

**Prioridade Recomendada:**
1. ⭐⭐⭐⭐⭐ Sistema de Exceções + Logging (Semana 1)
2. ⭐⭐⭐⭐⭐ Testes Unitários (Semana 2-3)
3. ⭐⭐⭐⭐ Type Hints (Semana 4)
4. ⭐⭐⭐ Refactoring consumo_lib.py (Semana 5+)

**Investimento:** 4-6 semanas para implementação completa
**Retorno:** Código mais mantível, menos bugs, maior confiança

---

**Documento gerado em:** 03/01/2026
**Próxima revisão sugerida:** Após implementação da Fase 1
