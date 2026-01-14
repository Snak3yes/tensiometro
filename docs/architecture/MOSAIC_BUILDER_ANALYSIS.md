# Mosaic Builder Analysis

**Date:** 2026-01-14
**File:** `tools/mosaic_builder.py` (712 lines)
**Status:** KEEP IN `tools/`
**Decision:** Do NOT move to `aoi_lib`

## Overview

The `mosaic_builder.py` module provides image stitching functionality for creating mosaics from grid-captured images.

## Current Structure

### Core Functions (Programmatic API)

- **`compose_mosaic_from_folder()`** - Main entry point
  - Loads tiles from folder pattern: `*_rNNN_cNNN.png`
  - Applies camera calibration corrections (optional)
  - Crops margins to remove lens distortion
  - Stitches images using multiband blending
  - Returns path to generated mosaic

- **`load_tiles()`** - Scans folder for tile images
- **`crop_tile_margins()`** - Removes edge distortions
- Blending functions: Gaussian/Laplacian pyramids for seamless blending

### GUI Components (Standalone Tool)

- **`MosaicBuilder` class** - Complete PyQt6 GUI
  - Folder selection
  - Parameter tuning (delta_x, delta_y, margin, blend_size)
  - Preview with zoom/pan
  - Progress indication

## Usage in Application

### Direct Imports

The application imports from `tools/mosaic_builder.py`:

```python
# consumo_lib/controllers/map_controller.py
from mosaic_builder import compose_mosaic_from_folder

# consumo_lib/handlers/dialog_router.py
from mosaic_builder import MosaicBuilder

# consumo_lib/main_window.py
from mosaic_builder import compose_mosaic_from_folder
```

### Usage Context

1. **Map Generation Workflow** (`map_controller.py`)
   - Generates mosaics from CNC grid captures
   - Used programmatically with progress callbacks

2. **Standalone Tool** (`dialog_router.py`)
   - Opens MosaicBuilder GUI as standalone tool
   - User can generate mosaics manually

3. **Main Application** (`main_window.py`)
   - Quick mosaic generation from existing images

## Evaluation: Move to `aoi_lib`?

### Option 1: Move to `aoi_lib/mosaic.py` ❌ **NOT RECOMMENDED**

**Pros:**
- ✅ Consistent import location (`aoi_lib.*`)
- ✅ Clearer that it's core functionality
- ✅ Easier to discover for new developers

**Cons:**
- ❌ Breaks existing import paths
- ❌ MosaicBuilder GUI has no place in `aoi_lib` (GUI layer)
- ❌ `tools/` directory is for standalone tools (documented in CLAUDE.md)
- ❌ Blending functions are generic computer vision (not AOI-specific)
- ❌ Adds dependency: `aoi_lib` would need PyQt6 for GUI class

### Option 2: Split - Core to `aoi_lib`, GUI stays in `tools/` ⚠️ **POSSIBLE**

**Structure:**
```
aoi_lib/mosaic.py          # Core functions (compose_mosaic_from_folder)
tools/mosaic_builder.py    # GUI that imports from aoi_lib.mosaic
```

**Pros:**
- ✅ Core functionality in `aoi_lib`
- ✅ GUI remains in `tools/`
- ✅ Clean separation

**Cons:**
- ❌ More complex (2 files instead of 1)
- ❌ Circular import risk if GUI needs to call back
- �1 Maintains two files for what is logically one tool
- �1 Extra effort for minimal benefit

### Option 3: Keep in `tools/` ✅ **RECOMMENDED**

**Rationale:**

1. **Project Standards (CLAUDE.md):**
   > "All standalone scripts MUST be in `tools/`"
   - mosaic_builder.py is a standalone tool (can run `python mosaic_builder.py`)
   - Has its own GUI and can be used independently
   - Fits the documented project structure

2. **Separation of Concerns:**
   - `aoi_lib/` is for AOI business logic (inspection, tension, PLC control)
   - `tools/` is for development utilities and standalone tools
   - Mosaic building is general computer vision, not AOI-specific

3. **Current Usage Works:**
   - Application can import from `tools/` when needed
   - No technical reason it must be in `aoi_lib/`
   - Import path is clear: `from mosaic_builder import ...`

4. **Standalone Utility:**
   - Can be used without the rest of the application
   - Has `__main__` block for direct execution
   - Useful for testing/debugging independent of main app

5. **Size and Complexity:**
   - 712 lines (manageable)
   - Self-contained (no complex dependencies)
   - Clear single responsibility: build mosaics

## Current Import Path Validity

### Why It Works

The current import pattern:
```python
from mosaic_builder import compose_mosaic_from_folder
```

Works because:
1. `tools/` directory is in `sys.path` (or application adds it)
2. Python's module resolution finds `mosaic_builder.py` in `tools/`
3. This is a documented pattern in CLAUDE.md

### If We MUST Use `aoi_lib`

Alternative approach (if project standards change):
```python
# In tools/mosaic_builder.py
from aoi_lib.mosaic import compose_mosaic_from_folder

# Keep GUI in tools/, use core from aoi_lib
class MosaicBuilder(QMainWindow):
    def generate_mosaic(self):
        result = compose_mosaic_from_folder(...)
```

But this adds complexity without clear benefit.

## Decision Matrix

| Criterion | Move to aoi_lib | Keep in tools | Winner |
|-----------|----------------|---------------|--------|
| Follows project standards | ❌ No | ✅ Yes | tools/ |
| Clear intent | ✅ Yes | ⚠️ OK (documented) | aoi_lib |
| Maintainability | ⚠️ Same | ✅ Simple | tools/ |
| Breaks existing code | ❌ Yes | ✅ No | tools/ |
| GUI placement | ❌ Problematic | ✅ Natural | tools/ |
| Standalone usability | ⚠️ Reduced | ✅ Full | tools/ |
| AOI domain specificity | ❌ Generic CV | ✅ Generic CV | tools/ |

**Score:** tools/ wins 6-1

## Recommendations

### Short Term (Phase 3)
- ✅ **Keep in `tools/`**
- ✅ Document import pattern in CLAUDE.md if not already there
- ✅ Add docstring example showing programmatic usage

### Long Term (Future Phases)
- Consider creating `aoi_lib/mosaic.py` IF:
  - Mosaic generation becomes core to AOI workflow (currently it's a tool)
  - Multiple parts of `aoi_lib` need to call it
  - Need to version it separately from tools

- Alternative: Create `consumo_lib/services/mosaic_service.py` IF:
  - Want to hide implementation details
  - Need to add business logic around mosaic generation
  - Want consistent import patterns within `consumo_lib/`

## Conclusion

**Mosaic builder should stay in `tools/`**

### Reasons

1. **Follows project structure** (documented in CLAUDE.md)
2. **Standalone tool** with own GUI
3. **Works fine** where it is
4. **Not AOI-specific** (general computer vision)
5. **Breaking change** to move it
6. **No clear benefit** to moving

### Current Import is Valid

```python
# This is OK and follows project standards:
from mosaic_builder import compose_mosaic_from_folder

# If you want to be more explicit:
from tools.mosaic_builder import compose_mosaic_from_folder  # Also works
```

### When to Reconsider

- If `aoi_lib` modules start importing it frequently (coupling concern)
- If mosaic generation becomes tightly coupled to AOI business logic
- If project structure changes (e.g., all imports must be from `aoi_lib` or `consumo_lib`)

**Final Decision: KEEP IN `tools/`**

---

**Analyzed By:** Claude Sonnet 4.5
**Date:** 2026-01-14
**Status:** Approved - No action required
