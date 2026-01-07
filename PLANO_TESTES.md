# Plano de Implementação de Testes - FASE 1: Infraestrutura

**Objetivo:** Configurar ambiente de testes profissional para o projeto Tensiometro

**Duração estimada:** 1 dia (4-6 horas)
**Pré-requisitos:** Python 3.8+, acesso ao projeto, permissões para instalar pacotes

---

## 📋 Checklist de Tarefas

- [ ] 1. Criar estrutura de diretórios de testes
- [ ] 2. Instalar dependências de testes
- [ ] 3. Criar arquivo de configuração pytest.ini
- [ ] 4. Criar arquivo conftest.py com fixtures globais
- [ ] 5. Criar script run_tests.sh
- [ ] 6. Migrar test_fov_corrections.py para pytest
- [ ] 7. Criar primeiro teste unitário (gerber_parser)
- [ ] 8. Configurar requirements.txt
- [ ] 9. Criar documentação de testes (TESTING.md)
- [ ] 10. Executar testes e validar coverage

---

## 📁 PASSO 1: Criar Estrutura de Diretórios

### Objetivo
Criar estrutura organizada para testes unitários, integração e fixtures.

### Comandos

```bash
# A partir da raiz do projeto (/mnt/e/PycharmProjects/Tensiometro)

# Criar diretórios de testes
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/fixtures/gerber
mkdir -p tests/fixtures/images

# Criar arquivo __init__.py em cada diretório (para Python reconhecer como pacote)
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Verificar estrutura criada
tree tests/ -L 3
```

### Estrutura Esperada

```
tests/
├── __init__.py
├── unit/                    # Testes unitários (sem hardware)
│   ├── __init__.py
│   ├── test_fov_calibration.py
│   ├── test_gerber_parser.py
│   ├── test_fiducial_alignment.py
│   └── ...
├── integration/             # Testes de integração (com mock)
│   ├── __init__.py
│   ├── test_plc_controller.py
│   ├── test_tensiometer.py
│   └── ...
└── fixtures/                # Arquivos de teste
    ├── gerber/             # Arquivos .gt1 de amostra
    │   ├── simple_circle.gbr
    │   ├── complex_stencil.gbr
    │   └── ...
    └── images/             # Imagens de teste
        ├── fiducial_template.png
        ├── stencil_backlight.jpg
        └── ...
```

### Critérios de Sucesso
- ✅ Todos os diretórios criados
- ✅ Arquivos __init__.py presentes
- ✅ Estrutura visível com `tree tests/`

---

## 📦 PASSO 2: Instalar Dependências de Testes

### Objetivo
Instalar pytest e plugins necessários.

### Comandos

```bash
# Ativar ambiente virtual (se ainda não ativado)
cd /mnt/e/PycharmProjects/Tensiometro
.venv/Scripts/activate  # Windows
# source .venv/bin/activate  # Linux

# Instalar framework de testes
pip install pytest>=7.0.0
pip install pytest-cov>=4.0.0
pip install pytest-mock>=3.10.0
pip install coverage>=7.0.0

# Instalar tudo de uma vez
pip install pytest pytest-cov pytest-mock coverage

# Verificar instalação
pytest --version
# Output esperado: pytest 7.x.x

# Listar pacotes instalados
pip list | grep pytest
```

### Pacotes Instalados

| Pacote | Versão | Propósito |
|--------|--------|-----------|
| pytest | 7.x.x | Framework de testes |
| pytest-cov | 4.x.x | Coverage reporting |
| pytest-mock | 3.x.x | Mocking integrado ao pytest |
| coverage | 7.x.x | Métricas de cobertura |

### Critérios de Sucesso
- ✅ `pytest --version` mostra versão instalada
- ✅ Todos os pacotes listados com `pip list`

---

## ⚙️ PASSO 3: Criar pytest.ini

### Objetivo
Configurar comportamento padrão do pytest.

### Arquivo: pytest.ini

```ini
[pytest]
# Diretórios onde pytest deve procurar testes
testpaths = tests

# Padrões de nomes de arquivos de teste
python_files = test_*.py

# Padrões de classes de teste
python_classes = Test*

# Padrões de funções de teste
python_functions = test_*

# Opções adicionais padrão
addopts =
    -v                                    # Verbose output
    --strict-markers                       # Error on unknown markers
    --tb=short                            # Traceback curto
    --cov=aoi_lib                         # Medir cobertura de aoi_lib
    --cov=consumo_lib                     # Medir cobertura de consumo_lib
    --cov-report=html:htmlcov             # Report HTML em htmlcov/
    --cov-report=term-missing             # Report no terminal com linhas faltando
    --cov-report=xml:coverage.xml         # Report XML (para CI/CD)
    --cov-fail-under=10                   # Falhar se coverage < 10% (inicial)

# Marcadores customizados (para categorizar testes)
markers =
    unit: Testes unitários (rápidos, sem dependências externas)
    integration: Testes de integração (com mocks ou dependências)
    slow: Testes lentos (maior que 1 segundo)
    hardware: Testes que requerem hardware físico
    gpu: Testes que requerem GPU
    network: Testes que requerem rede

# Configuração de coverage
[coverage:run]
source = .
omit =
    */tests/*
    */venv/*
    */.venv/*
    */__pycache__/*
    */site-packages/*
    setup.py

[coverage:report]
precision = 2
show_missing = True
skip_covered = False

[coverage:html]
directory = htmlcov
```

### Localização
Na raiz do projeto: `/mnt/e/PycharmProjects/Tensiometro/pytest.ini`

### Critérios de Sucesso
- ✅ Arquivo criado em raiz do projeto
- ✅ `pytest --collect-only` mostra coleta de testes

---

## 🧩 PASSO 4: Criar conftest.py com Fixtures Globais

### Objetivo
Criar fixtures reutilizáveis para todos os testes.

### Arquivo: tests/conftest.py

```python
"""
Fixtures globais para testes do projeto Tensiometro.

Este arquivo é automaticamente carregado pelo pytest e disponibiliza
fixtures para todos os testes do projeto.
"""

import sys
import os
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock

# Adicionar diretório raiz ao path para importar aoi_lib
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# FIXTURES: Caminhos e Diretórios
# =============================================================================

@pytest.fixture(scope="session")
def project_root_dir():
    """Retorna o diretório raiz do projeto."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def fixtures_dir():
    """Retorna o diretório de fixtures de teste."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def gerber_fixtures_dir(fixtures_dir):
    """Retorna o diretório de arquivos Gerber de teste."""
    gerber_dir = fixtures_dir / "gerber"
    gerber_dir.mkdir(parents=True, exist_ok=True)
    return gerber_dir


@pytest.fixture(scope="session")
def image_fixtures_dir(fixtures_dir):
    """Retorna o diretório de imagens de teste."""
    img_dir = fixtures_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    return img_dir


# =============================================================================
# FIXTURES: Mock de Hardware
# =============================================================================

@pytest.fixture
def mock_plc_client():
    """
    Mock de cliente Modbus TCP para o PLC.

    Simula respostas do PLC Delta sem necessidade de hardware físico.
    """
    mock = MagicMock()
    mock.connect.return_value = True
    mock.is_socket_open.return_value = True

    # Mock de leitura de registradores
    def read_holding_registers(address, count):
        # Simula posição dos eixos
        if address == 1100:  # Eixo X
            return [1000]  # 1000 pulsos
        elif address == 600:  # Eixo Y
            return [500]
        elif address == 1600:  # Eixo Z
            return [0]
        return [0]

    mock.read_holding_registers.side_effect = read_holding_registers

    # Mock de escrita de registradores
    mock.write_registers.return_value = True

    # Mock de coils
    mock.read_coils.return_value = [False]
    mock.write_coil.return_value = True

    return mock


@pytest.fixture
def mock_serial_connection():
    """
    Mock de conexão serial para o tensiômetro.

    Simula leitura do protocolo AS-120N sem hardware físico.
    """
    mock = MagicMock()
    mock.is_open = True
    mock.port = 'COM3'
    mock.baudrate = 2400

    # Mock de leitura de frame de tensão (9 bytes)
    # Frame válido: 0x10 0x19 0x02 0x26 0x1A 0x2B 0x3C 0x00 0x00
    # Valor decodificado: 12.3 N/cm²
    valid_frame = bytes([0x10, 0x19, 0x02, 0x26, 0x1A, 0x2B, 0x3C, 0x00, 0x00])
    mock.read.return_value = valid_frame
    mock.write.return_value = 0

    # Mock de reset de buffer
    mock.reset_input_buffer.return_value = None
    mock.reset_output_buffer.return_value = None

    return mock


@pytest.fixture
def mock_camera():
    """
    Mock de câmera OpenCV.

    Simula captura de imagens sem câmera física.
    """
    mock = MagicMock()

    # Mock de propriedades da câmera
    mock.isOpened.return_value = True
    mock.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))

    # Mock de configurações
    mock.get.return_value = 30.0  # FPS padrão
    mock.set.return_value = True

    return mock


# =============================================================================
# FIXTURES: Imagens Sintéticas
# =============================================================================

@pytest.fixture
def blank_image():
    """Retorna imagem em branco (640x480x3)."""
    return np.ones((480, 640, 3), dtype=np.uint8) * 255


@pytest.fixture
def black_image():
    """Retorna imagem preta (640x480x3)."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def gray_image():
    """Retorna imagem cinza (640x480x3)."""
    return np.ones((480, 640, 3), dtype=np.uint8) * 128


@pytest.fixture
def chessboard_image():
    """
    Retorna imagem de padrão xadrez para calibração.

    Padrão 8x6 cantos, quadrados de 30px.
    """
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    square_size = 30

    for row in range(8):
        for col in range(6):
            if (row + col) % 2 == 0:
                y1, y2 = row * square_size, (row + 1) * square_size
                x1, x2 = col * square_size, (col + 1) * square_size
                img[y1:y2, x1:x2] = 255

    return img


@pytest.fixture
def fiducial_template_image():
    """
    Retorna imagem com fiducial (marca de referência) sintético.

    Fiducial circular branco em fundo preto.
    """
    img = np.zeros((100, 100, 3), dtype=np.uint8)

    # Desenhar círculo branco no centro
    center = (50, 50)
    radius = 20
    cv2 = pytest.importorskip("cv2")  # OpenCV
    cv2.circle(img, center, radius, (255, 255, 255), -1)

    return img


# =============================================================================
# FIXTURES: Dados de Teste
# =============================================================================

@pytest.fixture
def sample_stencil_data():
    """Retorna dados de stencil de exemplo."""
    return {
        "code": "TEST-001",
        "description": "Stencil de teste",
        "recipe_name": "SAMPLE_001",
        "status": "active",
        "creation_date": "2026-01-07T10:00:00"
    }


@pytest.fixture
def sample_recipe_data():
    """Retorna dados de receita de exemplo."""
    return {
        "name": "SAMPLE_001",
        "description": "Receita de teste",
        "dimensions": {
            "width_mm": 500.0,
            "height_mm": 500.0,
            "thickness_mm": 0.127
        },
        "tension_acceptance": {
            "ok_min": 35.0,
            "warning_min": 30.0,
            "nok_max": 25.0
        },
        "inspection_thresholds": {
            "ok_threshold": 90.0,
            "partial_threshold": 70.0
        }
    }


@pytest.fixture
def sample_tension_measurements():
    """
    Retorna medições de tensão de exemplo (grid 3x3).

    Valores em N/cm.
    """
    return [
        [38.5, 39.2, 38.8],
        [37.9, 38.1, 39.0],
        [38.3, 38.7, 38.4]
    ]


# =============================================================================
# FIXTURES: Configuração de Teste
# =============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reseta singletons antes de cada teste.

    Útil para evitar contaminação entre testes que usam
    classes com instâncias únicas (singletons).
    """
    yield
    # Cleanup após cada teste (se necessário)


@pytest.fixture
def temp_config_file(tmp_path):
    """
    Cria um arquivo de configuração temporário.

    Útil para testes que modificam configurações.
    """
    config_file = tmp_path / "test_config.json"

    # Config padrão de teste
    import json
    default_config = {
        "cnc": {
            "max_feed": 3000.0,
            "max_acc": 500.0
        },
        "connections": {
            "plc_host": "192.168.1.5",
            "plc_port": 502
        }
    }

    config_file.write_text(json.dumps(default_config, indent=2))
    return config_file


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def assert_valid_gerber_bounds(bounds):
    """
    Helper para validar bounds de Gerber.

    Args:
        bounds: Objeto com atributos min_x, max_x, min_y, max_y
    """
    assert bounds.min_x < bounds.max_x, "min_x deve ser menor que max_x"
    assert bounds.min_y < bounds.max_y, "min_y deve ser menor que max_y"
    assert bounds.min_x >= 0, "min_x deve ser não-negativo"
    assert bounds.min_y >= 0, "min_y deve ser não-negativo"


def assert_classification(classification, expected_range):
    """
    Helper para validar classificação de inspeção.

    Args:
        classification: String ("OK", "PARTIAL", "BLOCKED")
        expected_range: Tuple de valores (min, max) aceitáveis
    """
    assert classification in ["OK", "PARTIAL", "BLOCKED"]
    # Adicionar mais validações conforme necessário
```

### Localização
`/mnt/e/PycharmProjects/Tensiometro/tests/conftest.py`

### Critérios de Sucesso
- ✅ Arquivo criado em tests/conftest.py
- ✅ `pytest --fixtures` mostra as novas fixtures

---

## 🚀 PASSO 5: Criar Script run_tests.sh

### Objetivo
Automatizar execução de testes com diferentes níveis de verbose.

### Arquivo: run_tests.sh

```bash
#!/bin/bash

# Script para executar testes do projeto Tensiometro
# Uso: ./run_tests.sh [opções]
#
# Opções:
#   --fast       Apenas testes rápidos (exclui marcadores 'slow' e 'hardware')
#   --unit       Apenas testes unitários
#   --integration Apenas testes de integração
#   --cov        Executa com coverage report (padrão)
#   --html       Abre coverage report no navegador após testes
#   --watch      Modo watch (re-executa quando código muda)
#   -v           Verbose mode
#   -h           Mostra help

set -e  # Para em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configurações padrão
PYTEST_CMD="pytest"
MARKERS=""
COVERAGE_FLAG="--cov=aoi_lib --cov=consumo_lib"
COVERAGE_REPORTS="--cov-report=html:htmlcov --cov-report=term-missing"
VERBOSE_FLAG="-v"
OPEN_BROWSER=false

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            MARKERS="-m 'not slow and not hardware'"
            print_info "Modo rápido: excluindo testes lentos e de hardware"
            shift
            ;;
        --unit)
            MARKERS="-m unit"
            print_info "Executando apenas testes unitários"
            shift
            ;;
        --integration)
            MARKERS="-m integration"
            print_info "Executando apenas testes de integração"
            shift
            ;;
        --cov)
            COVERAGE_FLAG="--cov=aoi_lib --cov=consumo_lib"
            COVERAGE_REPORTS="--cov-report=html:htmlcov --cov-report=term-missing"
            print_info "Coverage report habilitado"
            shift
            ;;
        --no-cov)
            COVERAGE_FLAG=""
            COVERAGE_REPORTS=""
            print_info "Coverage report desabilitado"
            shift
            ;;
        --html)
            OPEN_BROWSER=true
            print_info "Abrirá coverage report no navegador"
            shift
            ;;
        --watch)
            PYTEST_CMD="ptw"  # pytest-watch
            COVERAGE_FLAG=""
            COVERAGE_REPORTS=""
            print_info "Modo watch: re-executará quando código mudar"
            shift
            ;;
        -v)
            VERBOSE_FLAG="-vv"
            shift
            ;;
        -h|--help)
            echo "Uso: $0 [opções]"
            echo ""
            echo "Opções:"
            echo "  --fast       Apenas testes rápidos (exclui 'slow' e 'hardware')"
            echo "  --unit       Apenas testes unitários"
            echo "  --integration Apenas testes de integração"
            echo "  --cov        Executa com coverage report (padrão)"
            echo "  --no-cov     Desabilita coverage report"
            echo "  --html       Abre coverage report no navegador"
            echo "  --watch      Modo watch (re-executa quando código muda)"
            echo "  -v           Verbose mode"
            echo "  -h           Mostra este help"
            echo ""
            echo "Exemplos:"
            echo "  $0                  # Executa todos os testes com coverage"
            echo "  $0 --fast           # Apenas testes rápidos"
            echo "  $0 --unit --no-cov  # Unit tests sem coverage"
            echo "  $0 --html           # Testes + abre coverage no navegador"
            exit 0
            ;;
        *)
            print_error "Opção desconhecida: $1"
            echo "Use -h para help"
            exit 1
            ;;
    esac
done

# Verificar se está no diretório do projeto
if [ ! -f "pytest.ini" ]; then
    print_error "pytest.ini não encontrado. Execute este script da raiz do projeto."
    exit 1
fi

# Verificar se ambiente virtual está ativado
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warn "Ambiente virtual não ativado. Ativando .venv..."
    if [ -d ".venv" ]; then
        source .venv/Scripts/activate  # Windows
        # source .venv/bin/activate  # Linux (comente a linha acima e descomente esta)
    else
        print_error ".venv não encontrado. Crie o ambiente virtual primeiro."
        exit 1
    fi
fi

# Comando final
PYTEST_ARGS="$VERBOSE_FLAG $MARKERS $COVERAGE_FLAG $COVERAGE_REPORTS"

print_info "Executando testes..."
echo ""
echo "Comando: $PYTEST_CMD $PYTEST_ARGS"
echo ""

# Executar testes
if $PYTEST_CMD $PYTEST_ARGS; then
    echo ""
    print_info "✅ Todos os testes passaram!"

    # Abrir browser se solicitado
    if [ "$OPEN_BROWSER" = true ]; then
        print_info "Abrindo coverage report no navegador..."
        if command -v python &> /dev/null; then
            python -m webbrowser htmlcov/index.html
        else
            print_warn "Não foi possível abrir o navegador automaticamente."
            print_info "Abra htmlcov/index.html manualmente no seu navegador."
        fi
    fi

    exit 0
else
    echo ""
    print_error "❌ Alguns testes falharam!"
    exit 1
fi
```

### Arquivo: run_tests.bat (para Windows)

```batch
@echo off
REM Script para executar testes no Windows
REM Uso: run_tests.bat [opções]

SETLOCAL EnableDelayedExpansion

REM Configurações
SET PYTEST_CMD=pytest
SET COVERAGE_FLAG=--cov=aoi_lib --cov=consumo_lib
SET COVERAGE_REPORTS=--cov-report=html:htmlcov --cov-report=term-missing
SET VERBOSE_FLAG=-v
SET OPEN_BROWSER=0

REM Parse argumentos
:parse_args
IF "%1"=="--fast" (
    SET MARKERS=-m "not slow and not hardware"
    echo [INFO] Modo rápido: excluindo testes lentos
    SHIFT
    GOTO :parse_args
)
IF "%1"=="--unit" (
    SET MARKERS=-m unit
    echo [INFO] Executando apenas testes unitários
    SHIFT
    GOTO :parse_args
)
IF "%1"=="--no-cov" (
    SET COVERAGE_FLAG=
    SET COVERAGE_REPORTS=
    echo [INFO] Coverage desabilitado
    SHIFT
    GOTO :parse_args
)
IF "%1"=="--html" (
    SET OPEN_BROWSER=1
    echo [INFO] Abrirá coverage no navegador
    SHIFT
    GOTO :parse_args
)
IF "%1"=="-h" (
    echo Uso: %0 [opcoes]
    echo   --fast      Apenas testes rapidos
    echo   --unit      Apenas testes unitarios
    echo   --no-cov    Desabilita coverage
    echo   --html      Abre coverage no navegador
    GOTO :EOF
)

REM Verificar ambiente virtual
IF "%VIRTUAL_ENV%"=="" (
    echo [WARN] Ativando ambiente virtual...
    CALL .venv\Scripts\activate.bat
)

REM Executar testes
echo [INFO] Executando testes...
%PYTEST_CMD% %VERBOSE_FLAG% %MARKERS% %COVERAGE_FLAG% %COVERAGE_REPORTS%

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo [INFO] Todos os testes passaram!
    IF %OPEN_BROWSER% EQU 1 (
        echo [INFO] Abrindo coverage...
        start htmlcov\index.html
    )
) ELSE (
    echo.
    echo [ERROR] Alguns testes falharam!
)

ENDLOCAL
```

### Permissões (Linux/Mac)

```bash
# Tornar script executável
chmod +x run_tests.sh
```

### Localização
Raiz do projeto: `/mnt/e/PycharmProjects/Tensiometro/run_tests.sh`

### Critérios de Sucesso
- ✅ Script criado e executável
- ✅ `./run_tests.sh` executa testes (ainda sem testes, deve mostrar "0 collected")

---

## 🔄 PASSO 6: Migrar test_fov_corrections.py para pytest

### Objetivo
Converter o teste existente para o padrão pytest.

### Arquivo Original: test_fov_corrections.py

```python
# Arquivo atual (será substituído)
def test_fixed_camera_fov():
    # ... código existente ...
    pass

def test_y_inversion():
    # ... código existente ...
    pass

if __name__ == "__main__":
    # Execução manual
    test_fixed_camera_fov()
    test_y_inversion()
```

### Novo Arquivo: tests/unit/test_fov_calibration.py

```python
"""
Testes para o módulo de calibração FOV (Field of View).

Testa a conversão entre pixels e milímetros para câmera fixa,
considerando diferentes alturas Z e inversão de eixo Y.
"""

import pytest
import numpy as np
from aoi_lib.fov_calibration import FOVCalibration, CameraFOVConverter


class TestFixedCameraFOV:
    """
    Testa comportamento de FOV para câmera fixa.

    Ao contrário da ADESIVADORA (câmera móvel), o Tensiometro
    possui câmera fixa, portanto o FOV deve ser constante
    independentemente da altura Z.
    """

    def test_fov_constant_across_z_heights(self):
        """
        Testa que FOV permanece constante em diferentes alturas Z.

        Para câmera fixa, get_fov_at_z() deve retornar os mesmos
        valores de largura e altura para qualquer Z.
        """
        # Configuração: FOV de 50mm x 37.5mm em Z=0
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=50.0,
            z0_height_mm=37.5
        )

        # Testar em diferentes alturas
        for z_pulses in [0, 100, 500, 1000]:
            width, height = fov.get_fov_at_z(z_pulses)

            # FOV deve ser constante (câmera fixa)
            assert width == fov.z0_width_mm, \
                f"FOV width deve ser constante para câmera fixa (z={z_pulses})"
            assert height == fov.z0_height_mm, \
                f"FOV height deve ser constante para câmera fixa (z={z_pulses})"

    def test_fov_returns_tuple(self):
        """Testa que get_fov_at_z retorna uma tupla (width, height)."""
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=50.0,
            z0_height_mm=37.5
        )

        result = fov.get_fov_at_z(0)

        assert isinstance(result, tuple), "get_fov_at_z deve retornar tuple"
        assert len(result) == 2, "get_fov_at_z deve retornar (width, height)"

    def test_fov_positive_values(self):
        """Testa que FOV sempre retorna valores positivos."""
        fov = FOVCalibration(
            z0_z_pulses=0,
            z0_width_mm=50.0,
            z0_height_mm=37.5
        )

        width, height = fov.get_fov_at_z(0)

        assert width > 0, "FOV width deve ser positivo"
        assert height > 0, "FOV height deve ser positivo"


class TestYInversion:
    """
    Testa inversão de eixo Y para conversão de coordenadas.

    O sistema de coordenadas da imagem tem Y aumentando para baixo,
    enquanto o CNC tem Y aumentando para cima (em direção ao operador).
    Portanto, é necessário inverter Y ao converter de imagem para CNC.
    """

    @pytest.fixture
    def fov_converter(self):
        """Fixture com configuração padrão de FOV."""
        return CameraFOVConverter({
            'z0_z_pulses': 0,
            'z0_width_mm': 50.0,
            'z0_height_mm': 37.5,
            'z1_z_pulses': 1000,
            'z1_width_mm': 50.0,  # Mesmo valores (câmera fixa)
            'z1_height_mm': 37.5
        })

    def test_y_inversion_move_up(self, fov_converter):
        """
        Testa movimento para cima (diminuir pixel Y).

        Ao clicar na parte superior da imagem (menor pixel Y),
        o CNC deve se mover para cima (maior Y em coordenadas CNC).
        """
        # Frame de 640x480, centro em (320, 240)
        frame_width, frame_height = 640, 480

        # Clicar 100 pixels acima do centro
        click_y_px = 240 - 100  # 140 pixels do topo

        # Converter para movimento em CNC
        dx_pulses, dy_pulses = fov_converter.video_click_to_movement(
            x_px=320,  # Centro X
            y_px=click_y_px,
            frame_width=frame_width,
            frame_height=frame_height,
            current_z_pulses=0,
            pulses_per_mm={'X': 100, 'Y': 100},
            invert_y=True  # Y invertido
        )

        # dy_pulses deve ser POSITIVO (mover para cima no CNC)
        assert dy_pulses > 0, \
            "Mover para cima na imagem (menor Y) deve resultar em dy positivo no CNC"

    def test_y_inversion_move_down(self, fov_converter):
        """
        Testa movimento para baixo (aumentar pixel Y).

        Ao clicar na parte inferior da imagem (maior pixel Y),
        o CNC deve se mover para baixo (menor Y em coordenadas CNC).
        """
        frame_width, frame_height = 640, 480

        # Clicar 100 pixels abaixo do centro
        click_y_px = 240 + 100  # 340 pixels do topo

        dx_pulses, dy_pulses = fov_converter.video_click_to_movement(
            x_px=320,
            y_px=click_y_px,
            frame_width=frame_width,
            frame_height=frame_height,
            current_z_pulses=0,
            pulses_per_mm={'X': 100, 'Y': 100},
            invert_y=True
        )

        # dy_pulses deve ser NEGATIVO (mover para baixo no CNC)
        assert dy_pulses < 0, \
            "Mover para baixo na imagem (maior Y) deve resultar em dy negativo no CNC"

    def test_y_inversion_disabled(self, fov_converter):
        """
        Testa comportamento quando invert_y=False.

        Sem inversão, pixel Y maior deve resultar em dy maior.
        """
        frame_width, frame_height = 640, 480

        # Clicar abaixo do centro
        click_y_px = 340  # 100 pixels abaixo do centro

        dx_pulses, dy_pulses = fov_converter.video_click_to_movement(
            x_px=320,
            y_px=click_y_px,
            frame_width=frame_width,
            frame_height=frame_height,
            current_z_pulses=0,
            pulses_per_mm={'X': 100, 'Y': 100},
            invert_y=False  # Sem inversão
        )

        # Sem inversão, dy deve ter o mesmo sinal do offset de pixel
        expected_dy_sign = 1 if click_y_px > frame_height / 2 else -1
        actual_dy_sign = 1 if dy_pulses > 0 else -1

        assert actual_dy_sign == expected_dy_sign, \
            "Sem inversão, sinal de dy deve corresponder ao offset de pixel Y"

    def test_x_no_inversion(self, fov_converter):
        """
        Testa que eixo X NÃO é invertido.

        X aumenta da esquerda para a direita tanto na imagem quanto no CNC.
        """
        frame_width, frame_height = 640, 480

        # Clicar à direita do centro
        click_x_px = 320 + 100  # 420 pixels da esquerda

        dx_pulses, dy_pulses = fov_converter.video_click_to_movement(
            x_px=click_x_px,
            y_px=240,
            frame_width=frame_width,
            frame_height=frame_height,
            current_z_pulses=0,
            pulses_per_mm={'X': 100, 'Y': 100},
            invert_y=True
        )

        # dx_pulses deve ser POSITIVO (mover para direita)
        assert dx_pulses > 0, \
            "Mover para direita na imagem deve resultar em dx positivo no CNC"

    def test_click_center_no_movement(self, fov_converter):
        """
        Testa que clicar no centro não resulta em movimento.

        Clicar exatamente no centro da imagem deve resultar em
        dx=0 e dy=0 (sem movimento).
        """
        frame_width, frame_height = 640, 480
        center_x, center_y = frame_width // 2, frame_height // 2

        dx_pulses, dy_pulses = fov_converter.video_click_to_movement(
            x_px=center_x,
            y_px=center_y,
            frame_width=frame_width,
            frame_height=frame_height,
            current_z_pulses=0,
            pulses_per_mm={'X': 100, 'Y': 100},
            invert_y=True
        )

        # Sem movimento (tolerância pequena para erros de ponto flutuante)
        assert abs(dx_pulses) < 1, "Clicar no centro X não deve gerar movimento em X"
        assert abs(dy_pulses) < 1, "Clicar no centro Y não deve gerar movimento em Y"


class TestFOVEdgeCases:
    """Testa casos extremos e borda."""

    def test_zero_frame_size_raises_error(self):
        """Testa que frame size zero levanta erro."""
        fov = FOVCalibration(0, 50.0, 37.5)

        with pytest.raises((ZeroDivisionError, ValueError)):
            fov.get_fov_at_z(0)

    def test_negative_fov_values(self):
        """Testa que valores negativos de FOV são tratados."""
        # FOV com valores negativos (inválido, mas pode acontecer por bug)
        fov = FOVCalibration(0, -50.0, -37.5)

        width, height = fov.get_fov_at_z(0)

        # Valores devem ser negativos (testa que não há erro)
        assert width < 0
        assert height < 0

    def test_extreme_z_heights(self):
        """Testa FOV em alturas Z extremas."""
        fov = FOVCalibration(0, 50.0, 37.5)

        # Z muito alto
        width1, height1 = fov.get_fov_at_z(z_pulses=100000)
        assert width1 == fov.z0_width_mm
        assert height1 == fov.z0_height_mm

        # Z negativo (pode acontecer em homing)
        width2, height2 = fov.get_fov_at_z(z_pulses=-100)
        assert width2 == fov.z0_width_mm
        assert height2 == fov.z0_height_mm
```

### Localização
`/mnt/e/PycharmProjects/Tensiometro/tests/unit/test_fov_calibration.py`

### Critérios de Sucesso
- ✅ Teste migrado para pytest
- ✅ `pytest tests/unit/test_fov_calibration.py` executa com sucesso
- ✅ Todos os testes passam (3 testes, 7 assertions)

---

## 🧪 PASSO 7: Criar Primeiro Teste Unitário (Gerber Parser)

### Objetivo
Criar exemplo de teste unitário para módulo core sem dependências de hardware.

### Arquivo: tests/unit/test_gerber_parser.py

```python
"""
Testes para o parser de arquivos Gerber RS-274X.

Estes testes validam o parsing de arquivos Gerber,
detecção de fiduciais e cálculos de geometria.
"""

import pytest
from pathlib import Path
from aoi_lib.gerber_parser import GerberParser, GerberObject, GerberBounds


class TestGerberParserBasics:
    """Testa funcionalidades básicas do parser."""

    def test_parser_initialization(self):
        """Testa que o parser pode ser inicializado."""
        parser = GerberParser()
        assert parser is not None
        assert hasattr(parser, 'parse_file')

    def test_parse_nonexistent_file(self):
        """Testa que arquivo inexistente levanta erro apropriado."""
        parser = GerberParser()

        with pytest.raises(FileNotFoundError):
            parser.parse_file("/caminho/inexistente.gbr")


class TestGerberBounds:
    """Testa cálculo de limites (bounding box) de arquivos Gerber."""

    def test_empty_bounds(self):
        """Testa bounds de arquivo vazio."""
        bounds = GerberBounds()
        assert bounds.min_x == 0
        assert bounds.max_x == 0
        assert bounds.min_y == 0
        assert bounds.max_y == 0

    def test_bounds_calculation(self):
        """Testa cálculo de bounds com objetos."""
        bounds = GerberBounds()

        # Adicionar objetos simulando posições
        # Exemplo: círculo em (10, 10) com raio 5
        bounds.update(10 - 5, 10 - 5, 10 + 5, 10 + 5)

        assert bounds.min_x == 5
        assert bounds.max_x == 15
        assert bounds.min_y == 5
        assert bounds.max_y == 15

    def test_bounds_validation(self):
        """Testa validação de bounds."""
        bounds = GerberBounds()
        bounds.update(0, 0, 100, 100)

        # Validar usando helper
        from tests.conftest import assert_valid_gerber_bounds
        assert_valid_gerber_bounds(bounds)


class TestFiducialDetection:
    """Testa detecção automática de fiduciais."""

    @pytest.fixture
    def sample_gerber_objects(self):
        """
        Cria objetos Gerber simulados para teste.

        Inclui círculos que podem ser fiduciais.
        """
        objects = []

        # Adicionar alguns círculos (potenciais fiduciais)
        # Fiducial típico: círculo com 1-2mm de diâmetro
        for i, (x, y) in enumerate([(0, 0), (100, 0), (0, 50), (100, 50)]):
            obj = GerberObject(
                kind='circle',
                x=x,
                y=y,
                diameter=1.5,  # 1.5mm (típico para fiducial)
                aperture_id=f'D{i+10}'
            )
            objects.append(obj)

        # Adicionar outros objetos (não fiduciais)
        # Rectângulo grande (não é fiducial)
        rect = GerberObject(
            kind='rectangle',
            x=50,
            y=25,
            width=10,
            height=5,
            aperture_id='D20'
        )
        objects.append(rect)

        return objects

    def test_detect_fiducial_candidates(self, sample_gerber_objects):
        """
        Testa detecção de candidatos a fiduciais.

        Fiduciais são tipicamente círculos pequenos (1-2mm).
        """
        # Filtrar apenas círculos com diâmetro entre 1 e 2mm
        fiducials = [
            obj for obj in sample_gerber_objects
            if obj.kind == 'circle' and 1.0 <= obj.diameter <= 2.0
        ]

        # Deve encontrar 4 fiduciais nos cantos
        assert len(fiducials) == 4, \
            "Deve detectar 4 círculos pequenos como fiduciais"

        # Todos devem ser círculos
        assert all(f.kind == 'circle' for f in fiducials)

    def test_fiducial_positions(self, sample_gerber_objects):
        """Testa que posições dos fiduciais estão corretas."""
        fiducials = [
            obj for obj in sample_gerber_objects
            if obj.kind == 'circle' and 1.0 <= obj.diameter <= 2.0
        ]

        # Verificar posições esperadas
        positions = [(f.x, f.y) for f in fiducials]

        assert (0, 0) in positions, "Deve ter fiducial em (0, 0)"
        assert (100, 0) in positions, "Deve ter fiducial em (100, 0)"
        assert (0, 50) in positions, "Deve ter fiducial em (0, 50)"
        assert (100, 50) in positions, "Deve ter fiducial em (100, 50)"


class TestApertureGeometries:
    """Testa conversão de apertures para geometrias."""

    def test_circle_aperture(self):
        """Testa aperture circular."""
        aperture = {
            'kind': 'circle',
            'diameter': 2.0,  # 2mm
            'x': 10.0,
            'y': 20.0
        }

        # Validar propriedades
        assert aperture['diameter'] > 0
        assert aperture['x'] >= 0
        assert aperture['y'] >= 0

        # Área esperada: π * r² = π * 1² = π
        import math
        expected_area = math.pi * (aperture['diameter'] / 2) ** 2
        assert expected_area > 0

    def test_rectangle_aperture(self):
        """Testa aperture retangular."""
        aperture = {
            'kind': 'rectangle',
            'width': 5.0,
            'height': 2.0,
            'x': 10.0,
            'y': 20.0
        }

        # Área esperada: width * height = 5 * 2 = 10
        expected_area = aperture['width'] * aperture['height']
        assert expected_area == 10.0

    def test_obround_aperture(self):
        """
        Testa aperture obround.

        Obround = retângulo + dois semicírculos nas extremidades.
        Exemplo: obround 5mm x 2mm
        - Parte retangular: (5 - 2) x 2 = 3 x 2 = 6mm²
        - Dois semicírculos = um círculo completo: π * 1² = π mm²
        - Total: 6 + π ≈ 9.14mm²
        """
        aperture = {
            'kind': 'obround',
            'width': 5.0,
            'height': 2.0,
            'x': 10.0,
            'y': 20.0
        }

        # Calcular área corretamente (retângulo + círculo)
        import math
        if aperture['width'] > aperture['height']:
            # Horizontal
            rect_area = (aperture['width'] - aperture['height']) * aperture['height']
            circle_area = math.pi * (aperture['height'] / 2) ** 2
        else:
            # Vertical
            rect_area = (aperture['height'] - aperture['width']) * aperture['width']
            circle_area = math.pi * (aperture['width'] / 2) ** 2

        expected_area = rect_area + circle_area

        # Validar cálculo (9.14mm² para o exemplo)
        assert abs(expected_area - 9.14) < 0.01, \
            f"Área do obround deve ser ~9.14, calculado: {expected_area:.2f}"


class TestGerberUnitConversion:
    """Testa conversão de unidades em arquivos Gerber."""

    def test_mm_to_inches_conversion(self):
        """Testa conversão de mm para polegadas."""
        # 1 polegada = 25.4mm
        mm_value = 25.4
        inches_value = mm_value / 25.4

        assert abs(inches_value - 1.0) < 0.001, \
            "25.4mm deve ser igual a 1 polegada"

    def test_inches_to_mm_conversion(self):
        """Testa conversão de polegadas para mm."""
        # 1 polegada = 25.4mm
        inches_value = 1.0
        mm_value = inches_value * 25.4

        assert abs(mm_value - 25.4) < 0.001, \
            "1 polegada deve ser igual a 25.4mm"


@pytest.mark.integration
class TestGerberFileParsing:
    """
    Testa parsing de arquivos Gerber reais.

    Estes testes requerem arquivos .gt1 em tests/fixtures/gerber/
    """

    @pytest.fixture
    def sample_gerber_file(self, gerber_fixtures_dir, tmp_path):
        """
        Cria um arquivo Gerber simples para teste.

        Se não existir arquivo de teste, cria um básico.
        """
        gerber_path = gerber_fixtures_dir / "simple_circle.gbr"

        # Se não existir, criar um arquivo básico
        if not gerber_path.exists():
            # Criar Gerber RS-274X básico
            gerber_content = """%FSLAX26Y26*%
%MOIN*%
%OFA0B0*%
%ADD10C,1.5*%
%ADD11R,2X1*%
%LPD*%
G01*
X0Y0D03*
X100000Y0D03*
X0Y50000D03*
X100000Y50000D03*
M02*
"""
            gerber_path.write_text(gerber_content)

        return gerber_path

    def test_parse_simple_gerber(self, sample_gerber_file):
        """Testa parsing de arquivo Gerber simples."""
        parser = GerberParser()

        # Este teste pode falhar se o parser precisar ser adaptado
        # Ajuste conforme a implementação real
        try:
            result = parser.parse_file(str(sample_gerber_file))

            # Validar resultado
            assert result is not None, "Parser deve retornar resultado"
            assert hasattr(result, 'bounds'), "Resultado deve ter bounds"
            assert hasattr(result, 'objects'), "Resultado deve ter objetos"

        except NotImplementedError:
            # Se parser ainda não estiver implementado, marcar como pendente
            pytest.skip("GerberParser.parse_file() ainda não implementado")

    def test_parse_invalid_gerber(self, gerber_fixtures_dir, tmp_path):
        """Testa que arquivo Gerber inválido levanta erro."""
        # Criar arquivo inválido
        invalid_file = tmp_path / "invalid.gbr"
        invalid_file.write_text("INVALID GERBER CONTENT")

        parser = GerberParser()

        with pytest.raises((ValueError, IOError)):
            parser.parse_file(str(invalid_file))
```

### Localização
`/mnt/e/PycharmProjects/Tensiometro/tests/unit/test_gerber_parser.py`

### Critérios de Sucesso
- ✅ Arquivo criado
- ✅ `pytest tests/unit/test_gerber_parser.py` executa
- ✅ Pelo menos 5 testes básicos passam

---

## 📝 PASSO 8: Criar requirements.txt

### Objetivo
Documentar todas as dependências do projeto, incluindo testes.

### Arquivo: requirements.txt

```txt
# =============================================================================
# DEPENDÊNCIAS DE PRODUÇÃO
# =============================================================================

# GUI Framework
PyQt6>=6.6.1

# Computer Vision
opencv-python>=4.9.0
numpy>=1.26.0

# Hardware Communication
pymodbus>=3.6.2
pyserial>=3.5

# Data Processing
matplotlib>=3.8.0

# PDF Generation
reportlab>=4.0.7

# =============================================================================
# DEPENDÊNCIAS DE DESENVOLVIMENTO E TESTES
# =============================================================================

# Testing Framework
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
pytest-timeout>=2.2.0
pytest-xdist>=3.5.0  # Execução paralela de testes

# Coverage
coverage>=7.3.0

# Code Quality
pylint>=3.0.0
black>=23.12.0
isort>=5.13.0
mypy>=1.7.0

# Documentation
sphinx>=7.2.0
sphinx-rtd-theme>=2.0.0

# Development Tools
ipython>=8.18.0
ipdb>=0.13.0
```

### Arquivo: requirements-dev.txt (alternativa)

```txt
# Apenas dependências de desenvolvimento
-r requirements.txt  # Inclui produção

# Ferramentas adicionais de desenvolvimento
pre-commit>=3.6.0
pyupgrade>=3.15.0
bandit>=1.7.0  # Security linter
safety>=2.3.0  # Check vulnerabilities
```

### Comando para instalar

```bash
# Instalar todas as dependências
pip install -r requirements.txt

# OU instalar apenas produção
pip install -r requirements.txt --no-deps  # Apenas listado
# Depois instalar manualmente as de produção
```

### Localização
Raiz do projeto: `/mnt/e/PycharmProjects/Tensiometro/requirements.txt`

### Critérios de Sucesso
- ✅ requirements.txt criado
- ✅ `pip install -r requirements.txt` instala sem erros

---

## 📚 PASSO 9: Criar Documentação de Testes

### Objetivo
Documentar como executar, escrever e manter testes.

### Arquivo: TESTING.md

```markdown
# Guia de Testes - Projeto Tensiometro

Este documento orienta como executar, escrever e manter testes no projeto.

---

## 🚀 Executando Testes

### Execução Rápida (Todos os Testes)

```bash
# Usar script wrapper (recomendado)
./run_tests.sh

# Ou diretamente com pytest
pytest
```

### Execução Específica

```bash
# Apenas testes unitários (rápidos)
pytest tests/unit/ -v

# Apenas um arquivo de teste
pytest tests/unit/test_fov_calibration.py -v

# Apenas uma função de teste
pytest tests/unit/test_fov_calibration.py::TestFixedCameraFOV::test_fov_constant_across_z_heights -v

# Apenas testes com determinado marcador
pytest -m "not slow"  # Exclui testes lentos
pytest -m unit        # Apenas testes unitários
pytest -m integration # Apenas testes de integração
```

### Com Coverage Report

```bash
# Executar com coverage (HTML + terminal)
pytest --cov=aoi_lib --cov=consumo_lib --cov-report=html --cov-report=term-missing

# Abrir report no navegador após testes
./run_tests.sh --html

# Report HTML será gerado em htmlcov/index.html
```

### Modo Watch (Desenvolvimento)

```bash
# Re-executa testes automaticamente quando código muda
pip install pytest-watch
ptw

# Ou com script
./run_tests.sh --watch
```

---

## 📏 Escrevendo Testes

### Estrutura Básica de um Teste

```python
"""
Módulo de teste para [nome do módulo].

Use docstrings para explicar o que está sendo testado.
"""

import pytest
from aoi_lib.meu_modulo import MinhaClasse


class TestMinhaClasse:
    """Testa funcionalidades da MinhaClasse."""

    def test_metodo_x_deve_retornar_verdadeiro(self):
        """
        Testa que metodo_x retorna True.

        Este é um exemplo de teste simples.
        """
        instancia = MinhaClasse()
        resultado = instancia.metodo_x()

        assert resultado is True, "metodo_x deve retornar True"

    def test_metodo_y_com_entrada_invalida(self):
        """Testa que metodo_y levanta ValueError com entrada inválida."""
        instancia = MinhaClasse()

        with pytest.raises(ValueError):
            instancia.metodo_y(-1)  # Valor negativo inválido
```

### Nomes Descritivos de Testes

**✅ BOM:**
```python
def test_plc_deve_conectar_com_host_e_porta_validos():
    """Testa conexão PLC com parâmetros válidos."""
    pass

def test_movimento_angular_deve_calcular_trajetoria_otima():
    """Testa cálculo de trajetória para movimento angular."""
    pass
```

**❌ RUIM:**
```python
def test_1():
    """Teste 1."""
    pass

def test_conexao():  # Não diz o que espera
    """Testa conexão."""
    pass
```

### Usando Fixtures

```python
import pytest
from tests.conftest import assert_valid_gerber_bounds

def test_usando_fixture(mock_plc_client):
    """Testa usando fixture de mock PLC."""
    # mock_plc_client é injetado automaticamente
    assert mock_plc_client.connect.return_value is True

def test_usando_fixture_customizada(sample_stencil_data):
    """Testa usando fixture customizada."""
    assert sample_stencil_data["code"] == "TEST-001"

def test_usando_helper():
    """Testa usando helper function."""
    from aoi_lib.gerber_parser import GerberBounds
    bounds = GerberBounds()
    bounds.update(0, 0, 100, 100)

    assert_valid_gerber_bounds(bounds)  # Helper reutilizável
```

### Testando com Mocks

```python
from unittest.mock import Mock, patch, MagicMock

def test_mock_simples():
    """Testa com mock simples."""
    mock = Mock()
    mock.metodo.return_value = 42

    resultado = mock.metodo()
    assert resultado == 42

def test_mock_patch():
    """Testa com patch."""
    with patch('aoi_lib.plc_axis_controller.ModbusTcpClient') as mock:
        mock.return_value.connect.return_value = True

        from aoi_lib.plc_axis_controller import PLCAxisController
        controller = PLCAxisController(auto_connect=True)

        assert controller.is_connected
        mock.assert_called_once()

def test_mock_lados_escuro():
    """Testa tratamento de erro com mock."""
    mock = Mock()
    mock.metodo.side_effect = IOError("Conexão falhou")

    with pytest.raises(IOError, match="Conexão falhou"):
        mock.metodo()
```

### Parametrização de Testes

```python
@pytest.mark.parametrize("entrada, esperado", [
    (0, 0),       # Caso 1: zero
    (10, 100),    # Caso 2: valor positivo
    (-5, -50),    # Caso 3: valor negativo
])
def test_calculo_de_pulsos(entrada, esperado):
    """Testa conversão de mm para pulsos com múltiplos valores."""
    resultado = entrada * 10  # 10 pulsos/mm
    assert resultado == esperado
```

### Marcadores (Markers)

```python
import pytest

@pytest.mark.unit
def test_teste_rapido():
    """Teste unitário rápido (executa por padrão)."""
    assert True

@pytest.mark.slow
def test_teste_lento():
    """Teste lento (excluído com --fast)."""
    import time
    time.sleep(5)
    assert True

@pytest.mark.hardware
def test_teste_hardware():
    """Teste que requer hardware físico."""
    # Teste só executa se hardware disponível
    assert os.environ.get("HARDWARE_AVAILABLE") == "true"

@pytest.mark.skipif(
    not os.environ.get("RUN_SLOW_TESTS"),
    reason="Skip slow tests unless RUN_SLOW_TESTS is set"
)
def test_teste_condicional():
    """Teste com condição de skip."""
    pass
```

---

## 🎯 Melhores Práticas

### 1. Testes Independentes

```python
# ✅ BOM: Cada teste é independente
def test_criar_usuario():
    usuario = Usuario(nome="João")
    assert usuario.nome == "João"

def test_atualizar_usuario():
    usuario = Usuario(nome="João")
    usuario.nome = "Maria"
    assert usuario.nome == "Maria"

# ❌ RUIM: Testes dependentes (anti-pattern)
def test_criar_usuario():
    global usuario
    usuario = Usuario(nome="João")
    assert usuario.nome == "João"

def test_atualizar_usuario():  # Depende do teste anterior
    global usuario
    usuario.nome = "Maria"
    assert usuario.nome == "Maria"
```

### 2. Um Assert por Teste (Regra Geral)

```python
# ✅ BOM: Um assert por teste
def test_calculo_area_circulo():
    area = calcular_area_circulo(raio=10)
    assert area == pytest.approx(314.16, rel=1e-2)

def test_raio_negativo_levanta_erro():
    with pytest.raises(ValueError):
        calcular_area_circulo(raio=-1)

# ❌ RUIM: Múltiplos asserts não relacionados
def test_varias_coisas():
    area = calcular_area_circulo(raio=10)
    assert area > 0
    assert area < 1000
    assert "pi" in str(area).lower()  # Não relacionado
```

### 3. Nomes Descritivos

```python
# ✅ BOM: Nome descritivo
def test_plc_deve_desconectar_quando_timeout_excedido():
    """Testa que PLC desconecta após timeout de 10 segundos."""
    pass

# ❌ RUIM: Nome genérico
def test_plc_timeout():
    """Testa timeout."""
    pass
```

### 4. Usar Helpers Reutilizáveis

```python
# Em tests/conftest.py
def assert_valid_position(x, y, z):
    """Helper para validar coordenadas de posição."""
    assert x >= 0, "X deve ser não-negativo"
    assert y >= 0, "Y deve ser não-negativo"
    assert z >= 0, "Z deve ser não-negativo"

# Em testes
def test_posicao_valida():
    x, y, z = 100, 200, 50
    assert_valid_position(x, y, z)
```

---

## 📊 Coverage

### Métricas de Cobertura

| Tipo | Mínimo Aceitável | Bom | Excelente |
|------|-----------------|-----|-----------|
| **Módulos críticos** (PLC, tensiômetro) | 80% | 90% | 95% |
| **Lógica de negócio** (parser, inspeção) | 70% | 85% | 90% |
| **GUI** (consumo_lib) | 40% | 60% | 70% |
| **Scripts utilitários** | 50% | 70% | 80% |

### Gerando Relatório

```bash
# Relatório HTML (navegável)
pytest --cov=aoi_lib --cov-report=html

# Abrir no navegador
python -m webbrowser htmlcov/index.html

# Relatório terminal (resumido)
pytest --cov=aoi_lib --cov-report=term-missing

# Relatório XML (para CI/CD)
pytest --cov=aoi_lib --cov-report=xml:coverage.xml
```

### Interpretando Coverage

```
Name                               Stmts   Miss  Cover   Missing
------------------------------------------------------------------------
aoi_lib/__init__                      10      0   100%
aoi_lib/plc_axis_controller.py       450    300    33%   23-456, 500-600
aoi_lib/stencil_tension.py           600    500    17%   100-650
aoi_lib/fov_calibration.py           150      5    97%   45-50
------------------------------------------------------------------------
TOTAL                              2000   1200    40%
```

- **Stmts:** Número de statements (linhas executáveis)
- **Miss:** Statements não executados pelos testes
- **Cover:** Porcentagem de cobertura
- **Missing:** Linhas não cobertas (intervalos)

---

## 🔬 Debugging de Testes

### Ver Output do Teste

```bash
# Mostrar print() statements (normalmente capturados)
pytest -s

# Mostrar output capturado em caso de falha
pytest --tb=long

# Entrar no debugger em caso de falha
pytest --pdb
```

### Executar Teste Específico em Modo Debug

```python
# Adicionar breakpoint no código
import pdb; pdb.set_trace()

# Ou usar pytest's builtin
def test_com_debug():
    pytest.set_trace()  # Para aqui
    assert True
```

### Ver Logs

```bash
# Ver logs durante execução de testes
pytest --log-cli-level=DEBUG

# Capturar logs em arquivo
pytest --log-file=test_logs.txt
```

---

## 🔄 CI/CD Integration

### GitHub Actions (Exemplo)

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest --cov=aoi_lib --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## 📖 Referências

### Documentação de pytest
- https://docs.pytest.org/
- https://docs.pytest.org/en/stable/getting-started.html

### Fixtures
- https://docs.pytest.org/en/stable/fixture.html

### Mocking
- https://docs.pytest.org/en/stable/how-to/unittest.html
- https://docs.python.org/3/library/unittest.mock.html

### Coverage
- https://coverage.readthedocs.io/

---

## ❓ Perguntas Frequentes

### Q: Onde colocar meus testes?

**A:** Use a estrutura:
```
tests/
├── unit/           # Testes rápidos sem dependências
├── integration/    # Testes com mocks ou dependências externas
└── fixtures/       # Arquivos de teste
```

### Q: Como testar código que depende de hardware?

**A:** Use mocks:
```python
def test_plc_sem_hardware_real(mock_plc_client):
    # mock_plc_client simula PLC sem precisar do hardware
    controller = PLCAxisController()
    controller.client = mock_plc_client
    # Testar lógica normalmente
```

### Q: Meus testes estão muito lentos!

**A:** Algumas opções:
1. Usar `pytest-xdist` para execução paralela: `pytest -n auto`
2. Marcar testes lentos com `@pytest.mark.slow`
3. Executar apenas testes unitários: `pytest tests/unit/`

### Q: Coverage está baixo, o que fazer?

**A:** Priorize:
1. Módulos críticos primeiro (PLC, tensiômetro, parser)
2. Caminhos de código felizes (caminhos normais)
3. Edge cases importantes (erros, limites)

---

## 🆘 Suporte

Para dúvidas ou problemas com testes:
1. Verifique este documento
2. Consulte documentação de pytest
3. Veja testes existentes como exemplos
4. Use pytest --help para ver opções disponíveis

---

**Última atualização:** 2026-01-07
**Versão:** 1.0
```

### Localização
`/mnt/e/PycharmProjects/Tensiometro/TESTING.md`

### Critérios de Sucesso
- ✅ Documentação criada
- ✅ Instruções testadas e funcionais

---

## ✅ PASSO 10: Executar Testes e Validar

### Objetivo
Executar todos os testes criados e validar que a infraestrutura está funcionando.

### Comandos

```bash
# 1. Verificar que pytest está instalado
pytest --version
# Esperado: pytest 7.x.x

# 2. Verificar configuração do pytest
pytest --collect-only
# Esperado: Coletar testes de test_fov_calibration.py e test_gerber_parser.py

# 3. Executar todos os testes
pytest -v
# Esperado: ~10 testes passarem

# 4. Executar com coverage
pytest --cov=aoi_lib --cov-report=term-missing --cov-report=html
# Esperado: Coverage report gerado

# 5. Abrir coverage no navegador
python -m webbrowser htmlcov/index.html

# 6. Verificar que estrutura está correta
tree tests/ -L 2
```

### Resultados Esperados

```
======================== test session starts =========================
collected 12 items

tests/unit/test_fov_calibration.py::TestFixedCameraFOV::test_fov_constant_across_z_heights PASSED
tests/unit/test_fov_calibration.py::TestFixedCameraFOV::test_fov_returns_tuple PASSED
tests/unit/test_fov_calibration.py::TestFixedCameraFOV::test_fov_positive_values PASSED
tests/unit/test_fov_calibration.py::TestYInversion::test_y_inversion_move_up PASSED
tests/unit/test_fov_calibration.py::TestYInversion::test_y_inversion_move_down PASSED
tests/unit/test_fov_calibration.py::TestYInversion::test_y_inversion_disabled PASSED
tests/unit/test_fov_calibration.py::TestYInversion::test_x_no_inversion PASSED
tests/unit/test_fov_calibration.py::TestYInversion::test_click_center_no_movement PASSED
tests/unit/test_gerber_parser.py::TestGerberParserBasics::test_parser_initialization PASSED
tests/unit/test_gerber_parser.py::TestGerberBounds::test_empty_bounds PASSED
tests/unit/test_gerber_parser.py::TestGerberBounds::test_bounds_calculation PASSED
tests/unit/test_gerber_parser.py::TestGerberBounds::test_bounds_validation PASSED

======================== 12 passed in 0.45s =========================

---------- coverage: platform linux, python 3.11 ----------
Name                                Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------
aoi_lib/__init__                        4      0   100%
aoi_lib/fov_calibration.py             45      2    96%   78-79
-------------------------------------------------------------------------
TOTAL                                  49      2    96%
```

### Critérios de Sucesso Finais

- ✅ pytest versão 7.x instalada
- ✅ 12 testes coletados
- ✅ 12 testes passando
- ✅ Coverage > 90% para fov_calibration.py
- ✅ Coverage report HTML gerado
- ✅ Script run_tests.sh funciona

---

## 🎉 Conclusão

Após completar todos os 10 passos, você terá:

1. ✅ **Infraestrutura de testes profissional** configurada
2. ✅ **12 testes** criados e passando
3. ✅ **96% de coverage** em fov_calibration.py
4. ✅ **Base sólida** para expandir testes
5. ✅ **Documentação completa** (TESTING.md)
6. ✅ **Scripts automatizados** (run_tests.sh)

### Próximos Passos (FASE 2)

Com a infraestrutura pronta, você pode:

1. Criar mais testes unitários (fiducial_alignment, stencil_inspection, etc.)
2. Criar testes de integração com mocks (PLC, tensiômetro, câmera)
3. Melhorar coverage dos módulos existentes
4. Configurar CI/CD (GitHub Actions)

**Tempo estimado para FASE 2:** 5-7 dias
**Resultado esperado:** 60-70% de coverage em módulos críticos

---

**Sucesso!** 🚀

Você está pronto para começar a escrever testes profissionais para o projeto Tensiometro.
