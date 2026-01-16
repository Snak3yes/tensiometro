"""
Unit tests for ConfirmSaveWidget.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from consumo_lib.models.engineering.program_config import (
    ProgramConfig,
    FiducialConfig,
    MosaicConfig,
    AlignmentConfig,
    InspectionGroupConfig,
)
from consumo_lib.widgets.engenharia.confirm_save_widget import (
    ConfirmSaveWidget,
    SummaryCard,
    WarningPanel,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def qapp():
    """
    Fixture para QApplication (session scope).

    MARKED AS SLOW: Criar QApplication é uma operação cara em termos de performance.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def app(qapp):
    """Fixture para QApplication (test scope)."""
    return qapp


@pytest.fixture
def valid_program_config():
    """Fixture com ProgramConfig válido."""
    return ProgramConfig(
        # Aba 1: Dados do Programa
        stencil_code="STENCIL-TEST-001",
        program_name="Inspeção Teste Padrão",
        description="Programa de teste para validação",
        version="v1.0",
        recipe_name="Receita Padrão 0.5mm",
        created_by="test_user",
        # Aba 2: Gerber
        gerber_file="test_files/stencil_test.gbr",
        gerber_dimensions={"width": 400.0, "height": 300.0},
        aperture_count=245,
        detected_fiducials=2,
        # Aba 3: Fiduciais
        fiducials=FiducialConfig(
            fiducial1={"x": 15.2, "y": 20.3},
            fiducial2={"x": 180.5, "y": 20.3},
            template1_path="data/templates/fid1.png",
            template2_path="data/templates/fid2.png",
        ),
        # Aba 4: Mosaico
        mosaic=MosaicConfig(
            corner1={"x": 0.0, "y": 0.0},
            corner2={"x": 400.0, "y": 300.0},
            grid_rows=4,
            grid_cols=4,
            total_fovs=16,
            capture_delay_ms=200,
        ),
        # Aba 5: Alinhamento
        alignment=AlignmentConfig(
            translation_x=1.2,
            translation_y=-0.5,
            rotation=0.3,
            scale=1.01,
            alignment_score=85.5,
        ),
        # Aba 6: Janelas de Inspeção
        inspection_groups=[
            InspectionGroupConfig(
                name="0.5mm Círculo",
                aperture_count=145,
                ok_threshold=90.0,
                partial_threshold=70.0,
                binarization_method="otsu",
                pre_processing="blur",
                confirmed=True,
            ),
            InspectionGroupConfig(
                name="0.8mm Círculo",
                aperture_count=82,
                ok_threshold=90.0,
                partial_threshold=70.0,
                binarization_method="otsu",
                pre_processing="blur",
                confirmed=True,
            ),
            InspectionGroupConfig(
                name="1.2mm Quadrado",
                aperture_count=18,
                ok_threshold=85.0,
                partial_threshold=65.0,
                binarization_method="adaptive",
                pre_processing="denoise",
                confirmed=False,
            ),
        ],
        total_apertures=245,
    )


@pytest.fixture
def invalid_program_config():
    """Fixture com ProgramConfig inválido (dados faltando)."""
    return ProgramConfig(
        stencil_code="",  # Vazio - inválido
        program_name="",  # Vazio - inválido
        gerber_file=None,  # None - inválido
        aperture_count=0,  # Zero - inválido
    )


@pytest.fixture
def widget(app):
    """Fixture com ConfirmSaveWidget."""
    return ConfirmSaveWidget()


# =============================================================================
# TESTS: ProgramConfig
# =============================================================================

class TestProgramConfig:
    """Testes para o modelo ProgramConfig."""

    def test_initialization(self, valid_program_config):
        """Testa inicialização do ProgramConfig."""
        config = valid_program_config

        assert config.stencil_code == "STENCIL-TEST-001"
        assert config.program_name == "Inspeção Teste Padrão"
        assert config.version == "v1.0"
        assert config.aperture_count == 245
        assert len(config.inspection_groups) == 3
        assert config.total_apertures == 245
        assert config.configured_groups == 3
        assert config.confirmed_groups == 2  # 2 grupos confirmados

    def test_to_dict(self, valid_program_config):
        """Testa conversão para dicionário."""
        data = valid_program_config.to_dict()

        assert isinstance(data, dict)
        assert data["stencil_code"] == "STENCIL-TEST-001"
        assert data["program_name"] == "Inspeção Teste Padrão"
        assert "fiducials" in data
        assert "mosaic" in data
        assert "alignment" in data
        assert "inspection_groups" in data

    def test_from_dict(self, valid_program_config):
        """Testa criação a partir de dicionário."""
        data = valid_program_config.to_dict()
        config2 = ProgramConfig.from_dict(data)

        assert config2.stencil_code == valid_program_config.stencil_code
        assert config2.program_name == valid_program_config.program_name
        assert config2.aperture_count == valid_program_config.aperture_count

    def test_to_json(self, valid_program_config):
        """Testa conversão para JSON."""
        json_str = valid_program_config.to_json()

        assert isinstance(json_str, str)
        # Verifica que é JSON válido
        data = json.loads(json_str)
        assert data["stencil_code"] == "STENCIL-TEST-001"

    def test_from_json(self, valid_program_config):
        """Testa criação a partir de JSON."""
        json_str = valid_program_config.to_json()
        config2 = ProgramConfig.from_json(json_str)

        assert config2.stencil_code == valid_program_config.stencil_code
        assert config2.program_name == valid_program_config.program_name

    def test_validate_valid_config(self, valid_program_config):
        """Testa validação de configuração válida."""
        is_valid, errors = valid_program_config.validate()

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_config(self, invalid_program_config):
        """Testa validação de configuração inválida."""
        is_valid, errors = invalid_program_config.validate()

        assert is_valid is False
        assert len(errors) > 0
        # Verifica que erros específicos estão presentes
        error_messages = " ".join(errors)
        assert "stencil" in error_messages.lower()
        assert "programa" in error_messages.lower()

    def test_get_estimated_execution_time(self, valid_program_config):
        """Testa estimativa de tempo de execução."""
        estimates = valid_program_config.get_estimated_execution_time()

        assert "total_seconds" in estimates
        assert "total_minutes" in estimates
        assert "fov_capture_time" in estimates
        assert estimates["total_minutes"] > 0

    def test_get_summary(self, valid_program_config):
        """Testa geração de resumo."""
        summary = valid_program_config.get_summary()

        assert summary["stencil_code"] == "STENCIL-TEST-001"
        assert summary["program_name"] == "Inspeção Teste Padrão"
        assert summary["is_valid"] is True
        assert len(summary["errors"]) == 0
        assert "execution_time" in summary

    def test_get_file_path(self, valid_program_config, tmp_path):
        """Testa geração de caminho de arquivo."""
        filepath = valid_program_config.get_file_path()

        assert "inspection_programs" in filepath
        assert "STENCIL-TEST-001" in filepath
        assert "Inspeção_Teste_Padrão" in filepath
        assert filepath.endswith(".json")

    def test_save_and_load_file(self, valid_program_config, tmp_path):
        """Testa salvamento e carregamento de arquivo."""
        # Salva em arquivo temporário
        filepath = tmp_path / "test_program.json"
        valid_program_config.save_to_file(str(filepath))

        # Verifica que arquivo existe
        assert filepath.exists()

        # Carrega arquivo
        config2 = ProgramConfig.from_file(str(filepath))

        # Verifica que dados são iguais
        assert config2.stencil_code == valid_program_config.stencil_code
        assert config2.program_name == valid_program_config.program_name
        assert config2.aperture_count == valid_program_config.aperture_count


# =============================================================================
# TESTS: FiducialConfig
# =============================================================================

class TestFiducialConfig:
    """Testes para FiducialConfig."""

    def test_default_values(self):
        """Testa valores padrão."""
        config = FiducialConfig()

        assert config.fiducial1 == {"x": 0.0, "y": 0.0}
        assert config.fiducial2 == {"x": 0.0, "y": 0.0}
        assert config.template1_path is None
        assert config.template2_path is None

    def test_to_dict(self):
        """Testa conversão para dicionário."""
        config = FiducialConfig(
            fiducial1={"x": 10.0, "y": 20.0},
            fiducial2={"x": 30.0, "y": 40.0},
        )
        data = config.to_dict()

        assert data["fiducial1"]["x"] == 10.0
        assert data["fiducial1"]["y"] == 20.0

    def test_from_dict(self):
        """Testa criação a partir de dicionário."""
        data = {
            "fiducial1": {"x": 10.0, "y": 20.0},
            "fiducial2": {"x": 30.0, "y": 40.0},
        }
        config = FiducialConfig.from_dict(data)

        assert config.fiducial1["x"] == 10.0
        assert config.fiducial2["x"] == 30.0


# =============================================================================
# TESTS: MosaicConfig
# =============================================================================

class TestMosaicConfig:
    """Testes para MosaicConfig."""

    def test_default_values(self):
        """Testa valores padrão."""
        config = MosaicConfig()

        assert config.grid_rows == 4
        assert config.grid_cols == 4
        assert config.total_fovs == 16
        assert config.capture_delay_ms == 200


# =============================================================================
# TESTS: AlignmentConfig
# =============================================================================

class TestAlignmentConfig:
    """Testes para AlignmentConfig."""

    def test_default_values(self):
        """Testa valores padrão."""
        config = AlignmentConfig()

        assert config.translation_x == 0.0
        assert config.translation_y == 0.0
        assert config.rotation == 0.0
        assert config.scale == 1.0
        assert config.alignment_score == 0.0


# =============================================================================
# TESTS: InspectionGroupConfig
# =============================================================================

class TestInspectionGroupConfig:
    """Testes para InspectionGroupConfig."""

    def test_default_values(self):
        """Testa valores padrão."""
        config = InspectionGroupConfig(name="Teste", aperture_count=10)

        assert config.name == "Teste"
        assert config.aperture_count == 10
        assert config.ok_threshold == 90.0
        assert config.partial_threshold == 70.0
        assert config.binarization_method == "otsu"
        assert config.confirmed is False


# =============================================================================
# TESTES: SummaryCard
# =============================================================================

@pytest.mark.slow
class TestSummaryCard:
    """Testes para SummaryCard."""

    def test_initialization(self, app):
        """Testa inicialização."""
        card = SummaryCard("Test Card")

        assert card.title() == "Test Card"

    def test_set_content(self, app):
        """Testa definição de conteúdo texto."""
        card = SummaryCard("Test Card")

        card.set_content("Test content")
        assert card.content_label.text() == "Test content"

    def test_set_html(self, app):
        """Testa definição de conteúdo HTML."""
        card = SummaryCard("Test Card")

        html = "<b>Bold</b> and <i>italic</i>"
        card.set_html(html)
        assert card.content_label.text() == html


# =============================================================================
# TESTES: WarningPanel
# =============================================================================

@pytest.mark.slow
class TestWarningPanel:
    """Testes para WarningPanel."""

    def test_initialization(self, app):
        """Testa inicialização."""
        panel = WarningPanel()

        assert panel.warnings == []

    def test_set_warnings_empty(self, app):
        """Testa definição de lista vazia de avisos."""
        panel = WarningPanel()

        panel.set_warnings([])
        # Verifica que mensagem de sucesso é exibida
        # Check for success indicators (green background, checkmark)
        text = panel.label.text()
        assert "#E8F5E9" in text  # Green background color
        assert "Nenhum" in text or "Programa" in text  # Text content

    def test_set_warnings_with_errors(self, app):
        """Testa definição de avisos."""
        panel = WarningPanel()

        warnings = ["Erro 1", "Erro 2", "Erro 3"]
        panel.set_warnings(warnings)

        assert "Erro 1" in panel.label.text()
        assert "Erro 2" in panel.label.text()
        assert "Erro 3" in panel.label.text()


# =============================================================================
# TESTES: ConfirmSaveWidget
# =============================================================================

class TestConfirmSaveWidget:
    """Testes para ConfirmSaveWidget."""

    def test_initialization(self, widget):
        """Testa inicialização do widget."""
        assert widget.program_config is None
        assert widget.is_base_program is False
        assert widget.save_button.isEnabled() is False  # Sem config, desabilitado

    def test_set_program_config(self, widget, valid_program_config):
        """Testa definição de configuração do programa."""
        widget.set_program_config(valid_program_config)

        assert widget.program_config is not None
        assert widget.program_config.stencil_code == "STENCIL-TEST-001"
        # Config válido, botão deve estar habilitado
        assert widget.save_button.isEnabled() is True

    def test_set_invalid_program_config(self, widget, invalid_program_config):
        """Testa definição de configuração inválida."""
        widget.set_program_config(invalid_program_config)

        assert widget.program_config is not None
        # Config inválido, botão deve estar desabilitado
        assert widget.save_button.isEnabled() is False

    def test_signals(self, widget, valid_program_config):
        """Testa emissão de sinais."""
        widget.set_program_config(valid_program_config)

        # Captura sinais
        save_signals = []
        test_signals = []
        back_signals = []

        widget.save_requested.connect(lambda c: save_signals.append(c))
        widget.test_requested.connect(lambda c: test_signals.append(c))
        widget.back_requested.connect(lambda: back_signals.append(True))

        # Testa sinal de voltar
        widget.back_button.click()
        assert len(back_signals) == 1

    def test_base_program_toggle(self, widget, valid_program_config):
        """Testa checkbox de programa base."""
        widget.set_program_config(valid_program_config)

        # Inicialmente não marcado
        assert widget.is_base_program is False
        assert "STENCIL-TEST-001" in widget.stencil_code_edit.text()

        # Marca checkbox
        widget.base_program_checkbox.setChecked(True)
        assert widget.is_base_program is True
        assert "N/A" in widget.stencil_code_edit.text()

    def test_get_program_config(self, widget, valid_program_config):
        """Testa recuperação de configuração."""
        assert widget.get_program_config() is None

        widget.set_program_config(valid_program_config)
        assert widget.get_program_config() is not None
        assert widget.get_program_config().stencil_code == "STENCIL-TEST-001"

    def test_is_ready_to_save(self, widget, valid_program_config, invalid_program_config):
        """Testa verificação de prontidão para salvar."""
        # Sem config
        assert widget.is_ready_to_save() is False

        # Config inválido
        widget.set_program_config(invalid_program_config)
        assert widget.is_ready_to_save() is False

        # Config válido
        widget.set_program_config(valid_program_config)
        assert widget.is_ready_to_save() is True
