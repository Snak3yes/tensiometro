"""
Gerber Object Editor

Module responsible for editing Gerber objects (edit/delete/move operations).
Extracted from mainwindow.py to follow Single Responsibility Principle.

Classes:
    ObjectEditor: Handles all object manipulation operations
"""

from typing import TYPE_CHECKING
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QMessageBox,
)
from PyQt6.QtCore import QObject, pyqtSignal

if TYPE_CHECKING:
    from .parser import GerberObject
    from .gui.mainwindow import WidthHeightDialog, GerberMacroViewer
    from .gui.preview import PreviewGraphicsView
    from PyQt6.QtGui import QColor

from .commands.parser_edit_commands import create_parser_edit_command


class ObjectEditor(QObject):
    """
    Handles editing operations for Gerber objects.

    Responsibilities:
    - Edit single object properties (diameter, width, height, scale)
    - Edit multiple objects (group editing)
    - Delete objects (single or multiple)
    - Move objects (translation)

    This class was extracted from GerberMacroViewer to follow SRP.
    """

    # Signals to notify main window of changes
    objects_modified = pyqtSignal()
    objects_deleted = pyqtSignal()

    def __init__(
        self,
        preview_view: "PreviewGraphicsView",
        aperture_color: "QColor",
        background_color: "QColor",
        parent: "GerberMacroViewer" = None,
    ):
        """
        Initialize ObjectEditor.

        Args:
            preview_view: Preview graphics view for rendering
            aperture_color: Color for apertures
            background_color: Background color
            parent: Parent window (for dialogs)
        """
        super().__init__(parent)
        self._preview_view = preview_view
        self._aperture_color = aperture_color
        self._background_color = background_color
        self._parent_window = parent

    # ====================================================================== #
    # EDIT: Single Object
    # ====================================================================== #

    def edit_object(
        self,
        obj: "GerberObject",
        index: int,
        objects_list: list["GerberObject"],
    ) -> "GerberObject | None":
        """
        Edit properties of a single Gerber object.

        Args:
            obj: Object to edit
            index: Index of object in list
            objects_list: Full list of objects (for updating)

        Returns:
            Modified object if successful, None otherwise

        Supported types:
            - flash_circle: diameter
            - flash_rect: width x height
            - flash_oval: width x height
            - region: width x height (by scale)
        """
        from .gui.mainwindow import WidthHeightDialog

        print(
            "[DEBUG edit] objeto selecionado:",
            f"idx={index}, kind={obj.kind}, dcode={obj.dcode}, "
            f"x={obj.x_mm}, y={obj.y_mm}, params={obj.params}",
        )

        # Create appropriate command using Factory Function
        command = create_parser_edit_command(obj)
        if command is None:
            QMessageBox.information(
                self._parent_window,
                "Não editável",
                "Este tipo de objeto ainda não pode ser editado.",
            )
            return None

        # Execute type-specific dialog and modify object
        modified_obj = None

        if obj.kind == "flash_circle":
            modified_obj = self._edit_circle(obj, command)
        elif obj.kind in ("flash_rect", "flash_oval"):
            modified_obj = self._edit_rectangle_or_oval(obj, command)
        elif obj.kind == "region":
            modified_obj = self._edit_region(obj, command)

        return modified_obj

    def _edit_circle(
        self,
        obj: "GerberObject",
        command,
    ) -> "GerberObject | None":
        """Edit circle diameter."""
        cur_dia = float(obj.params.get("dia_mm", 0.0))
        new_dia, ok = QInputDialog.getDouble(
            self._parent_window,
            "Editar diâmetro",
            "Novo diâmetro (mm):",
            cur_dia,
            0.001,
            1000.0,
            3,  # decimals
        )
        if not ok:
            return None
        if new_dia <= 0:
            QMessageBox.warning(
                self._parent_window,
                "Valor inválido",
                "O diâmetro deve ser maior que zero.",
            )
            return None

        # Use command to modify object
        try:
            return command.execute(new_dia_mm=new_dia)
        except ValueError as e:
            QMessageBox.warning(self._parent_window, "Erro ao modificar", str(e))
            return None

    def _edit_rectangle_or_oval(
        self,
        obj: "GerberObject",
        command,
    ) -> "GerberObject | None":
        """Edit rectangle or oval width/height."""
        from .gui.mainwindow import WidthHeightDialog

        cur_w = float(obj.params.get("width_mm", 0.0))
        cur_h = float(obj.params.get("height_mm", 0.0))

        title = (
            "Editar abertura retangular"
            if obj.kind == "flash_rect"
            else "Editar abertura oval"
        )
        dlg = WidthHeightDialog(
            title=title,
            label_width="Largura (mm):",
            label_height="Altura (mm):",
            cur_w=cur_w,
            cur_h=cur_h,
            parent=self._parent_window,
            move_callback=lambda dx, dy: self._move_object(obj, dx, dy),
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None

        new_w, new_h = dlg.values()

        if new_w <= 0 or new_h <= 0:
            QMessageBox.warning(
                self._parent_window,
                "Valores inválidos",
                "Largura e altura devem ser maiores que zero.",
            )
            return None

        # Use command to modify object
        try:
            return command.execute(new_width_mm=new_w, new_height_mm=new_h)
        except ValueError as e:
            QMessageBox.warning(self._parent_window, "Erro ao modificar", str(e))
            return None

    def _edit_region(
        self,
        obj: "GerberObject",
        command,
    ) -> "GerberObject | None":
        """Edit region width/height by scale."""
        from .gui.mainwindow import WidthHeightDialog

        if not obj.polygon_mm or len(obj.polygon_mm) < 3:
            QMessageBox.information(
                self._parent_window,
                "Não editável",
                "Esta região não possui polígono válido para edição.",
            )
            return None

        # Calculate current dimensions
        xs = [p[0] for p in obj.polygon_mm]
        ys = [p[1] for p in obj.polygon_mm]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        cur_w = maxx - minx
        cur_h = maxy - miny

        if cur_w <= 0 or cur_h <= 0:
            QMessageBox.information(
                self._parent_window,
                "Não editável",
                "Não foi possível determinar largura/altura da região.",
            )
            return None

        # Dialog
        dlg = WidthHeightDialog(
            title="Editar tamanho da região",
            label_width="Largura (mm):",
            label_height="Altura (mm):",
            cur_w=cur_w,
            cur_h=cur_h,
            parent=self._parent_window,
            move_callback=lambda dx, dy: self._move_object(obj, dx, dy),
        )
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None

        new_w, new_h = dlg.values()

        if new_w <= 0 or new_h <= 0:
            QMessageBox.warning(
                self._parent_window,
                "Valores inválidos",
                "Largura e altura devem ser maiores que zero.",
            )
            return None

        # Calculate scale factors
        sx = new_w / cur_w
        sy = new_h / cur_h

        # Use command to modify object
        try:
            return command.execute(scale_x=sx, scale_y=sy)
        except ValueError as e:
            QMessageBox.warning(self._parent_window, "Erro ao modificar", str(e))
            return None

    # ====================================================================== #
    # EDIT: Multiple Objects
    # ====================================================================== #

    def edit_many_objects(
        self,
        indices: list[int],
        objects_list: list["GerberObject"],
    ) -> bool:
        """
        Edit multiple objects (group editing).

        Behavior:
            - Maintains individual centers of each object
            - Only allows group editing if objects are same type
            - Same type + same dimensions → edit by mm + %
            - Same type + different dimensions → edit by % only

        Supported types:
            - flash_rect
            - flash_oval
            - region

        Args:
            indices: List of object indices to edit
            objects_list: Full list of objects

        Returns:
            True if successful, False otherwise
        """
        if not indices:
            return False

        # Get valid sorted indices
        valid_indices: list[int] = [
            i for i in sorted(set(indices))
            if 0 <= i < len(objects_list)
        ]
        if len(valid_indices) < 2:
            # Fall back to single edit
            if valid_indices:
                modified = self.edit_object(
                    objects_list[valid_indices[0]],
                    valid_indices[0],
                    objects_list,
                )
                if modified is not None:
                    objects_list[valid_indices[0]] = modified
                    self.refresh_preview(objects_list)
                    return True
            return False

        # Get objects
        objs: list["GerberObject"] = [
            objects_list[i] for i in valid_indices
        ]
        kinds = {o.kind for o in objs}
        if len(kinds) != 1:
            QMessageBox.information(
                self._parent_window,
                "Edição em grupo",
                "A edição em grupo só é suportada para objetos do MESMO tipo.\n"
                "Selecione apenas retângulos, apenas ovais ou apenas regiões.",
            )
            return False

        kind = next(iter(kinds))

        # Create command
        command = create_parser_edit_command(objs[0])
        if command is None:
            QMessageBox.information(
                self._parent_window,
                "Edição em grupo",
                "Edição em grupo ainda não foi implementada para este tipo "
                "de objeto.",
            )
            return False

        # Process by type
        if kind in ("flash_rect", "flash_oval"):
            self._edit_rectangle_or_oval_group(objs, kind, objects_list)
        elif kind == "region":
            self._edit_region_group(objs, objects_list)

        self.refresh_preview(objects_list)
        return True

    def _edit_rectangle_or_oval_group(
        self,
        objs: list["GerberObject"],
        kind: str,
        objects_list: list["GerberObject"],
    ):
        """Edit group of rectangles or ovals."""
        from .gui.mainwindow import WidthHeightDialog

        # Get original indices
        valid_indices: list[int] = []
        for o in objs:
            for idx in range(len(objects_list)):
                if objects_list[idx] == o:
                    valid_indices.append(idx)
                    break

        # Get individual widths/heights
        ws = []
        hs = []
        for o in objs:
            try:
                ws.append(float(o.params.get("width_mm", 0.0)))
                hs.append(float(o.params.get("height_mm", 0.0)))
            except Exception:
                ws.append(0.0)
                hs.append(0.0)
        if not ws or not hs:
            return
        base_w = ws[0]
        base_h = hs[0]

        # Check if all dimensions are equal
        tol = 1e-6
        same_size = all(abs(w - base_w) < tol for w in ws) and all(
            abs(h - base_h) < tol for h in hs
        )

        title = (
            "Editar aberturas retangulares (grupo)"
            if kind == "flash_rect"
            else "Editar aberturas ovais (grupo)"
        )

        dlg = WidthHeightDialog(
            title=title,
            label_width="Largura (mm):",
            label_height="Altura (mm):",
            cur_w=base_w,
            cur_h=base_h,
            parent=self._parent_window,
            move_callback=lambda dx, dy: self._move_objects(objs, dx, dy),
            percent_only=not same_size,
        )

        if not same_size:
            QMessageBox.information(
                self._parent_window,
                "Edição em grupo",
                "Os objetos selecionados possuem dimensões diferentes.\n"
                "A edição por medida em mm foi desabilitada; use apenas "
                "a edição por percentual (%).",
            )

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        # Apply modifications using Command Pattern
        if same_size:
            # Edit by measurement and/or % → use final size in mm
            new_w, new_h = dlg.values()
            if new_w <= 0 or new_h <= 0:
                QMessageBox.warning(
                    self._parent_window,
                    "Valores inválidos",
                    "Largura e altura devem ser maiores que zero.",
                )
                return

            for i, o in enumerate(objs):
                cmd = create_parser_edit_command(o)
                if cmd is not None:
                    try:
                        modified = cmd.execute(
                            new_width_mm=new_w, new_height_mm=new_h
                        )
                        if i < len(valid_indices):
                            objects_list[valid_indices[i]] = modified
                    except ValueError as e:
                        QMessageBox.warning(
                            self._parent_window, "Erro ao modificar", str(e)
                        )
                        return
        else:
            # Edit only by % → use scale factors
            sx, sy = dlg.scales()
            for i, o in enumerate(objs):
                cmd = create_parser_edit_command(o)
                if cmd is not None:
                    try:
                        modified = cmd.execute(scale_x=sx, scale_y=sy)
                        if i < len(valid_indices):
                            objects_list[valid_indices[i]] = modified
                    except ValueError as e:
                        QMessageBox.warning(
                            self._parent_window, "Erro ao modificar", str(e)
                        )
                        return

    def _edit_region_group(
        self,
        objs: list["GerberObject"],
        objects_list: list["GerberObject"],
    ):
        """Edit group of regions."""
        from .gui.mainwindow import WidthHeightDialog

        # Get original indices
        valid_indices: list[int] = []
        for o in objs:
            for idx in range(len(objects_list)):
                if objects_list[idx] == o:
                    valid_indices.append(idx)
                    break

        # Calculate width/height and individual centers
        widths: list[float] = []
        heights: list[float] = []
        centers: list[tuple[float, float]] = []
        for o in objs:
            poly = o.polygon_mm
            if not poly or len(poly) < 3:
                QMessageBox.information(
                    self._parent_window,
                    "Não editável",
                    "Uma das regiões selecionadas não possui polígono válido.",
                )
                return
            xs = [p[0] for p in poly]
            ys = [p[1] for p in poly]
            minx, maxx = min(xs), max(xs)
            miny, maxy = min(ys), max(ys)
            w = maxx - minx
            h = maxy - miny
            if w <= 0 or h <= 0:
                QMessageBox.information(
                    self._parent_window,
                    "Não editável",
                    "Não foi possível determinar largura/altura de uma região.",
                )
                return
            cx = (minx + maxx) / 2.0
            cy = (miny + maxy) / 2.0
            widths.append(w)
            heights.append(h)
            centers.append((cx, cy))

        base_w = widths[0]
        base_h = heights[0]
        tol = 1e-6
        same_size = all(abs(w - base_w) < tol for w in widths) and all(
            abs(h - base_h) < tol for h in heights
        )

        dlg = WidthHeightDialog(
            title="Editar tamanho das regiões (grupo)",
            label_width="Largura (mm):",
            label_height="Altura (mm):",
            cur_w=base_w,
            cur_h=base_h,
            parent=self._parent_window,
            move_callback=lambda dx, dy: self._move_objects(objs, dx, dy),
            percent_only=not same_size,
        )

        if not same_size:
            QMessageBox.information(
                self._parent_window,
                "Edição em grupo",
                "As regiões selecionadas possuem dimensões diferentes.\n"
                "A edição por medida em mm foi desabilitada; use apenas "
                "a edição por percentual (%).",
            )

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        if same_size:
            new_w, new_h = dlg.values()
            if new_w <= 0 or new_h <= 0:
                QMessageBox.warning(
                    self._parent_window,
                    "Valores inválidos",
                    "Largura e altura devem ser maiores que zero.",
                )
                return
            sx = new_w / base_w
            sy = new_h / base_h
        else:
            sx, sy = dlg.scales()

        # Apply scale to each region using Command Pattern
        for i, (o, (cx, cy)) in enumerate(zip(objs, centers)):
            cmd = create_parser_edit_command(o)
            if cmd is not None:
                try:
                    # For regions, we calculate dx, dy to maintain center
                    poly = o.polygon_mm
                    if not poly:
                        continue
                    # Command pattern applies scale relative to center
                    modified = cmd.execute(scale_x=sx, scale_y=sy)
                    if i < len(valid_indices):
                        objects_list[valid_indices[i]] = modified
                except ValueError as e:
                    QMessageBox.warning(self._parent_window, "Erro ao modificar", str(e))
                    return

    # ====================================================================== #
    # DELETE: Single or Multiple Objects
    # ====================================================================== #

    def delete_object(
        self,
        index: int,
        objects_list: list["GerberObject"],
    ) -> bool:
        """
        Delete a single Gerber object.

        Args:
            index: Index of object to delete
            objects_list: List of objects (will be modified)

        Returns:
            True if deleted, False otherwise
        """
        if not (0 <= index < len(objects_list)):
            return False

        obj = objects_list[index]

        # Confirmation
        desc = obj.kind
        if obj.dcode is not None:
            desc += f" (D{obj.dcode})"
        msg = (
            "Tem certeza que deseja excluir este objeto?\n\n"
            f"Tipo: {obj.kind}\n"
        )
        if obj.dcode is not None:
            msg += f"D-code: D{obj.dcode}\n"
        if obj.x_mm is not None and obj.y_mm is not None:
            msg += f"Posição: ({obj.x_mm:.6f}, {obj.y_mm:.6f}) mm\n"

        reply = QMessageBox.question(
            self._parent_window,
            "Confirmar exclusão",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return False

        # Remove object
        del objects_list[index]
        return True

    def delete_many_objects(
        self,
        indices: list[int],
        objects_list: list["GerberObject"],
    ) -> bool:
        """
        Delete multiple Gerber objects with single confirmation.

        Args:
            indices: List of object indices to delete
            objects_list: List of objects (will be modified)

        Returns:
            True if any deleted, False otherwise
        """
        if not indices:
            return False

        valid_indices: list[int] = [
            i for i in sorted(set(indices))
            if 0 <= i < len(objects_list)
        ]
        if not valid_indices:
            return False

        n = len(valid_indices)
        reply = QMessageBox.question(
            self._parent_window,
            "Confirmar exclusão",
            f"Tem certeza que deseja excluir {n} objetos selecionados?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return False

        # Remove from highest to lowest index to avoid shifting
        for idx in sorted(valid_indices, reverse=True):
            try:
                del objects_list[idx]
            except IndexError:
                continue

        return True

    # ====================================================================== #
    # MOVE: Translation
    # ====================================================================== #

    def _move_object(self, obj: "GerberObject", dx: float, dy: float):
        """
        Apply translation (dx, dy) in mm to a single object.

        Args:
            obj: Object to move
            dx: X translation in mm
            dy: Y translation in mm
        """
        self._move_objects([obj], dx, dy)

    def _move_objects(
        self,
        objs: list["GerberObject"],
        dx: float,
        dy: float,
    ):
        """
        Apply translation (dx, dy) in mm to multiple objects.

        Args:
            objs: List of objects to move
            dx: X translation in mm
            dy: Y translation in mm
        """
        if not objs:
            return

        # Update position of flash/center, if exists
        for obj in objs:
            if obj.x_mm is not None:
                obj.x_mm += dx
            if obj.y_mm is not None:
                obj.y_mm += dy
            # Translate associated polygon
            if obj.polygon_mm:
                obj.polygon_mm = [
                    (x + dx, y + dy) for (x, y) in obj.polygon_mm
                ]

    # ====================================================================== #
    # PREVIEW: Refresh
    # ====================================================================== #

    def refresh_preview(self, objects_list: list["GerberObject"]):
        """
        Refresh preview after editing.

        Args:
            objects_list: Current list of objects
        """
        # Update polygon list from objects
        polys_mm = [
            o.polygon_mm
            for o in objects_list
            if o.polygon_mm and len(o.polygon_mm) >= 3
        ]

        # Re-render
        self._preview_view.set_objects(
            objects_list,
            aperture_color=self._aperture_color,
            bg_color=self._background_color,
            preserve_view=True,  # maintain zoom/pan after edit
        )

        # Emit signal
        self.objects_modified.emit()

    def clear_preview(self):
        """Clear the preview."""
        self._preview_view._scene.clear()
        self._preview_view._polys_mm = []
        self._preview_view._objects = None
