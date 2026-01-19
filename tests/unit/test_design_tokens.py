"""
Testes unitários para Design Tokens

Valida se todos os tokens de design estão corretamente definidos.
"""

import pytest
from consumo_lib.ui.design_tokens import COLORS, TYPO, ColorPalette


class TestColorPalette:
    """Testes para ColorPalette"""

    def test_primary_colors_defined(self):
        """Verifica se cores primárias estão definidas"""
        assert COLORS.PRIMARY == "#4CAF50"
        assert COLORS.PRIMARY_DARK == "#388E3C"
        assert COLORS.PRIMARY_LIGHT == "#81C784"
        assert COLORS.ON_PRIMARY == "#FFFFFF"

    def test_secondary_colors_defined(self):
        """Verifica se cores secundárias estão definidas"""
        assert COLORS.SECONDARY == "#2196F3"
        assert COLORS.SECONDARY_DARK == "#1976D2"
        assert COLORS.SECONDARY_LIGHT == "#64B5F6"

    def test_semantic_colors_defined(self):
        """Verifica se cores semânticas estão definidas"""
        assert COLORS.SUCCESS == "#2ecc71"
        assert COLORS.WARNING == "#f1c40f"
        assert COLORS.ERROR == "#e74c3c"

    def test_status_colors_defined(self):
        """Verifica se cores de status estão definidas"""
        assert COLORS.STATUS_APPROVED_AUTO == "#4CAF50"
        assert COLORS.STATUS_APPROVED_USER == "#CDDC39"
        assert COLORS.STATUS_REJECTED == "#F44336"
        assert COLORS.STATUS_PENDING == "#9E9E9E"
        assert COLORS.STATUS_IN_PROGRESS == "#2196F3"

    def test_neutral_colors_defined(self):
        """Verifica se cores neutras estão definidas"""
        assert COLORS.TEXT_PRIMARY == "#212121"
        assert COLORS.TEXT_SECONDARY == "#757575"
        assert COLORS.BACKGROUND == "#FFFFFF"
        assert COLORS.SURFACE == "#F5F5F5"

    def test_engineering_colors_defined(self):
        """Verifica se cores de engenharia estão definidas"""
        assert COLORS.OVERLAY_IMAGE == "#1e1e1e"
        assert COLORS.FIDUCIAL_FOUND == "#00ff00"
        assert COLORS.FIDUCIAL_NOT_FOUND == "#ff0000"

    def test_to_qcolor_valid(self):
        """Verifica conversão de HEX para QColor"""
        color = COLORS.to_qcolor(COLORS.PRIMARY)
        assert color.isValid() is True
        assert color.name() == "#4caf50"  # Qt converte para lowercase

    def test_to_qcolor_invalid_format(self):
        """Verifica se formato inválido lança exceção"""
        with pytest.raises(ValueError):
            COLORS.to_qcolor("4CAF50")  # Missing #

        with pytest.raises(ValueError):
            COLORS.to_qcolor("#ZZZZZZ")  # Invalid HEX

    def test_get_status_color_valid(self):
        """Verifica obtenção de cor por status"""
        assert COLORS.get_status_color("approved_auto") == "#4CAF50"
        assert COLORS.get_status_color("rejected") == "#F44336"
        assert COLORS.get_status_color("pending") == "#9E9E9E"

    def test_get_status_color_invalid(self):
        """Verifica se status inválido lança exceção"""
        with pytest.raises(ValueError):
            COLORS.get_status_color("invalid_status")

    def test_all_colors_have_hash_prefix(self):
        """Verifica se todas as cores começam com #"""
        # Listar todos os atributos que começam com letras maiúsculas (constantes)
        color_attrs = [
            attr for attr in dir(COLORS)
            if attr.isupper() and not attr.startswith("_")
        ]

        for attr in color_attrs:
            value = getattr(COLORS, attr)
            if isinstance(value, str) and not attr.startswith("ON_"):
                assert value.startswith("#"), f"{attr} não começa com #: {value}"


class TestTypography:
    """Testes para Typography"""

    def test_font_families_defined(self):
        """Verifica se font families estão definidas"""
        assert TYPO.FONT_FAMILY == "Arial"
        assert TYPO.FONT_FAMILY_MONOSPACE == "Consolas"

    def test_type_scale_defined(self):
        """Verifica se type scale está definido"""
        assert TYPO.DISPLAY_LARGE == 57
        assert TYPO.DISPLAY_MEDIUM == 45
        assert TYPO.DISPLAY_SMALL == 36

        assert TYPO.HEADLINE_LARGE == 32
        assert TYPO.HEADLINE_MEDIUM == 28
        assert TYPO.HEADLINE_SMALL == 24

        assert TYPO.TITLE_LARGE == 22
        assert TYPO.TITLE_MEDIUM == 16
        assert TYPO.TITLE_SMALL == 14

        assert TYPO.BODY_LARGE == 16
        assert TYPO.BODY_MEDIUM == 14
        assert TYPO.BODY_SMALL == 12

        assert TYPO.LABEL_LARGE == 14
        assert TYPO.LABEL_MEDIUM == 12
        assert TYPO.LABEL_SMALL == 11

    def test_get_font_basic(self):
        """Verifica criação básica de fonte"""
        font = TYPO.get_font(14)
        assert font.family() == "Arial"
        assert font.pointSize() == 14
        assert font.bold() is False
        assert font.italic() is False

    def test_get_font_bold(self):
        """Verifica criação de fonte com negrito"""
        font = TYPO.get_font(14, bold=True)
        assert font.bold() is True
        assert font.pointSize() == 14

    def test_get_font_italic(self):
        """Verifica criação de fonte com itálico"""
        font = TYPO.get_font(14, italic=True)
        assert font.italic() is True
        assert font.pointSize() == 14

    def test_get_font_bold_italic(self):
        """Verifica criação de fonte com negrito e itálico"""
        font = TYPO.get_font(14, bold=True, italic=True)
        assert font.bold() is True
        assert font.italic() is True

    def test_convenience_methods(self):
        """Verifica métodos convenience"""
        # Display methods
        font = TYPO.display_large()
        assert font.pointSize() == 57
        assert font.bold() is True

        # Headline methods
        font = TYPO.headline_medium()
        assert font.pointSize() == 28
        assert font.bold() is True

        # Title methods
        font = TYPO.title_medium()
        assert font.pointSize() == 16
        assert font.bold() is True

        # Body methods
        font = TYPO.body_medium()
        assert font.pointSize() == 14
        assert font.bold() is False

        # Label methods
        font = TYPO.label_small()
        assert font.pointSize() == 11
        assert font.bold() is False
