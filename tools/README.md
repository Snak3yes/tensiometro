# Development Tools

This directory contains standalone utility scripts for development, calibration, and testing.

## Scripts

### camera_calibration.py
**Purpose:** Camera FOV (Field of View) calibration utility
**Usage:** `python tools/camera_calibration.py`
**Description:**
- Interactive calibration tool for camera pixel-to-millimeter conversion
- Captures calibration images using checkerboard pattern
- Generates `config/camera_calibration.json` with FOV data
- Required for accurate click-to-move functionality

### mosaic_builder.py
**Purpose:** Image stitching tool for creating composite mosaics
**Usage:** `python tools/mosaic_builder.py`
**Description:**
- Combines multiple images into single mosaic
- Uses multiband blending for seamless transitions
- Reads configuration from `config/map_programs/`
- Outputs high-resolution composite images

### Leitura_Continua.py
**Purpose:** Continuous tensiometer serial reader (standalone)
**Usage:** `python tools/Leitura_Continua.py [COM_PORT]`
**Description:**
- Standalone tool for testing AS-120N tensiometer connectivity
- Reads tension values via RS-232 serial protocol
- Useful for hardware validation without full GUI
- Default COM port: auto-detect or specify as argument

## Subdirectories

### tension/
**Purpose:** Tension measurement configuration files
**Contains:** JSON files with grid patterns for tension testing
**Example:** `padrão 3x3.json` - 3x3 grid configuration

## Running Tools

From project root:
```bash
# Camera calibration
python tools/camera_calibration.py

# Mosaic builder
python tools/mosaic_builder.py

# Tensiometer reader (with specific COM port)
python tools/Leitura_Continua.py COM3
```

From tools/ directory:
```bash
cd tools/
python camera_calibration.py
python mosaic_builder.py
python Leitura_Continua.py
```

## Adding New Tools

When adding new utility scripts:
1. Place in `tools/` directory
2. Add descriptive comment at top with purpose/usage
3. Update this README with script information
4. Follow naming convention: `lowercase_with_underscores.py`

## Notes

- All tools are standalone scripts (not part of main application)
- Tools may have additional dependencies not in main requirements.txt
- Test/debug tools go here, production code goes in `aoi_lib/` or `consumo_lib/`
