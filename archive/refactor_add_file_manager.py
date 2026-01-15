#!/usr/bin/env python3
"""
Script para refatorar mainwindow.py usando GerberFileManager.
"""

import re
from pathlib import Path


def refactor_with_file_manager():
    """Refatora mainwindow.py para usar GerberFileManager."""

    project_root = Path(__file__).parent
    mainwindow_path = project_root / "aoi_lib" / "gerber_core" / "gui" / "mainwindow.py"

    # Read file
    with open(mainwindow_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # ========================================================================
    # 1. Add GerberFileManager import
    # ========================================================================

    import_pattern = r'(from \.\.object_editor import ObjectEditor)'
    import_replacement = r'''\1
from ..file_manager import GerberFileManager'''

    if "from ..file_manager import GerberFileManager" not in content:
        content = re.sub(import_pattern, import_replacement, content)

    # ========================================================================
    # 2. Create GerberFileManager instance in __init__
    # ========================================================================

    init_pattern = r'(        # Object Editor: Handles edit/delete/move operations\s+self\.object_editor = ObjectEditor\()'

    init_replacement = r'''\1
            preview_view=self.preview_view,
            aperture_color=self.aperture_color,
            background_color=self.background_color,
            parent=self,
        )

        # File Manager: Handles file I/O operations
        self.file_manager = GerberFileManager(
            preview_width=self.preview_width,
            preview_height=self.preview_height,
            parent=self,
        )'''

    content = re.sub(init_pattern, init_replacement, content)

    # ========================================================================
    # 3. Update on_new_project to use GerberFileManager
    # ========================================================================

    new_project_pattern = r'(    def on_new_project\(self\):.*?)(        # 4\) Inicia fluxo de importação de arquivo Gerber para este projeto\s+#    \(abre o diálogo de seleção e, se o arquivo for carregado,\s+#     já renderiza automaticamente a camada completa\)\s+self\.on_import_gbr\(\))'

    new_project_replacement = r'''\1

        # 4) Inicia fluxo de importação de arquivo Gerber para este projeto
        #    (abre o diálogo de seleção e, se o arquivo for carregado,
        #     já renderiza automaticamente a camada completa)
        self.on_import_gbr()'''

    # Keep this method as-is for now, it's simple enough

    # ========================================================================
    # 4. Update on_import_gbr to use GerberFileManager
    # ========================================================================

    import_gbr_pattern = r'(    def on_import_gbr\(self\):.*?)(        loaded = self\.on_open_file\(\)\s+if not loaded:\s+return\s+self\.on_render_full_layer\(\))'

    import_gbr_replacement = r'''    def on_import_gbr(self):
        """
        Importa um arquivo Gerber (.gbr).

        REFATORADO: Usa GerberFileManager para separar responsabilidades.
        """
        def file_dialog():
            from PyQt6.QtWidgets import QFileDialog
            filters = (
                "Arquivos Gerber (*.gbr *.ger *.pho *.art *.gb* *.gt* *.g*);;"
                "Todos os arquivos (*.*)"
            )
            return QFileDialog.getOpenFileName(
                self,
                "Selecionar arquivo Gerber",
                "",
                filters,
            )

        loaded = self.file_manager.import_gbr(file_dialog)
        if loaded:
            # Update local state from file manager
            self.gerber_lines = self.file_manager.gerber_lines
            self.gerber_cfg = self.file_manager.gerber_cfg
            self.apertures_by_dcode = self.file_manager.apertures_by_dcode
            self.macros = self.file_manager.macros
            self._full_layer_objects = self.file_manager.full_layer_objects
            self._full_layer_polys_mm = self.file_manager.full_layer_polys_mm'''

    content = re.sub(import_gbr_pattern, import_gbr_replacement, content, flags=re.DOTALL)

    # ========================================================================
    # 5. Update on_open_file to use GerberFileManager
    # ========================================================================

    open_file_pattern = r'(    def on_open_file\(self\) -> bool:.*?)(        self\.clear_preview\(\)\s+return True)'

    open_file_replacement = r'''    def on_open_file(self) -> bool:
        """
        Abre arquivo Gerber.

        REFATORADO: Usa GerberFileManager para separar responsabilidades.
        """
        def file_dialog():
            from PyQt6.QtWidgets import QFileDialog
            filters = (
                "Arquivos Gerber (*.gbr *.ger *.pho *.art *.gb* *.gt* *.g*);;"
                "Todos os arquivos (*.*)"
            )
            return QFileDialog.getOpenFileName(
                self,
                "Selecionar arquivo Gerber",
                "",
                filters,
            )

        return self.file_manager.open_file(file_dialog)'''

    content = re.sub(open_file_pattern, open_file_replacement, content, flags=re.DOTALL)

    # ========================================================================
    # 6. Update on_render_full_layer to use GerberFileManager
    # ========================================================================

    render_full_pattern = r'(    def on_render_full_layer\(self\):.*?)(                    # Não foi possível converter a imagem da camada completa para exibição\.\s+\))'

    render_full_replacement = r'''    def on_render_full_layer(self):
        """
        Renderiza camada completa.

        REFATORADO: Usa GerberFileManager para separar responsabilidades.
        """
        if not self.file_manager.has_data:
            QMessageBox.information(
                self,
                "Nenhum arquivo",
                "Abra um arquivo Gerber antes de gerar a camada completa.",
            )
            return

        success = self.file_manager.render_full_layer()
        if not success:
            return

        # Update local state from file manager
        self._full_layer_objects = self.file_manager.full_layer_objects
        self._full_layer_polys_mm = self.file_manager.full_layer_polys_mm

        # Render preview
        self._current_pixmap = None
        if self._full_layer_objects:
            self.preview_view.set_objects(
                self._full_layer_objects,
                aperture_color=self.aperture_color,
                bg_color=self.background_color,
                preserve_view=False,  # primeira renderização: ajusta visão
            )
        else:
            # fallback (não deve ocorrer nesse fluxo normal)
            self.preview_view.set_polygons(
                self._full_layer_polys_mm,
                aperture_color=self.aperture_color,
                bg_color=self.background_color,
            )
        self.export_btn.setEnabled(True)
        self.reset_view_btn.setEnabled(True)'''

    content = re.sub(render_full_pattern, render_full_replacement, content, flags=re.DOTALL)

    # ========================================================================
    # 7. Update on_export_gbr to use GerberFileManager
    # ========================================================================

    export_gbr_pattern = r'(    def on_export_gbr\(self\):.*?)(                # Veja o terminal para detalhes\.\s+\))'

    export_gbr_replacement = r'''    def on_export_gbr(self):
        """
        Exporta camada atual para arquivo Gerber.

        REFATORADO: Usa GerberFileManager para separar responsabilidades.
        """
        def file_dialog():
            from PyQt6.QtWidgets import QFileDialog
            return QFileDialog.getSaveFileName(
                self,
                "Exportar como Gerber",
                "",
                "Arquivos Gerber (*.gbr *.ger *.pho *.art *.gb* *.gt* *.g*)",
            )

        self.file_manager.export_gbr(file_dialog)'''

    content = re.sub(export_gbr_pattern, export_gbr_replacement, content, flags=re.DOTALL)

    # ========================================================================
    # 8. Update on_export_png to use GerberFileManager
    # ========================================================================

    export_png_pattern = r'(    def on_export_png\(self\):.*?)(                # Veja o terminal para detalhes\.\s+\))'

    export_png_replacement = r'''    def on_export_png(self):
        """
        Exporta camada atual para PNG.

        REFATORADO: Usa GerberFileManager para separar responsabilidades.
        """
        def file_dialog():
            from PyQt6.QtWidgets import QFileDialog
            return QFileDialog.getSaveFileName(
                self,
                "Salvar imagem em PNG",
                "",
                "Imagem PNG (*.png)",
            )

        self.file_manager.export_png(
            file_dialog,
            self.aperture_color,
            self.background_color,
        )'''

    content = re.sub(export_png_pattern, export_png_replacement, content, flags=re.DOTALL)

    # ========================================================================
    # Write modified file
    # ========================================================================

    if content != original_content:
        with open(mainwindow_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Count lines
        original_lines = original_content.count('\n')
        new_lines = content.count('\n')
        reduction = original_lines - new_lines
        percentage = (reduction / original_lines) * 100

        print(f"[OK] Arquivo modificado: {mainwindow_path.name}")
        print(f"     Linhas originais: {original_lines}")
        print(f"     Linhas apos: {new_lines}")
        print(f"     Reducao: -{reduction} linhas ({percentage:.1f}%)")

        return True
    else:
        print("[INFO] Nenhuma modificacao necessaria.")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("Refatorando mainwindow.py para usar GerberFileManager")
    print("=" * 70)
    print()

    try:
        refactor_with_file_manager()
        print("\n[OK] Refatoracao concluida!")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
