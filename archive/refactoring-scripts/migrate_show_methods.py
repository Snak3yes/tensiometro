#!/usr/bin/env python3
"""
Migra métodos show_* do main_window para delegar ao DialogRouter.

Métodos a serem substituídos:
- show_recipe_manager
- show_new_recipe_dialog
- show_stencil_manager
- show_new_stencil_dialog
- show_mosaic_builder
- show_camera_calibration_dialog
- show_fov_calibration_dialog
- show_crosshair_settings_dialog
- show_fiducial_alignment_dialog
- show_report_settings
- show_tension_report_dialog
- show_stencil_report_dialog
- show_period_query_dialog
- show_inspection_settings
- show_inspection_dialog
- show_last_inspection_result
- show_settings_dialog
- show_about_dialog
"""

import re

METHODS_TO_REPLACE = [
    'show_recipe_manager',
    'show_new_recipe_dialog',
    'show_stencil_manager',
    'show_new_stencil_dialog',
    'show_mosaic_builder',
    'show_camera_calibration_dialog',
    'show_fov_calibration_dialog',
    'show_crosshair_settings_dialog',
    'show_fiducial_alignment_dialog',
    'show_report_settings',
    'show_tension_report_dialog',
    'show_stencil_report_dialog',
    'show_period_query_dialog',
    'show_inspection_settings',
    'show_inspection_dialog',
    'show_last_inspection_result',
    'show_settings_dialog',
    'show_about_dialog',
]

def migrate_show_methods(input_file, output_file):
    """Substitui métodos show_* por stubs que delegam ao DialogRouter."""

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output_lines = []
    skip_mode = False
    replaced_count = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detecta início de método show_*
        method_match = None
        for method_name in METHODS_TO_REPLACE:
            pattern = rf'^\s*def {method_name}\(self'
            if re.match(pattern, line):
                method_match = method_name
                break

        if method_match:
            # Substitui por stub
            indent = len(line) - len(line.lstrip())
            stub_lines = [
                f"{' ' * indent}def {method_match}(self):\n",
                f"{' ' * indent}    \"\"\"Ver docstring completa em DialogRouter.{method_match}\"\"\"\n",
                f"{' ' * indent}    self.dialog_router.{method_match}()\n",
                f"{' ' * indent}\n",
            ]
            output_lines.extend(stub_lines)
            replaced_count += 1

            # Pula método original
            i += 1
            current_indent = indent

            while i < len(lines):
                next_line = lines[i]

                # Se chegou em um método/classe com mesma ou menor indentação, parou
                if next_line.strip() and not next_line.strip().startswith('#'):
                    next_indent = len(next_line) - len(next_line.lstrip())
                    if next_indent <= current_indent and re.match(r'^\s*(def |class )', next_line):
                        break

                i += 1

            continue

        # Se não está em modo skip, adiciona a linha
        if not skip_mode:
            output_lines.append(line)

        i += 1

    # Escreve o arquivo modificado
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)

    return replaced_count

if __name__ == '__main__':
    input_file = 'consumo_lib/main_window.py'
    output_file = 'consumo_lib/main_window.py'

    print("Migrando métodos show_* para delegar ao DialogRouter...")
    replaced = migrate_show_methods(input_file, output_file)

    print(f"\nResultado:")
    print(f"- Métodos substituídos: {replaced}")
    print(f"- Arquivo atualizado: {output_file}")
