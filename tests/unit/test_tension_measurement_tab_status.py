from dataclasses import dataclass

import pytest
from PyQt6.QtWidgets import QApplication

from consumo_lib.managers.tension_criteria_manager import TensionCriteriaConfig
from consumo_lib.tabs.tension_measurement_tab import TensionMeasurementTab
from consumo_lib.ui import COLORS
from consumo_lib.widgets.mini_tension_heatmap import MiniTensionHeatmapWidget
from aoi_lib.recipe_manager import TensionAcceptance


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
    measurements: tuple = ()

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "result": self.result,
            "average_tension": self.average_tension,
            "measurements": list(self.measurements),
            "parameters": {},
        }


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


def test_latest_measurement_summary_uses_saved_point_statuses(app):
    record = _FakeTensionRecord(
        result="OK",
        average_tension=46.5,
        measurements=(
            {"x": 0, "y": 0, "tension": 46.0, "status": "OK"},
            {"x": 1, "y": 0, "tension": 47.0, "status": "OK"},
        ),
    )
    manager = _FakeStencilManager(record)
    tab = TensionMeasurementTab(stencil_manager=manager)

    try:
        tab._load_latest_measurement_for_stencil(tab.current_stencils[0])

        assert tab.stats_counts_label.text().startswith("OK: 2")
        assert tab.result_badge.text() == "APROVADO"
    finally:
        tab.close()


def test_measurement_summary_classifies_above_warning_high_as_approved(app):
    tab = TensionMeasurementTab(stencil_manager=None)

    try:
        tab.update_criteria(
            TensionCriteriaConfig(
                min_tension=30.0,
                max_tension=50.0,
                warning_low=30.0,
                warning_high=34.0,
            )
        )
        tab.measurements_data = {
            "measurements": [
                {"x": 0, "y": 0, "tension": 40.0},
                {"x": 1, "y": 0, "tension": 49.0},
            ],
            "parameters": {},
        }

        tab.update_statistics()

        assert tab.stats_counts_label.text().startswith("OK: 2")
        assert tab.result_badge.text() == "APROVADO"
    finally:
        tab.close()


def test_heatmap_color_uses_saved_point_status(app):
    widget = MiniTensionHeatmapWidget()

    try:
        widget.set_acceptance_criteria(
            TensionAcceptance(min_tension=30.0, max_tension=45.0, warning_high=34.0)
        )

        assert widget._get_tension_color(47.0, {"status": "OK"}) == COLORS.to_qcolor(COLORS.SUCCESS)
    finally:
        widget.close()
