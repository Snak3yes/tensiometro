# AlignmentWidget - Guia de Uso (Track 5)

**Data:** 2026-01-13
**Versão:** 1.0
**Status:** Produção

---

## 📋 ÍNDICE

1. [Visão Geral](#visão-geral)
2. [Instalação](#instalação)
3. [Uso Básico](#uso-básico)
4. [Funcionalidades](#funcionalidades)
5. [Integração com Engineering Wizard](#integração)
6. [API Reference](#api-reference)

---

## 🎯 VISÃO GERAL

O `AlignmentWidget` é a **Track 5** do Engineering Wizard, responsável por alinhar o arquivo Gerber sobre o mosaico capturado do stencil.

### Funcionalidades Principais

- ✅ Preview do mosaico + overlay do Gerber com zoom/pan
- ✅ Controles manuais de transformação (translação X/Y, rotação, escala)
- ✅ Controles finos (slider de opacidade, drag & move do overlay)
- ✅ Auto-tuning usando template matching dos fiduciais
- ✅ Score de matching com indicador visual
- ✅ Reset para estado inicial
- ✅ Validação de alinhamento (score ≥ 70% ou fiduciais encontrados)

### Signals Emitidos

- `validationChanged(isValid)` - Emitido quando validação muda
- `alignmentApplied(transform_data)` - Emitido quando alinhamento é aplicado

---

## 📦 INSTALAÇÃO

O widget está localizado em:
```
consumo_lib/widgets/engenharia/alignment_widget.py
```

### Importação

```python
from consumo_lib.widgets.engenharia.alignment_widget import AlignmentWidget
```

---

## 🚀 USO BÁSICO

### Exemplo 1: Criar e Exibir Widget

```python
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from consumo_lib.widgets.engenharia.alignment_widget import AlignmentWidget
import numpy as np

app = QApplication([])

# Cria janela principal
window = QMainWindow()
central_widget = QWidget()
layout = QVBoxLayout(central_widget)

# Cria widget de alinhamento
alignment_widget = AlignmentWidget()
layout.addWidget(alignment_widget)

window.setCentralWidget(central_widget)
window.show()

# Carrega dados (ver seção completa abaixo)
# mosaic_image = ...
# gerber_data = ...
# fiducial_templates = ...
# alignment_widget.load_data(mosaic_image, gerber_data, fiducial_templates)

app.exec()
```

### Exemplo 2: Carregar Dados

```python
import cv2
import numpy as np

# 1. Carrega mosaico capturado
mosaic_image = cv2.imread('data/mosaico_stencil.png')

# 2. Carrega dados do Gerber
from aoi_lib.gerber_parser import GerberParser

parser = GerberParser()
parsed_gerber = parser.parse_file('stencil.gbr')

gerber_data = {
    'parsed': parsed_gerber,
    'fiducial_positions': [(50.0, 50.0), (200.0, 50.0)]  # Posição dos fiduciais no Gerber (mm)
}

# 3. Templates de fiduciais capturados (da aba anterior)
fiducial_templates = [
    {
        'name': 'Fiducial A',
        'image': cv2.imread('fiducial_a.png'),  # Template 50x50
        'position': (100, 100)  # Posição no mosaico (pixels)
    },
    {
        'name': 'Fiducial B',
        'image': cv2.imread('fiducial_b.png'),
        'position': (300, 100)
    }
]

# Carrega dados no widget
alignment_widget.load_data(
    mosaic_image=mosaic_image,
    gerber_data=gerber_data,
    fiducial_templates=fiducial_templates
)
```

### Exemplo 3: Capturar Resultado

```python
# Conecta signal de aplicação
def on_alignment_applied(data):
    """Handler chamado quando usuário aplica alinhamento."""
    transform = data['transform']
    score = data['score']
    fiducials_found = data['fiducials_found']

    print(f"Alinhamento aplicado:")
    print(f"  Translação: ({transform['tx']:.1f}, {transform['ty']:.1f}) px")
    print(f"  Rotação: {transform['angle']:.2f}°")
    print(f"  Escala: {transform['scale']:.4f}")
    print(f"  Score: {score:.1f}%")
    print(f"  Fiduciais encontrados: {fiducials_found}")

alignment_widget.alignmentApplied.connect(on_alignment_applied)

# OU obtém dados diretamente:
data = alignment_widget.get_alignment_data()
```

---

## ⚙️ FUNCIONALIDADES

### 1. Controles Manuais de Transformação

O widget oferece 4 controles manuais:

- **Translação X** (-1000 a 1000 px): Move overlay horizontalmente
- **Translação Y** (-1000 a 1000 px): Move overlay verticalmente
- **Rotação** (-180° a 180°): Rotaciona overlay
- **Escala** (0.1 a 10.0): Redimensiona overlay

```python
# Ajusta valores programaticamente
alignment_widget.spin_tx.setValue(50.0)  # Move 50px para direita
alignment_widget.spin_ty.setValue(-20.0)  # Move 20px para cima
alignment_widget.spin_angle.setValue(5.0)  # Rotaciona 5°
alignment_widget.spin_scale.setValue(1.1)  # Aumenta 10%
```

### 2. Controles Finos

#### Opacidade do Overlay

```python
# Ajusta opacidade (0-100%)
alignment_widget.slider_opacity.setValue(75)  # 75% de opacidade

# Lê valor atual
opacity = alignment_widget._state.opacity  # 0.0 a 1.0
```

#### Arraste do Overlay (Drag & Move)

O usuário pode clicar e arrastar o overlay diretamente na visualização.

```python
# Isso é feito automaticamente pelo widget
# quando o usuário clica e arrasta na área do overlay
```

### 3. Auto-Tuning

O auto-tuning usa template matching para encontrar fiduciais automaticamente:

```python
# Dispara auto-tuning
alignment_widget._on_auto_tune()

# Processo:
# 1. Busca fiduciais usando templates capturados
# 2. Calcula transformação ótima (translação + rotação + escala)
# 3. Aplica transformação nos controles manuais
# 4. Atualiza score de alinhamento
```

### 4. Score de Alinhamento

O score é calculado automaticamente baseado na transformação:

```python
# Lê score atual
score = alignment_widget._state.score  # 0.0 a 100.0

# Visualização:
# - Verde (score ≥ 90%): Alinhamento excelente
# - Laranja (70% ≤ score < 90%): Alinhamento aceitável
# - Vermelho (score < 70%): Alinhamento ruim
```

### 5. Reset

```python
# Volta ao estado inicial
alignment_widget._on_reset()

# Usuário confirma caixa de diálogo antes de resetar
```

### 6. Validação

```python
# Verifica se alinhamento é válido
is_valid = alignment_widget.is_valid()
# Válido se: score ≥ 70% OU fiduciais foram encontrados

# Conecta signal de validação
def on_validation_changed(is_valid):
    print(f"Alinhamento válido: {is_valid}")
    # Habilita/desabilita botão "Próximo", por exemplo

alignment_widget.validationChanged.connect(on_validation_changed)
```

---

## 🔗 INTEGRAÇÃO COM ENGINEERING WIZARD

### Exemplo de Integração Completa

```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton
from consumo_lib.widgets.engenharia.alignment_widget import AlignmentWidget

class EngineeringWizardDialog(QDialog):
    """Dialog principal do Engineering Wizard."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Engineering Wizard - Criar Programa de Inspeção")
        self.setMinimumSize(1200, 800)

        layout = QVBoxLayout(self)

        # Widget de alinhamento (Track 5)
        self.alignment_widget = AlignmentWidget()
        layout.addWidget(self.alignment_widget)

        # Botões de navegação
        btn_layout = QHBoxLayout()

        self.btn_previous = QPushButton("← Anterior")
        self.btn_previous.clicked.connect(self._on_previous)
        btn_layout.addWidget(self.btn_previous)

        btn_layout.addStretch()

        self.btn_next = QPushButton("Próximo →")
        self.btn_next.clicked.connect(self._on_next)
        self.btn_next.setEnabled(False)  # Desabilitado até validação
        btn_layout.addWidget(self.btn_next)

        layout.addLayout(btn_layout)

        # Conecta sinais
        self.alignment_widget.validationChanged.connect(self._on_validation_changed)
        self.alignment_widget.alignmentApplied.connect(self._on_alignment_applied)

        # Dados das tracks anteriores
        self._data = {
            'mosaic_image': None,
            'gerber_data': None,
            'fiducial_templates': None
        }

    def load_from_previous_track(self, data):
        """Carrega dados da track anterior (Mosaic Capture)."""
        self._data.update(data)

        # Carrega no widget de alinhamento
        self.alignment_widget.load_data(
            mosaic_image=self._data['mosaic_image'],
            gerber_data=self._data['gerber_data'],
            fiducial_templates=self._data['fiducial_templates']
        )

    def _on_validation_changed(self, is_valid):
        """Handler: validação alterada."""
        self.btn_next.setEnabled(is_valid)

    def _on_alignment_applied(self, data):
        """Handler: alinhamento aplicado."""
        # Salva dados da track 5
        self._data['alignment'] = data

        # Avança para próxima track
        self.accept()

    def _on_previous(self):
        """Volta para track anterior."""
        self.reject()

    def _on_next(self):
        """Avança para próxima track."""
        # Força aplicação do alinhamento
        self.alignment_widget._on_apply()

    def get_data(self):
        """Retorna dados coletados."""
        return self._data
```

---

## 📚 API REFERENCE

### Classe `AlignmentWidget`

#### Métodos Públicos

```python
def load_data(
    self,
    mosaic_image: np.ndarray,
    gerber_data: dict,
    fiducial_templates: list
) -> None:
    """
    Carrega dados para alinhamento.

    Args:
        mosaic_image: Imagem do mosaico capturado (BGR, numpy array)
        gerber_data: Dicionário com dados do Gerber:
            {
                'parsed': ParsedGerber,  # Objeto do parser
                'fiducial_positions': [(x1, y1), (x2, y2)]  # mm
            }
        fiducial_templates: Lista de templates capturados:
            [
                {
                    'name': str,       # 'Fiducial A', 'Fiducial B'
                    'image': np.ndarray,  # Template 50x50
                    'position': (x, y)  # Posição no mosaico (pixels)
                },
                ...
            ]
    """

def get_alignment_data(self) -> dict:
    """
    Retorna dados do alinhamento.

    Returns:
        dict: {
            'transform': {
                'tx': float,      # Translação X (pixels)
                'ty': float,      # Translação Y (pixels)
                'angle': float,   # Rotação (graus)
                'scale': float    # Escala (fator)
            },
            'score': float,              # Score 0-100
            'fiducials_found': bool      # Fiduciais encontrados?
        }
    """

def is_valid(self) -> bool:
    """
    Verifica se alinhamento é válido.

    Returns:
        True se score ≥ 70% OU fiduciais foram encontrados
    """
```

#### Signals

```python
# Emitido quando validação muda
validationChanged = pyqtSignal(bool)  # isValid

# Emitido quando alinhamento é aplicado
alignmentApplied = pyqtSignal(dict)  # alignment_data
```

#### Atributos Públicos

```python
# Componentes de UI
image_view: AlignmentImageView  # Preview do mosaico + overlay
slider_zoom: QSlider            # Controle de zoom
lbl_zoom: QLabel                # Label de zoom (%)
spin_tx: QDoubleSpinBox         # Translação X (px)
spin_ty: QDoubleSpinBox         # Translação Y (px)
spin_angle: QDoubleSpinBox      # Rotação (graus)
spin_scale: QDoubleSpinBox      # Escala (fator)
slider_opacity: QSlider         # Opacidade do overlay (0-100)
lbl_opacity: QLabel             # Label de opacidade (%)
lbl_score: QLabel               # Label de score (%)
indicator_score: QLabel         # Indicador visual
btn_auto_tune: QPushButton      # Botão auto-tuning
btn_reset: QPushButton          # Botão reset
btn_apply: QPushButton          # Botão aplicar

# Estado interno
_state: AlignmentState           # Estado do alinhamento
_mosaic_image: np.ndarray       # Imagem do mosaico
_gerber_data: dict              # Dados do Gerber
_fiducial_templates: list       # Templates de fiduciais
_initial_state: AlignmentState  # Estado inicial (para reset)
```

### Classe `AlignmentState`

Dataclass que representa o estado do alinhamento:

```python
@dataclass
class AlignmentState:
    tx: float = 0.0           # Translação X (pixels)
    ty: float = 0.0           # Translação Y (pixels)
    angle: float = 0.0        # Rotação (graus)
    scale: float = 1.0        # Escala (fator)
    opacity: float = 0.5      # Opacidade do overlay (0-1)
    score: float = 0.0        # Score de alinhamento (0-100)
    fiducials_found: bool = False  # Fiduciais foram encontrados?
```

---

## 🧪 TESTES

### Executar Testes

```bash
# Todos os testes do widget
pytest tests/unit/widgets/engenharia/test_alignment_widget.py -v

# Com coverage
pytest tests/unit/widgets/engenharia/test_alignment_widget.py --cov=consumo_lib/widgets/engenharia/alignment_widget --cov-report=html
```

### Cobertura de Código

Atualmente: **80%** de cobertura

Testes implementados:
- ✅ Inicialização (4 testes)
- ✅ Carregamento de dados (4 testes)
- ✅ Controles de transformação (5 testes)
- ✅ Controles finos (2 testes)
- ✅ Auto-tuning (3 testes)
- ✅ Reset (2 testes)
- ✅ Validação (4 testes)
- ✅ Aplicação (3 testes)
- ✅ Visualização (5 testes)
- ✅ Estado (2 testes)

**Total: 34 testes, 100% passando**

---

## 📝 EXEMPLO PRÁTICO

### Fluxo Completo: Tracks 1-5

```python
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget
from consumo_lib.widgets.engenharia.alignment_widget import AlignmentWidget

class EngineeringWizard(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Engineering Wizard")

        layout = QVBoxLayout(self)

        # Tabs (abas)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Track 5: Alignment
        self.alignment_tab = AlignmentWidget()
        self.tabs.addTab(self.alignment_tab, "5. Alinhamento")

        # ... outras tracks (1-4, 6-7)

    def run_track_5(self):
        """Executa Track 5 com dados das tracks anteriores."""

        # Dados coletados nas tracks anteriores
        mosaic_image = self._data['track4']['mosaic_image']
        gerber_data = self._data['track2']['gerber_data']
        fiducial_templates = self._data['track3']['fiducial_templates']

        # Carrega dados
        self.alignment_tab.load_data(
            mosaic_image=mosaic_image,
            gerber_data=gerber_data,
            fiducial_templates=fiducial_templates
        )

        # Mostra tab
        self.tabs.setCurrentWidget(self.alignment_tab)

        # Aguarda usuário completar
        if self.exec() == QDialog.DialogCode.Accepted:
            # Alinhamento aplicado
            alignment_data = self.alignment_tab.get_alignment_data()
            self._data['track5'] = alignment_data
            return True
        else:
            # Usuário cancelou
            return False
```

---

## 🔧 SOLUÇÃO DE PROBLEMAS

### Problema: Score muito baixo (< 50%)

**Causa provável:** Mosaico e Gerber não correspondem

**Solução:**
1. Verifique se o mosaico capturado está correto
2. Verifique se o arquivo Gerber é o do stencil correto
3. Tente auto-tuning novamente
4. Ajuste manualmente os controles

### Problema: Auto-tuning falha

**Causa provável:** Templates de fiduciais ruins

**Solução:**
1. Recapture os templates na Track 3
2. Certifique-se de que os templates estão nítidos
3. Aumente o raio de busca nos parâmetros

### Problema: Overlay não aparece

**Causa provável:** Gerber não foi renderizado

**Solução:**
1. Verifique se `gerber_data['parsed']` não é None
2. Verifique se o GerberParser funcionou corretamente
3. Ajuste a opacidade do overlay (pode estar muito transparente)

---

## 📚 REFERÊNCIAS

- **FiducialAlignmentWidget** (`aoi_lib/fiducial_alignment_widget.py`): Widget original de alinhamento
- **GerberRenderer** (`aoi_lib/gerber_renderer.py`): Renderização de Gerber
- **FiducialAligner** (`aoi_lib/fiducial_alignment.py`): Algoritmo de alinhamento
- **Engenharia Questionários** (`docs/guides/QUESTIONARIO_FLUXO_ENGENHARIA_FASE2.md`): Especificação

---

**Autor:** Claude Code (Sonnet 4.5)
**Data:** 2026-01-13
**Versão:** 1.0
**Status:** ✅ Produção - Todos os testes passando
