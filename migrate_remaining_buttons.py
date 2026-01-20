"""
Script para migrar QPushButton para StandardButton automaticamente.

Este script:
1. Lê cada arquivo Python
2. Encontra QPushButton(...)
3. Substitui por StandardButton(...) com variant apropriado
4. Adiciona import de StandardButton se necessário
"""

import re
from pathlib import Path

# Mapeamento de padrões de botão para variantes
BUTTON_PATTERNS = [
    (r'QPushButton\("(Salvar|Salvar/Atualizar|Aplicar|Aplicar\s+\w+|OK|Confirmar|Concluir|▶️\s*Executar)"',
     'StandardButton("{text}", variant="primary")'),

    (r'QPushButton\("(Cancelar|Fechar|Voltar)"',
     'StandardButton("{text}")'),  # secondary is default

    (r'QPushButton\("(📁)"',
     'StandardButton("{text}", icon_only=True)'),

    (r'QPushButton\("(🎯|⚙️|▶️|💡)"',
     'StandardButton("{text}")'),

    (r'QPushButton\("([^"]+)"',
     'StandardButton("{text}")'),  # fallback
]

def detect_variant_from_text(text: str, button_text: str) -> str:
    """Detecta variante apropriada baseado no texto do botão"""
    button_text_lower = button_text.lower()

    # Primário
    primary_keywords = ['salvar', 'aplicar', 'confirmar', 'ok', 'concluir', 'executar', '▶️']
    if any(kw in button_text_lower for kw in primary_keywords):
        return 'variant="primary"'

    # Perigoso
    danger_keywords = ['excluir', 'deletar', 'remover', 'stop']
    if any(kw in button_text_lower for kw in danger_keywords):
        return 'variant="danger"'

    # Default (secondary)
    return ''

def migrate_file(file_path: Path) -> int:
    """Migra um arquivo Python, retorna quantidade de botões migrados"""
    content = file_path.read_text(encoding="utf-8")

    # Contar QPushButton originais
    original_count = content.count("QPushButton(")
    if original_count == 0:
        return 0

    # Adicionar import se não existe
    if "from consumo_lib.ui.widget_standards import StandardButton" not in content:
        # Encontrar o primeiro import de consumo_lib.ui ou PyQt6
        if "from consumo_lib.ui import" in content:
            content = re.sub(
                r'(from consumo_lib\.ui import [^\n]+)',
                r'\1\nfrom consumo_lib.ui.widget_standards import StandardButton',
                content,
                count=1
            )
        elif "from PyQt6.QtWidgets import" in content:
            # Adicionar após imports PyQt6
            content = re.sub(
                r'(from PyQt6\.QtWidgets import[^\n]+\))',
                r'\1\n\n# Design System\nfrom consumo_lib.ui.widget_standards import StandardButton',
                content,
                count=1
            )

    # Migração simples: QPushButton → StandardButton
    # Esta é uma migração conservadora - sempre usa variant padrão (secondary)
    # Exceto para botões claramente primários
    lines = content.split('\n')
    migrated = 0

    for i, line in enumerate(lines):
        if "QPushButton(" in line and "StandardButton" not in line:
            # Extrair o texto do botão
            match = re.search(r'QPushButton\("([^"]+)"', line)
            if match:
                button_text = match.group(1)
                variant = detect_variant_from_text(button_text, button_text)

                # Substituir
                if variant:
                    new_line = line.replace(
                        f'QPushButton("{button_text}")',
                        f'StandardButton("{button_text}", {variant})'
                    )
                else:
                    new_line = line.replace(
                        f'QPushButton("{button_text}")',
                        f'StandardButton("{button_text}")'
                    )

                lines[i] = new_line
                migrated += 1

    # Escrever de volta
    new_content = '\n'.join(lines)
    file_path.write_text(new_content, encoding="utf-8")

    return migrated

def main():
    """Função principal"""
    # Lista de arquivos para migrar (baseado no inventário)
    files_to_migrate = [
        # Dialogs de alta complexidade (5-8 botões)
        "consumo_lib/dialogs/defect_judgment_dialog.py",
        "consumo_lib/dialogs/map_settings_dialog.py",
        "consumo_lib/widgets/engenharia/inspection_windows_widget.py",
        "consumo_lib/dialogs/tension/tension_measurement_dialog.py",
        "consumo_lib/dialogs/report_settings.py",
        "consumo_lib/widgets/sequence_control.py",
        "consumo_lib/dialogs/recipe/recipe_manager_dialog.py",
        "consumo_lib/dialogs/stencil/manager_dialog.py",
        "consumo_lib/ui_builders/ui_builders.py",
        "consumo_lib/widgets/engenharia/gerber_upload_widget.py",

        # Dialogs de média complexidade (2-4 botões)
        "consumo_lib/dialogs/crosshair_settings.py",
        "consumo_lib/dialogs/engineering_wizard_dialog.py",
        "consumo_lib/dialogs/inspection_history_dialog.py",
        "consumo_lib/widgets/engenharia/alignment_widget.py",
        "consumo_lib/widgets/engenharia/gerber_edit_dialogs.py",
        "consumo_lib/widgets/stencil/identification_widget.py",
        "consumo_lib/controllers/report_dialog_controller.py",
        "consumo_lib/dialogs/final_decision_dialog.py",
        "consumo_lib/dialogs/inspection_results_dialog.py",
        "consumo_lib/dialogs/inspection_settings.py",
        "consumo_lib/tabs/tracking_tab.py",
        "consumo_lib/widgets/camera_capture.py",
        "consumo_lib/widgets/plc_monitor.py",
        "consumo_lib/widgets/tension_viz.py",
        "consumo_lib/widgets/engenharia/confirm_save_widget.py",
        "consumo_lib/widgets/engenharia/mosaic_capture_widget.py",
        "consumo_lib/utils/main_window/engineering_workflow.py",

        # Dialogs simples (2-3 botões)
        "consumo_lib/dialogs/auth_settings_dialog.py",
        "consumo_lib/dialogs/confirm_positioning_dialog.py",
        "consumo_lib/dialogs/fov_calibration.py",
        "consumo_lib/dialogs/inspection_progress_dialog.py",
        "consumo_lib/dialogs/login_dialog.py",
        "consumo_lib/dialogs/mode_selection_dialog.py",
        "consumo_lib/dialogs/operator_workflow_dialog.py",
        "consumo_lib/dialogs/theme_settings.py",
        "consumo_lib/tabs/inspection_tab.py",
        "consumo_lib/tabs/map_tab.py",
        "consumo_lib/tabs/tree_view_tab.py",
        "consumo_lib/widgets/camera_preview.py",
        "consumo_lib/widgets/position_list.py",
        "consumo_lib/widgets/position_registry.py",
        "consumo_lib/widgets/engenharia/fiducial_capture_widget.py",
        "consumo_lib/dialogs/stencil/full_history_dialog.py",
        "consumo_lib/dialogs/stencil/history_dialog.py",

        # Baixa prioridade (1 botão)
        "consumo_lib/controllers/fiducial_alignment_controller.py",
        "consumo_lib/handlers/dialog_router.py",
    ]

    total_migrated = 0
    errors = []

    for file_path_str in files_to_migrate:
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"[NOK] ARQUIVO NAO EXISTE: {file_path_str}")
            continue

        try:
            migrated = migrate_file(file_path)
            if migrated > 0:
                print(f"[OK] {file_path_str}: {migrated} botoes migrados")
                total_migrated += migrated
            else:
                print(f"[--] {file_path_str}: Nenhum botao encontrado")
        except Exception as e:
            print(f"[ERRO] em {file_path_str}: {e}")
            errors.append((file_path_str, str(e)))

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_migrated} botões migrados")
    print(f"ARQUIVOS COM ERRO: {len(errors)}")

    if errors:
        print("\nERROS:")
        for file_path, error in errors:
            print(f"  - {file_path}: {error}")

if __name__ == "__main__":
    main()
