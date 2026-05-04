from dataclasses import dataclass

import pytest
from PyQt6.QtWidgets import QApplication

from consumo_lib.tabs.tension_measurement_tab import TensionMeasurementTab


@pytest.fixture
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


@dataclass
class _FakeStencil:
    code: str = "STENCIL-001"
    description: str = "Stencil teste"
    status: str = "active"
    last_inspection: str = "2026-05-04T10:00:00"
    recipe_name: str = "Padrao"
    inspection_count: int = 1
    created_at: str = "2026-05-04T09:00:00"
    notes: str = ""


@dataclass
class _FakeTensionRecord:
    result: str
    average_tension: float = 20.0
    timestamp: str = "2026-05-04T10:00:00"


class _FakeStencilManager:
    def __init__(self, record):
        self._record = record

    def list_stencils(self):
        return [_FakeStencil(status="active")]

    def get_tension_history(self, code, limit=50):
        del code, limit
        return [self._record]


def test_selected_stencil_status_uses_latest_measurement_result(app):
    manager = _FakeStencilManager(_FakeTensionRecord(result="NOK"))
    tab = TensionMeasurementTab(stencil_manager=manager)

    try:
        stencil = tab.current_stencils[0]
        tab.show_details(stencil)

        assert stencil["status"] == "active"
        assert stencil["latest_result"] == "NOK"
        assert tab.field_status_badge.text() == "Reprovado"
    finally:
        tab.close()


def test_tree_status_badge_uses_latest_measurement_result(app):
    manager = _FakeStencilManager(_FakeTensionRecord(result="OK", average_tension=32.0))
    tab = TensionMeasurementTab(stencil_manager=manager)

    try:
        item = tab.tree_widget.topLevelItem(0)
        badge = tab.tree_widget.itemWidget(item, 2)

        assert badge.text() == "Aprovado"
    finally:
        tab.close()
