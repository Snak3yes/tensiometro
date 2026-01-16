"""
Testes unitários para AlignmentWidget (Track 5)

Testes:
- Inicialização do widget
- Carregamento de dados (mosaico, gerber, fiduciais)
- Controles manuais de transformação
- Auto-tuning
- Reset
- Validação
- Sinais emitidos
"""

import sys
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtTest import QTest

# Caminho para importação
sys.path.insert(0, '.')
sys.path.insert(0, 'E:/PycharmProjects/Tensiometro')

from consumo_lib.widgets.engenharia.alignment_widget import (
    AlignmentWidget, AlignmentImageView, AlignmentState
)


# Fixture para QApplication (necessário para widgets PyQt6)
@pytest.fixture(scope="session")
def qapp():
    """
    Cria QApplication uma vez por sessão de testes.

    MARKED AS SLOW: Criar QApplication é uma operação cara em termos de performance.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Não executa app.quit() para evitar problemas com outros testes


@pytest.fixture
def widget(qapp):
    """Cria instância do widget para cada teste."""
    widget = AlignmentWidget()
    yield widget
    widget.deleteLater()


@pytest.fixture
def sample_mosaic():
    """Cria imagem de mosaico de teste."""
    # Cria imagem 640x480 com gradiente simples
    h, w = 480, 640
    img = np.zeros((h, w, 3), dtype=np.uint8)

    for i in range(h):
        for j in range(w):
            img[i, j] = [j * 255 // w, i * 255 // h, 128]

    return img


@pytest.fixture
def sample_gerber_data():
    """Cria dados de Gerber mockados."""
    # Mock do ParsedGerber
    parsed_gerber = Mock()
    parsed_gerber.bounds = Mock(
        min_x=0.0, max_x=100.0,
        min_y=0.0, max_y=100.0
    )

    return {
        'parsed': parsed_gerber,
        'fiducial_positions': [(50.0, 50.0), (200.0, 50.0)]
    }


@pytest.fixture
def sample_fiducial_templates():
    """Cria templates de fiduciais de teste."""
    # Cria 2 templates de teste (imagens 50x50)
    templates = []

    for i in range(2):
        img = np.random.randint(0, 256, (50, 50, 3), dtype=np.uint8)
        templates.append({
            'name': f'Fiducial {chr(65 + i)}',  # Fiducial A, B
            'image': img,
            'position': (100 + i * 200, 100)
        })

    return templates


# ===========================================================================
#  TESTES DE INICIALIZAÇÃO
# ===========================================================================

@pytest.mark.slow
class TestAlignmentWidgetInitialization:
    """
    Testes de inicialização do AlignmentWidget.

    MARKED AS SLOW: Usa qapp fixture que cria QApplication PyQt6.
    """

    def test_initialization(self, widget):
        """Testa se widget é inicializado corretamente."""
        assert widget is not None
        # Verifica atributos individualmente (timestamp pode variar)
        state = widget._state
        assert state.tx == 0.0
        assert state.ty == 0.0
        assert state.angle == 0.0
        assert state.scale == 1.0
        assert state.opacity == 0.5
        assert state.score == 0.0
        assert state.fiducials_found is False
        assert state.is_valid is False
        assert widget._mosaic_image is None
        assert widget._gerber_data is None
        assert widget._fiducial_templates == []

    def test_ui_components_exist(self, widget):
        """Testa se componentes da UI existem."""
        # Preview
        assert hasattr(widget, 'image_view')
        assert isinstance(widget.image_view, AlignmentImageView)

        # Controles de zoom
        assert hasattr(widget, 'slider_zoom')
        assert hasattr(widget, 'lbl_zoom')

        # Controles de transformação
        assert hasattr(widget, 'spin_tx')
        assert hasattr(widget, 'spin_ty')
        assert hasattr(widget, 'spin_angle')
        assert hasattr(widget, 'spin_scale')

        # Controles finos
        assert hasattr(widget, 'slider_opacity')
        assert hasattr(widget, 'lbl_opacity')

        # Botões
        assert hasattr(widget, 'btn_auto_tune')
        assert hasattr(widget, 'btn_reset')
        assert hasattr(widget, 'btn_apply')

    def test_initial_values(self, widget):
        """Testa valores iniciais dos controles."""
        # Transformação
        assert widget.spin_tx.value() == 0.0
        assert widget.spin_ty.value() == 0.0
        assert widget.spin_angle.value() == 0.0
        assert widget.spin_scale.value() == 1.0

        # Opacidade
        assert widget.slider_opacity.value() == 50
        assert widget.lbl_opacity.text() == "50%"

        # Zoom
        assert widget.slider_zoom.value() == 100
        assert widget.lbl_zoom.text() == "100%"

    def test_not_valid_initially(self, widget):
        """Testa que widget não é válido inicialmente."""
        assert not widget.is_valid()


# ===========================================================================
#  TESTES DE CARREGAMENTO DE DADOS
# ===========================================================================

@pytest.mark.slow
class TestAlignmentWidgetDataLoading:
    """Testes de carregamento de dados no widget."""

    def test_load_mosaic(self, widget, sample_mosaic):
        """Testa carregamento do mosaico."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        assert widget._mosaic_image is not None
        assert widget._mosaic_image.shape == sample_mosaic.shape

    def test_load_gerber_data(self, widget, sample_mosaic, sample_gerber_data):
        """Testa carregamento de dados do Gerber."""
        with patch.object(widget, '_render_gerber_overlay'):
            widget.load_data(
                mosaic_image=sample_mosaic,
                gerber_data=sample_gerber_data,
                fiducial_templates=[]
            )

            assert widget._gerber_data is not None
            assert 'parsed' in widget._gerber_data

    def test_load_fiducial_templates(
        self, widget, sample_mosaic, sample_fiducial_templates
    ):
        """Testa carregamento de templates de fiduciais."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=sample_fiducial_templates
        )

        assert len(widget._fiducial_templates) == 2
        assert widget._fiducial_templates[0]['name'] == 'Fiducial A'
        assert widget._fiducial_templates[1]['name'] == 'Fiducial B'

    def test_initial_state_saved(
        self, widget, sample_mosaic, sample_gerber_data, sample_fiducial_templates
    ):
        """Testa que estado inicial é salvo após carregar dados."""
        with patch.object(widget, '_render_gerber_overlay'):
            widget.load_data(
                mosaic_image=sample_mosaic,
                gerber_data=sample_gerber_data,
                fiducial_templates=sample_fiducial_templates
            )

            assert widget._initial_state is not None
            assert widget._initial_state.tx == 0.0
            assert widget._initial_state.ty == 0.0
            assert widget._initial_state.angle == 0.0
            assert widget._initial_state.scale == 1.0


# ===========================================================================
#  TESTES DE CONTROLES DE TRANSFORMAÇÃO
# ===========================================================================

@pytest.mark.slow
class TestAlignmentWidgetTransformControls:
    """Testes dos controles de transformação."""

    def test_translation_x(self, widget, sample_mosaic):
        """Testa controle de translação X."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        widget.spin_tx.setValue(50.0)

        assert widget._state.tx == 50.0
        assert widget.spin_tx.value() == 50.0

    def test_translation_y(self, widget, sample_mosaic):
        """Testa controle de translação Y."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        widget.spin_ty.setValue(-30.0)

        assert widget._state.ty == -30.0
        assert widget.spin_ty.value() == -30.0

    def test_rotation(self, widget, sample_mosaic):
        """Testa controle de rotação."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        widget.spin_angle.setValue(15.5)

        assert widget._state.angle == 15.5
        assert widget.spin_angle.value() == 15.5

    def test_scale(self, widget, sample_mosaic):
        """Testa controle de escala."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        widget.spin_scale.setValue(1.5)

        assert widget._state.scale == 1.5
        assert widget.spin_scale.value() == 1.5

    def test_combined_transform(self, widget, sample_mosaic):
        """Testa transformação combinada."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        widget.spin_tx.setValue(10.0)
        widget.spin_ty.setValue(-20.0)
        widget.spin_angle.setValue(5.0)
        widget.spin_scale.setValue(1.1)

        assert widget._state.tx == 10.0
        assert widget._state.ty == -20.0
        assert widget._state.angle == 5.0
        assert widget._state.scale == 1.1


# ===========================================================================
#  TESTES DE CONTROLES FINOS
# ===========================================================================

@pytest.mark.slow
class TestAlignmentWidgetFineControls:
    """Testes dos controles finos."""

    def test_opacity_slider(self, widget, sample_mosaic):
        """Testa slider de opacidade."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        widget.slider_opacity.setValue(75)

        assert widget._state.opacity == 0.75
        assert widget.lbl_opacity.text() == "75%"

    def test_opacity_range(self, widget, sample_mosaic):
        """Testa range de opacidade."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        # Valor mínimo
        widget.slider_opacity.setValue(0)
        assert widget._state.opacity == 0.0

        # Valor máximo
        widget.slider_opacity.setValue(100)
        assert widget._state.opacity == 1.0


# ===========================================================================
#  TESTES DE AUTO-TUNING
# ===========================================================================

@pytest.mark.slow
class TestAlignmentWidgetAutoTuning:
    """Testes de auto-tuning."""

    def test_auto_tune_without_mosaic(self, widget):
        """Testa auto-tuning sem mosaico carregado."""
        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            widget._on_auto_tune()

            assert mock_warning.called
            args = mock_warning.call_args[0]
            assert "Erro" in args[1]  # Título do messagebox

    def test_auto_tune_without_fiducials(
        self, widget, sample_mosaic
    ):
        """Testa auto-tuning sem fiduciais configurados."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        with patch('PyQt6.QtWidgets.QMessageBox.warning') as mock_warning:
            widget._on_auto_tune()

            assert mock_warning.called
            args = mock_warning.call_args[0]
            assert "Erro" in args[1]  # Título do messagebox

    def test_auto_tune_success(
        self, widget, sample_mosaic, sample_fiducial_templates
    ):
        """Testa auto-tuning com sucesso."""
        from consumo_lib.models.alignment_state import AlignmentState, FiducialMatch

        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=sample_fiducial_templates
        )

        # Cria resultado de sucesso do serviço
        success_state = AlignmentState(
            tx=5.0,
            ty=-3.0,
            angle=0.5,
            scale=1.01,
            score=87.5,  # média de 85.0 e 90.0
            fiducial_matches=[
                FiducialMatch(
                    template_id=1,
                    found=True,
                    x=100.0,
                    y=100.0,
                    score=85.0,
                    expected_x=100.0,
                    expected_y=100.0
                ),
                FiducialMatch(
                    template_id=2,
                    found=True,
                    x=200.0,
                    y=100.0,
                    score=90.0,
                    expected_x=200.0,
                    expected_y=100.0
                )
            ]
        )
        # Métricas são calculadas automaticamente em __post_init__
        success_state.is_valid = success_state.metrics.is_acceptable

        # Mock do AlignmentResult
        mock_result = Mock()
        mock_result.success = True
        mock_result.state = success_state
        mock_result.error = None

        # Mock do serviço
        with patch.object(widget._fiducial_service, 'align', return_value=mock_result):
            with patch('PyQt6.QtWidgets.QMessageBox.information'):
                widget._on_auto_tune()

                # Verifica que transformação foi aplicada
                assert widget._state.tx == 5.0
                assert widget._state.ty == -3.0
                assert widget._state.angle == 0.5
                assert widget._state.scale == 1.01
                assert widget._state.fiducials_found is True


# ===========================================================================
#  TESTES DE RESET
# ===========================================================================

@pytest.mark.slow
class TestAlignmentWidgetReset:
    """Testes de reset."""

    def test_reset_to_initial_state(self, widget, sample_mosaic):
        """Testa reset para estado inicial."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        # Modifica valores
        widget.spin_tx.setValue(50.0)
        widget.spin_ty.setValue(30.0)
        widget.spin_angle.setValue(10.0)
        widget.spin_scale.setValue(1.2)

        # Mock da MessageBox
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.Yes):
            widget._on_reset()

            # Verifica que voltou ao estado inicial
            assert widget._state.tx == 0.0
            assert widget._state.ty == 0.0
            assert widget._state.angle == 0.0
            assert widget._state.scale == 1.0

    def test_reset_cancelled(self, widget, sample_mosaic):
        """Testa cancelamento do reset."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        # Modifica valores
        widget.spin_tx.setValue(50.0)

        # Mock da MessageBox (usuário clica Não)
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=QMessageBox.StandardButton.No):
            widget._on_reset()

            # Verifica que NÃO voltou ao estado inicial
            assert widget._state.tx == 50.0


# ===========================================================================
#  TESTES DE VALIDAÇÃO
# ===========================================================================

@pytest.mark.slow
class TestAlignmentWidgetValidation:
    """Testes de validação."""

    def test_not_valid_without_fiducials(self, widget, sample_mosaic):
        """Testa que não é válido sem fiduciais encontrados."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        # Score baixo
        widget._state.score = 50.0
        widget._state.fiducials_found = False

        assert not widget.is_valid()

    def test_valid_with_good_score(self, widget, sample_mosaic):
        """Testa que é válido com score >= 70%."""
        from consumo_lib.models.alignment_state import FiducialMatch

        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        # Cria match com score alto para ser válido
        match = FiducialMatch(
            template_id=1,
            found=True,
            x=100.0,
            y=100.0,
            score=75.0,  # >= 70%
            expected_x=100.0,
            expected_y=100.0
        )

        # Atualiza matches para recalcular métricas
        widget._state.update_matches([match])

        # is_valid é calculado automaticamente
        assert widget._state.is_valid

    def test_valid_with_fiducials_found(self, widget, sample_mosaic):
        """Testa que é válido quando fiduciais foram encontrados."""
        from consumo_lib.models.alignment_state import FiducialMatch

        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        # Cria 2 fiduciais encontrados (mesmo com score baixo individual)
        match1 = FiducialMatch(
            template_id=1,
            found=True,
            x=100.0,
            y=100.0,
            score=50.0,  # score baixo
            expected_x=100.0,
            expected_y=100.0
        )
        match2 = FiducialMatch(
            template_id=2,
            found=True,
            x=200.0,
            y=100.0,
            score=60.0,  # score baixo
            expected_x=200.0,
            expected_y=100.0
        )

        # Atualiza matches - média = 55.0, mas is_acceptable = True
        # pois há 2 fiduciais e min_required = 1 para 2 templates
        widget._state.update_matches([match1, match2])

        # Com 2 fiduciais encontrados, score médio é 55, mas is_acceptable é True
        # pois min_required = 1 para 2 templates (veja AlignmentMetrics.from_matches)
        assert widget._state.fiducials_found is True
        # Nota: is_valid depende de score >= 70 E fiducials_found >= min_required
        # Como score médio é 55 (<70), is_valid deve ser False
        assert widget._state.is_valid is False

    def test_validation_signal_emitted(self, widget, sample_mosaic):
        """Testa que sinal de validação é emitido."""
        from consumo_lib.models.alignment_state import FiducialMatch

        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        with patch.object(widget, 'validationChanged') as mock_signal:
            # Cria match com score alto para ser válido
            match = FiducialMatch(
                template_id=1,
                found=True,
                x=100.0,
                y=100.0,
                score=80.0,  # >= 70%
                expected_x=100.0,
                expected_y=100.0
            )

            # Atualiza matches para recalcular métricas e is_valid
            widget._state.update_matches([match])

            # Chama _update_validation para emitir sinal
            widget._update_validation()

            assert mock_signal.emit.called
            args = mock_signal.emit.call_args[0]
            assert args[0] is True  # Válido (score >= 70)


# ===========================================================================
#  TESTES DE APLICAÇÃO
# ===========================================================================

@pytest.mark.slow
class TestAlignmentWidgetApplication:
    """Testes de aplicação do alinhamento."""

    def test_get_alignment_data(self, widget, sample_mosaic):
        """Testa obtenção de dados de alinhamento."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        # Modifica estado
        widget._state.tx = 10.0
        widget._state.ty = -5.0
        widget._state.angle = 2.5
        widget._state.scale = 1.05
        widget._state.score = 85.0
        widget._state.fiducials_found = True

        data = widget.get_alignment_data()

        assert 'transform' in data
        assert data['transform']['tx'] == 10.0
        assert data['transform']['ty'] == -5.0
        assert data['transform']['angle'] == 2.5
        assert data['transform']['scale'] == 1.05
        assert data['score'] == 85.0
        assert data['fiducials_found'] is True

    def test_apply_with_valid_alignment(self, widget, sample_mosaic):
        """Testa aplicação de alinhamento válido."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        widget._state.score = 85.0

        with patch.object(widget, 'alignmentApplied') as mock_signal:
            with patch('PyQt6.QtWidgets.QMessageBox.information'):
                widget._on_apply()

                assert mock_signal.emit.called

    def test_apply_with_invalid_alignment_shows_warning(
        self, widget, sample_mosaic
    ):
        """Testa que aviso é mostrado com alinhamento inválido."""
        widget.load_data(
            mosaic_image=sample_mosaic,
            gerber_data={},
            fiducial_templates=[]
        )

        widget._state.score = 50.0

        with patch('PyQt6.QtWidgets.QMessageBox.question') as mock_question:
            with patch('PyQt6.QtWidgets.QMessageBox.information'):
                with patch.object(widget, 'alignmentApplied') as mock_signal:
                    mock_question.return_value = QMessageBox.StandardButton.No

                    widget._on_apply()

                    # Verifica que pergunta foi mostrada
                    assert mock_question.called
                    # Verifica que NÃO aplicou (usuário cancelou)
                    assert not mock_signal.emit.called


# ===========================================================================
#  TESTES DE VISUALIZAÇÃO
# ===========================================================================

@pytest.mark.slow
class TestAlignmentImageView:
    """Testes do widget de visualização."""

    @pytest.fixture
    def image_view(self, qapp):
        """Cria instância da view."""
        view = AlignmentImageView()
        yield view
        view.deleteLater()

    def test_set_mosaic(self, image_view, sample_mosaic):
        """Testa definição do mosaico."""
        image_view.set_mosaic(sample_mosaic)

        assert image_view._image is not None
        assert image_view._pixmap is not None

    def test_fit_in_view(self, image_view, sample_mosaic):
        """Testa ajuste à janela."""
        image_view.set_mosaic(sample_mosaic)
        image_view.fit_in_view()

        assert image_view._zoom > 0
        assert image_view._zoom <= 1.0

    def test_set_zoom(self, image_view, sample_mosaic):
        """Testa definição de zoom."""
        image_view.set_mosaic(sample_mosaic)
        image_view.set_zoom(2.0)

        assert image_view._zoom == 2.0

    def test_set_gerber_transform(self, image_view):
        """Testa definição de transformação do Gerber."""
        image_view.set_gerber_transform(
            offset_x=10.0,
            offset_y=-5.0,
            scale=1.2,
            angle=5.0,
            opacity=0.75
        )

        assert image_view._gerber_offset.x() == 10.0
        assert image_view._gerber_offset.y() == -5.0
        assert image_view._gerber_scale == 1.2
        assert image_view._gerber_angle == 5.0
        assert image_view._gerber_opacity == 0.75

    def test_zoom_range(self, image_view, sample_mosaic):
        """Testa limites de zoom."""
        image_view.set_mosaic(sample_mosaic)

        # Limite inferior
        image_view.set_zoom(0.01)
        assert image_view._zoom == 0.1

        # Limite superior
        image_view.set_zoom(10.0)
        assert image_view._zoom == 5.0


# ===========================================================================
#  TESTES DE ESTADO
# ===========================================================================

@pytest.mark.slow
class TestAlignmentState:
    """Testes do dataclass AlignmentState."""

    def test_default_values(self):
        """Testa valores padrão."""
        state = AlignmentState()

        assert state.tx == 0.0
        assert state.ty == 0.0
        assert state.angle == 0.0
        assert state.scale == 1.0
        assert state.opacity == 0.5
        assert state.score == 0.0
        assert state.fiducials_found is False

    def test_custom_values(self):
        """Testa valores customizados."""
        state = AlignmentState(
            tx=10.0,
            ty=-5.0,
            angle=2.5,
            scale=1.1,
            opacity=0.75,
            score=85.0,
            fiducials_found=True
        )

        assert state.tx == 10.0
        assert state.ty == -5.0
        assert state.angle == 2.5
        assert state.scale == 1.1
        assert state.opacity == 0.75
        assert state.score == 85.0
        assert state.fiducials_found is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
