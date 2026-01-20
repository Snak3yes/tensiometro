# Changelog - Tensiometro

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.1] - 2026-01-20

### Added - Design System v2.0

#### Phase 1: Nomenclatura Decision (Material Design 3)
- Created `DECISION_LOG.md` documenting decision to maintain Material Design 3
- Updated `TYPOGRAPHY_GUIDE.md` from v1.0 (semantic) to v2.0 (MD3)
- Typography scale: 6 levels → 13 levels (DISPLAY_LARGE to LABEL_SMALL)
- **Justification**: Market standard, 13 levels vs 6, time-to-value (1 day vs 3-5 days)

#### Phase 2: Button Variants (5 variants)
- **NEW**: `variant="primary-green"` - Green gradient for confirmation/start actions
- **NEW**: `variant="primary-blue"` - Blue gradient for default/generic actions
- **NEW**: `variant="primary-orange"` - Orange gradient for stop/attention actions
- **UPDATED**: `variant="secondary"` - Changed from solid blue to outline blue (transparent background)
- **RENAMED**: `variant="danger"` → `variant="emergency"` (for physical emergencies)
- **DEPRECATED**: `variant="primary"` (use `primary-green` instead)
- Files updated:
  - `consumo_lib/ui/styles.qss.template` - Added 5 button variants with gradients
  - `consumo_lib/ui/widget_standards.py` - Updated StandardButton with deprecation warnings

#### Phase 3: Font Weights System (5 levels)
- **NEW**: `FontWeight` enum (LIGHT=300, NORMAL=400, MEDIUM=500, SEMIBOLD=600, BOLD=700)
- **UPDATED**: `Typography.get_font()` accepts `weight` parameter with backward compatibility for `bold`
- **NEW**: Convenience methods - `TYPO.light()`, `TYPO.normal()`, `TYPO.medium()`, `TYPO.semibold()`, `TYPO.bold()`
- **DEPRECATED**: `bold=True/False` parameter (will be removed in v0.6.0)
- Usage frequencies:
  - NORMAL (400): 70% - Standard text, labels, instructions
  - MEDIUM (500): 20% - Section titles, buttons, headings
  - SEMIBOLD (600): 4% - Main titles, dialogs
  - BOLD (700): 1% - Emergencies, critical alerts
  - LIGHT (300): 5% - Rarely used
- Files updated:
  - `consumo_lib/ui/design_tokens.py` - Added FontWeight enum, updated get_font(), added convenience methods

#### Phase 4: Small Corrections (Font Family, Sizes)
- **UPDATED**: Font family changed from "Arial" to "Segoe UI" (modern Windows font)
- **NEW**: `BUTTON_SIZE_SM=(80, 32)`, `BUTTON_SIZE_MD=(120, 40)`, `BUTTON_SIZE_LG=(160, 48)`
- **UPDATED**: `StandardButton` accepts `size` parameter ("sm" | "md" | "lg")
- **UPDATED**: `StandardButton` uses `FontWeight.MEDIUM` (500) instead of `bold=True`
- Files updated:
  - `consumo_lib/ui/design_tokens.py` - Updated FONT_FAMILY, added BUTTON_SIZE_* constants
  - `consumo_lib/ui/widget_standards.py` - Added size parameter, uses setMinimumSize(width, height)

#### Phase 5: Documentation Update
- **UPDATED**: `TYPOGRAPHY_GUIDE.md` - Already includes Font Weights section
- **UPDATED**: `BUTTON_GUIDE.md` - Rewritten for v2.0 API (StandardButton, 5 variants, 3 sizes)
- **NEW**: `MIGRATION_GUIDE.md` - Complete migration guide v1.0 → v2.0
  - Botões: StyleManager → StandardButton
  - Font Weights: bold=True/False → FontWeight enum
  - Font Family: Arial → Segoe UI
  - Examples, best practices, FAQ
- **UPDATED**: `CLAUDE.md` - Design System section updated for v2.0
  - Added FontWeight examples
  - Added button variants (primary-green, primary-blue, primary-orange)
  - Added button sizes (sm/md/lg)
  - Updated imports to include FontWeight

### Changed

### Deprecated

### Removed

### Fixed

---

## [0.4.0] - Previous Release

(Previous changelog entries would be here)

---

## Migration Notes

### Design System v1.0 → v2.0

**Breaking Changes:**
- Button variant `primary` renamed to `primary-green`
- Button variant `danger` renamed to `emergency`
- Button variant `secondary` visual changed (solid → outline blue)
- Font family changed from Arial to Segoe UI

**Backward Compatibility:**
- Old button variants still work with deprecation warnings
- `bold=True/False` parameter still works with deprecation warnings
- Will be removed in v0.6.0

**Migration Guide:**
- See `MIGRATION_GUIDE.md` for detailed instructions
- Quick reference:
  ```python
  # OLD (v1.0)
  btn = StyleManager.create_button("Salvar", 'primary')
  font = TYPO.get_font(14, bold=True)

  # NEW (v2.0)
  btn = StandardButton("Salvar", variant="primary-green")
  font = TYPO.medium(14)  # or TYPO.get_font(14, weight=FontWeight.MEDIUM)
  ```

---

## Links

- **Typography Guide**: `TYPOGRAPHY_GUIDE.md`
- **Button Guide**: `BUTTON_GUIDE.md`
- **Migration Guide**: `MIGRATION_GUIDE.md`
- **Design System Decision**: `conductor/tracks/design_system_alignment_20260120/DECISION_LOG.md`

---

**Last Updated:** 2026-01-20
**Version:** 0.4.1
**Design System Version:** 2.0
