# Test Scripts

This directory contains scripts for running and managing tests.

## Scripts

### run_tests.bat
**Purpose:** Main test runner script for Windows
**Usage:**
```bash
# From project root (wrapper):
run_tests.bat

# Or directly:
tests\scripts\run_tests.bat

# With options:
run_tests.bat --fast           # Skip slow/hardware tests
run_tests.bat --unit           # Unit tests only
run_tests.bat --integration    # Integration tests only
run_tests.bat --no-cov         # Disable coverage
run_tests.bat --html           # Open coverage in browser
run_tests.bat -h               # Show help
```

**Features:**
- Automatic virtual environment activation
- Configurable markers (unit, integration, slow, hardware)
- HTML coverage report generation
- Optional browser auto-open
- Verbose output with colored results

### run_tests.sh
**Purpose:** Main test runner script for Unix/Linux/macOS (TODO)
**Status:** Placeholder for future implementation
**Note:** Currently delegates to run_tests.bat via wrapper

## Running Tests

### Quick Start
```bash
# Windows
run_tests.bat

# Linux/macOS (TODO)
./run_tests.sh
```

### With Coverage
```bash
# Run with coverage (default)
run_tests.bat

# Generate HTML report
run_tests.bat --html

# Open report automatically
run_tests.bat --html
# Then: start htmlcov/index.html (Windows)
# Or: xdg-open htmlcov/index.html (Linux)
```

### Test Categories
```bash
# Fast tests only (no hardware, no slow)
run_tests.bat --fast

# Unit tests only
run_tests.bat --unit

# Integration tests only
run_tests.bat --integration
```

### Without Coverage
```bash
run_tests.bat --no-cov
```

## Coverage Reports

Coverage reports are generated in:
- `htmlcov/` - HTML coverage report (browse in browser)
- `coverage.xml` - XML coverage report (for CI/CD)
- Terminal output - Missing lines shown in terminal

**View HTML Report:**
```bash
# Windows
run_tests.bat --html
# Opens browser automatically

# Manual
start htmlcov/index.html
```

## Adding New Test Scripts

When adding new test utilities:
1. Place in `tests/scripts/`
2. Add executable permissions (Unix/Linux): `chmod +x tests/scripts/script.sh`
3. Update this README with usage instructions
4. Create wrapper in root if frequently used

## CI/CD Integration

For CI/CD pipelines:
```bash
# Run tests without browser
run_tests.bat --fast --no-cov

# Generate coverage for CI
pytest --cov=aoi_lib --cov=consumo_lib --cov-report=xml --cov-report=term
```

## Troubleshooting

### Virtual Environment Not Found
```
[ERROR] .venv não encontrado
```
**Solution:** Create virtual environment first:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### Coverage Import Errors
```
ImportError: No module named pytest_cov
```
**Solution:** Install coverage dependencies:
```bash
pip install pytest-cov
```

### Tests Not Found
```
collected 0 items
```
**Solution:** Ensure tests are in `tests/` directory and follow naming:
- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

## Notes

- Scripts in this directory are **not** part of the test suite
- They are utilities for **running** tests
- Actual test code is in `tests/unit/`, `tests/integration/`, etc.
- pytest configuration is in `pytest.ini` (project root)

---

**Last Updated:** 2026-01-08
