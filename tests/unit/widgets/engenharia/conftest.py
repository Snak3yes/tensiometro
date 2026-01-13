"""
Pytest configuration and fixtures for engineering widgets tests.
"""

import pytest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def qapp():
    """Fixture para QApplication (session scope)."""
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def temp_library_path(tmp_path):
    """Create temporary path for library files."""
    return tmp_path / "test_library.json"
