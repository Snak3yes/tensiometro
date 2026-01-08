# Guia de Testes - Projeto Tensiometro

Este documento orienta como executar, escrever e manter testes no projeto.

---

## 🚀 Executando Testes

### Execução Rápida

```bash
# Usar script wrapper (recomendado no Windows)
run_tests.bat

# Ou diretamente com pytest
.venv/Scripts/python.exe -m pytest
```

### Execução Específica

```bash
# Apenas testes unitários
pytest tests/unit/ -v

# Apenas um arquivo
pytest tests/unit/test_fov_calibration.py -v

# Apenas uma função de teste
pytest tests/unit/test_fov_calibration.py::TestFixedCameraFOV::test_fov_constant_across_z_heights -v

# Apenas testes rápidos (exclui lentos e hardware)
pytest -m "not slow and not hardware" -v
```

### Com Coverage Report

```bash
# Executar com coverage
pytest --cov=aoi_lib --cov-report=html --cov-report=term-missing

# Abrir report no navegador após testes
run_tests.bat --html

# Report HTML será gerado em htmlcov/index.html
```

---

## 📏 Escrevendo Testes

### Estrutura Básica

```python
"""
Módulo de teste para [nome do módulo].
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

### Nomes Descritivos

**✅ BOM:**
```python
def test_plc_deve_conectar_com_host_e_porta_validos():
    """Testa conexão PLC com parâmetros válidos."""
    pass
```

**❌ RUIM:**
```python
def test_1():
    """Teste 1."""
    pass
```

### Usando Fixtures

```python
def test_usando_fixture(mock_plc_client):
    """Testa usando fixture de mock PLC."""
    # mock_plc_client é injetado automaticamente
    assert mock_plc_client.connect.return_value is True

def test_usando_fixture_customizada(sample_stencil_data):
    """Testa usando fixture customizada."""
    assert sample_stencil_data["code"] == "TEST-001"
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
    pass
```

---

## 🧩 Fixtures Disponíveis

### Hardware Mocks

- **mock_plc_client**: Mock de cliente Modbus TCP para PLC Delta
- **mock_serial_connection**: Mock de conexão serial para tensiômetro AS-120N
- **mock_camera**: Mock de câmera OpenCV

### Imagens Sintéticas

- **blank_image**: Imagem branca (640x480x3)
- **black_image**: Imagem preta (640x480x3)
- **gray_image**: Imagem cinza (640x480x3)

### Dados de Teste

- **sample_stencil_data**: Dados de stencil de exemplo
- **sample_recipe_data**: Dados de receita de exemplo
- **sample_tension_measurements**: Grid 3x3 de medições

### Arquivos

- **temp_config_file**: Arquivo de configuração temporário
- **gerber_fixtures_dir**: Diretório para arquivos Gerber de teste
- **image_fixtures_dir**: Diretório para imagens de teste

---

## 🎯 Melhores Práticas

### 1. Testes Independentes

```python
# ✅ BOM: Cada teste é independente
def test_criar_usuario():
    usuario = Usuario(nome="João")
    assert usuario.nome == "João"

# ✅ BOM: Novo teste independente
def test_atualizar_usuario():
    usuario = Usuario(nome="João")  # Nova instância
    usuario.nome = "Maria"
    assert usuario.nome == "Maria"
```

### 2. Um Assert por Teste

```python
# ✅ BOM: Um assert claro
def test_calculo_area_circulo():
    area = calcular_area_circulo(raio=10)
    assert area == pytest.approx(314.16, rel=1e-2)
```

### 3. Nomes Descritivos

```python
# ✅ BOM: Nome descritivo
def test_plc_deve_desconectar_quando_timeout_excedido():
    """Testa que PLC desconecta após timeout de 10 segundos."""
    pass
```

### 4. Helpers Reutilizáveis

Disponíveis em `tests/conftest.py`:

```python
from tests.conftest import assert_valid_gerber_bounds

def test_posicao_valida():
    bounds = GerberBounds()
    bounds.update(0, 0, 100, 100)
    assert_valid_gerber_bounds(bounds)  # Helper reutilizável
```

---

## 📊 Coverage

### Executando com Coverage

```bash
# Relatório HTML (navegável)
pytest --cov=aoi_lib --cov-report=html

# Abrir no navegador
python -m webbrowser htmlcov/index.html

# Relatório terminal (resumido)
pytest --cov=aoi_lib --cov-report=term-missing
```

### Métricas de Cobertura

| Tipo | Mínimo Aceitável | Bom | Excelente |
|------|-----------------|-----|-----------|
| **Módulos críticos** | 80% | 90% | 95% |
| **Lógica de negócio** | 70% | 85% | 90% |
| **GUI** | 40% | 60% | 70% |

---

## 🔬 Debugging de Testes

### Ver Output

```bash
# Mostrar print() statements
pytest -s

# Mostrar output em caso de falha
pytest --tb=long

# Entrar no debugger em caso de falha
pytest --pdb
```

### Executar Teste Específico

```bash
# Apenas uma classe de testes
pytest tests/unit/test_fov_calibration.py::TestFixedCameraFOV -v

# Apenas um método
pytest tests/unit/test_fov_calibration.py::TestFixedCameraFOV::test_fov_constant_across_z_heights -v
```

---

## 📖 Referências

### Documentação
- pytest: https://docs.pytest.org/
- Fixtures: https://docs.pytest.org/en/stable/fixture.html
- Mocking: https://docs.python.org/3/library/unittest.mock.html
- Coverage: https://coverage.readthedocs.io/

### Scripts do Projeto

- `run_tests.bat` - Script wrapper para executar testes
- `pytest.ini` - Configuração do pytest
- `tests/conftest.py` - Fixtures globais

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

**A:** Use os mocks disponíveis:
```python
def test_plc_sem_hardware_real(mock_plc_client):
    # mock_plc_client simula PLC sem precisar do hardware
    controller = PLCAxisController()
    controller.client = mock_plc_client
    # Testar lógica normalmente
```

### Q: Meus testes estão muito lentos!

**A:** Algumas opções:
1. Executar apenas testes unitários: `pytest tests/unit/`
2. Marcar testes lentos: `@pytest.mark.slow`
3. Executar apenas rápidos: `pytest -m "not slow"`

---

**Última atualização:** 2026-01-07
**Versão:** 1.0
**Status:** Básico - Pronto para expansão
