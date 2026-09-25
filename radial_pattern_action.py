import math

import wx

from kipy import KiCad
from kipy.board_types import BoardLayer, BoardSegment, Group
from kipy.geometry import Vector2
from kipy.util import from_mm


PLUGIN_NAME = "Radial Pattern Generator"
GROUP_PREFIX = "Radial Pattern"


# ============================================================
# Geometry
# ============================================================

def generate_radial_lines(
    radius,
    start_angle,
    total_angle,
    n_lines,
    line_length_start,
    line_length_end,
    density_exp,
    length_exp,
):
    """
    Generate radial line segments.

    All dimensions are in mm.
    Angles are in degrees.

    Returns:
        [(x1, y1, x2, y2), ...]
    """

    if n_lines < 1:
        return []

    lines = []

    for i in range(n_lines):

        t = (
            0.0
            if n_lines == 1
            else i / (n_lines - 1)
        )

        # ----------------------------------------------------
        # Angular density
        # ----------------------------------------------------

        if density_exp == 0:
            t_density = t
        else:
            denominator = math.exp(density_exp) - 1.0

            t_density = (
                math.exp(density_exp * t) - 1.0
            ) / denominator

        angle_deg = (
            start_angle
            + total_angle * t_density
        )

        angle = math.radians(angle_deg)

        # ----------------------------------------------------
        # Line length
        # ----------------------------------------------------

        if length_exp == 0:
            t_length = t
        else:
            denominator = math.exp(length_exp) - 1.0

            t_length = (
                math.exp(length_exp * t) - 1.0
            ) / denominator

        length = (
            line_length_start
            + (
                line_length_end
                - line_length_start
            ) * t_length
        )

        # ----------------------------------------------------
        # Coordinates relative to center
        # ----------------------------------------------------

        r1 = radius
        r2 = radius + length

        x1 = r1 * math.cos(angle)
        y1 = r1 * math.sin(angle)

        x2 = r2 * math.cos(angle)
        y2 = r2 * math.sin(angle)

        lines.append(
            (x1, y1, x2, y2)
        )

    return lines


# ============================================================
# Dialog
# ============================================================

class RadialPatternDialog(wx.Dialog):

    def __init__(self, parent):

        super().__init__(
            parent,
            title=PLUGIN_NAME,
            size=(500, 780),
        )

        panel = wx.Panel(self)
        main = wx.BoxSizer(wx.VERTICAL)

        # ----------------------------------------------------
        # Helper
        # ----------------------------------------------------

        def add_field(
            label,
            value,
        ):
            row = wx.BoxSizer(wx.HORIZONTAL)

            row.Add(
                wx.StaticText(
                    panel,
                    label=label,
                ),
                1,
                wx.ALIGN_CENTER_VERTICAL
                | wx.RIGHT,
                10,
            )

            field = wx.TextCtrl(
                panel,
                value=str(value),
            )

            row.Add(
                field,
                1,
            )

            main.Add(
                row,
                0,
                wx.EXPAND
                | wx.LEFT
                | wx.RIGHT
                | wx.TOP,
                6,
            )

            return field

        # ----------------------------------------------------
        # Center
        # ----------------------------------------------------

        center_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            panel,
            "Pattern Center",
        )

        self.center_selected = wx.RadioButton(
            panel,
            label="Use center of selected item",
            style=wx.RB_GROUP,
        )

        self.center_coordinates = wx.RadioButton(
            panel,
            label="Use coordinates",
        )

        self.center_selected.SetValue(True)

        center_box.Add(
            self.center_selected,
            0,
            wx.ALL,
            5,
        )

        center_box.Add(
            self.center_coordinates,
            0,
            wx.ALL,
            5,
        )

        xy = wx.BoxSizer(wx.HORIZONTAL)

        xy.Add(
            wx.StaticText(
                panel,
                label="X (mm):",
            ),
            0,
            wx.ALIGN_CENTER_VERTICAL
            | wx.RIGHT,
            5,
        )

        self.center_x = wx.TextCtrl(
            panel,
            value="0",
        )

        xy.Add(
            self.center_x,
            1,
            wx.RIGHT,
            15,
        )

        xy.Add(
            wx.StaticText(
                panel,
                label="Y (mm):",
            ),
            0,
            wx.ALIGN_CENTER_VERTICAL
            | wx.RIGHT,
            5,
        )

        self.center_y = wx.TextCtrl(
            panel,
            value="0",
        )

        xy.Add(
            self.center_y,
            1,
        )

        center_box.Add(
            xy,
            0,
            wx.EXPAND | wx.ALL,
            5,
        )

        main.Add(
            center_box,
            0,
            wx.EXPAND | wx.ALL,
            10,
        )

        # ----------------------------------------------------
        # Geometry
        # ----------------------------------------------------

        geometry_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            panel,
            "Geometry",
        )

        geometry_fields = wx.BoxSizer(
            wx.VERTICAL
        )

        def add_geometry_field(
            label,
            value,
        ):
            row = wx.BoxSizer(
                wx.HORIZONTAL
            )

            row.Add(
                wx.StaticText(
                    panel,
                    label=label,
                ),
                1,
                wx.ALIGN_CENTER_VERTICAL
                | wx.RIGHT,
                10,
            )

            field = wx.TextCtrl(
                panel,
                value=str(value),
            )

            row.Add(
                field,
                1,
            )

            geometry_fields.Add(
                row,
                0,
                wx.EXPAND
                | wx.BOTTOM,
                5,
            )

            return field

        self.radius = add_geometry_field(
            "Inner radius (mm):",
            35,
        )

        self.start_angle = add_geometry_field(
            "Start angle (deg):",
            -60,
        )

        self.total_angle = add_geometry_field(
            "Total angle (deg):",
            300,
        )

        self.n_lines = add_geometry_field(
            "Number of lines:",
            45,
        )

        self.length_start = add_geometry_field(
            "Line length start (mm):",
            1,
        )

        self.length_end = add_geometry_field(
            "Line length end (mm):",
            11,
        )

        self.density_exp = add_geometry_field(
            "Density exponent:",
            5,
        )

        self.length_exp = add_geometry_field(
            "Length exponent:",
            3,
        )

        geometry_box.Add(
            geometry_fields,
            1,
            wx.EXPAND | wx.ALL,
            8,
        )

        main.Add(
            geometry_box,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT,
            10,
        )

        # ----------------------------------------------------
        # Copper
        # ----------------------------------------------------

        copper_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            panel,
            "Copper",
        )

        copper_row = wx.BoxSizer(
            wx.HORIZONTAL
        )

        copper_row.Add(
            wx.StaticText(
                panel,
                label="Layer:",
            ),
            1,
            wx.ALIGN_CENTER_VERTICAL
            | wx.RIGHT,
            10,
        )

        self.copper_layer = wx.Choice(
            panel,
            choices=[
                "F.Cu",
                "B.Cu",
            ],
        )

        self.copper_layer.SetSelection(0)

        copper_row.Add(
            self.copper_layer,
            1,
        )

        copper_box.Add(
            copper_row,
            0,
            wx.EXPAND | wx.ALL,
            8,
        )

        self.copper_width = add_to_sizer(
            copper_box,
            panel,
            "Line width (mm):",
            "0.5",
        )

        main.Add(
            copper_box,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            10,
        )

        # ----------------------------------------------------
        # Mask
        # ----------------------------------------------------

        mask_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            panel,
            "Solder Mask",
        )

        self.add_mask = wx.CheckBox(
            panel,
            label="Add corresponding solder-mask layer",
        )

        self.add_mask.SetValue(False)

        mask_box.Add(
            self.add_mask,
            0,
            wx.ALL,
            8,
        )

        mask_row = wx.BoxSizer(
            wx.HORIZONTAL
        )

        mask_row.Add(
            wx.StaticText(
                panel,
                label="Mask layer:",
            ),
            1,
            wx.ALIGN_CENTER_VERTICAL
            | wx.RIGHT,
            10,
        )

        self.mask_layer = wx.Choice(
            panel,
            choices=[
                "F.Mask",
                "B.Mask",
            ],
        )

        self.mask_layer.SetSelection(0)

        mask_row.Add(
            self.mask_layer,
            1,
        )

        mask_box.Add(
            mask_row,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT,
            8,
        )

        self.mask_width = add_to_sizer(
            mask_box,
            panel,
            "Mask line width (mm):",
            "0.6",
        )

        main.Add(
            mask_box,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            10,
        )

        # ----------------------------------------------------
        # Pattern options
        # ----------------------------------------------------

        options_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            panel,
            "Pattern",
        )

        self.pattern_name = add_to_sizer(
            options_box,
            panel,
            "Pattern name:",
            "Radial Pattern",
        )

        self.delete_previous = wx.CheckBox(
            panel,
            label="Delete previous generated patterns",
        )

        self.delete_previous.SetValue(False)

        options_box.Add(
            self.delete_previous,
            0,
            wx.ALL,
            8,
        )

        main.Add(
            options_box,
            0,
            wx.EXPAND | wx.ALL,
            10,
        )

        # ----------------------------------------------------
        # Copper layer change
        # ----------------------------------------------------

        self.copper_layer.Bind(
            wx.EVT_CHOICE,
            self.on_copper_layer_changed,
        )

        self.add_mask.Bind(
            wx.EVT_CHECKBOX,
            self.on_mask_checkbox,
        )

        self.mask_layer.Enable(False)
        self.mask_width.Enable(False)

        # ----------------------------------------------------
        # Buttons
        # ----------------------------------------------------

        buttons = wx.StdDialogButtonSizer()

        generate = wx.Button(
            panel,
            wx.ID_OK,
            "Generate",
        )

        cancel = wx.Button(
            panel,
            wx.ID_CANCEL,
            "Cancel",
        )

        buttons.AddButton(generate)
        buttons.AddButton(cancel)

        buttons.Realize()

        main.Add(
            buttons,
            0,
            wx.EXPAND | wx.ALL,
            10,
        )

        panel.SetSizer(main)
        self.Centre()

    # ========================================================
    # Mask handling
    # ========================================================

    def on_copper_layer_changed(self, event):

        copper = (
            self.copper_layer
            .GetStringSelection()
        )

        if copper == "F.Cu":
            self.mask_layer.SetStringSelection(
                "F.Mask"
            )

        elif copper == "B.Cu":
            self.mask_layer.SetStringSelection(
                "B.Mask"
            )

        self.mask_layer.Enable(
            self.add_mask.GetValue()
        )

        self.mask_width.Enable(
            self.add_mask.GetValue()
        )

        event.Skip()

    def on_mask_checkbox(self, event):

        enabled = self.add_mask.GetValue()

        self.mask_layer.Enable(
            enabled
        )

        self.mask_width.Enable(
            enabled
        )

        event.Skip()

    # ========================================================
    # Values
    # ========================================================

    def get_values(self):

        return {
            "radius":
                float(
                    self.radius.GetValue()
                ),

            "start_angle":
                float(
                    self.start_angle.GetValue()
                ),

            "total_angle":
                float(
                    self.total_angle.GetValue()
                ),

            "n_lines":
                int(
                    self.n_lines.GetValue()
                ),

            "line_length_start":
                float(
                    self.length_start.GetValue()
                ),

            "line_length_end":
                float(
                    self.length_end.GetValue()
                ),

            "density_exp":
                float(
                    self.density_exp.GetValue()
                ),

            "length_exp":
                float(
                    self.length_exp.GetValue()
                ),

            "copper_layer":
                self.copper_layer
                .GetStringSelection(),

            "copper_width":
                float(
                    self.copper_width.GetValue()
                ),

            "add_mask":
                self.add_mask.GetValue(),

            "mask_layer":
                self.mask_layer
                .GetStringSelection(),

            "mask_width":
                float(
                    self.mask_width.GetValue()
                ),

            "pattern_name":
                self.pattern_name.GetValue(),

            "delete_previous":
                self.delete_previous
                .GetValue(),

            "use_selected":
                self.center_selected
                .GetValue(),

            "center_x":
                float(
                    self.center_x.GetValue()
                ),

            "center_y":
                float(
                    self.center_y.GetValue()
                ),
        }


# ============================================================
# UI helper
# ============================================================

def add_to_sizer(
    sizer,
    panel,
    label,
    value,
):
    row = wx.BoxSizer(
        wx.HORIZONTAL
    )

    row.Add(
        wx.StaticText(
            panel,
            label=label,
        ),
        1,
        wx.ALIGN_CENTER_VERTICAL
        | wx.RIGHT,
        10,
    )

    field = wx.TextCtrl(
        panel,
        value=value,
    )

    row.Add(
        field,
        1,
    )

    sizer.Add(
        row,
        0,
        wx.EXPAND
        | wx.LEFT
        | wx.RIGHT
        | wx.BOTTOM,
        8,
    )

    return field


# ============================================================
# Plugin
# ============================================================

class RadialPatternPlugin:

    def __init__(self):

        self.kicad = KiCad()

    # ========================================================
    # Get board
    # ========================================================

    def get_board(self):

        board = self.kicad.get_board()

        if board is None:
            raise RuntimeError(
                "No PCB is currently open."
            )

        return board

    # ========================================================
    # Determine center
    # ========================================================

    def get_center(
        self,
        board,
        values,
    ):

        if values["use_selected"]:

            selection = board.get_selection()

            if len(selection) != 1:

                raise RuntimeError(
                    "Select exactly one PCB item "
                    "to use as the pattern center."
                )

            item = selection[0]

            bbox = board.get_item_bounding_box(
                item
            )

            if bbox is None:

                raise RuntimeError(
                    "The selected item has no "
                    "usable bounding box."
                )

            return Vector2.from_xy(
                int(
                    (
                        bbox.top_left.x
                        + bbox.bottom_right.x
                    ) / 2
                ),
                int(
                    (
                        bbox.top_left.y
                        + bbox.bottom_right.y
                    ) / 2
                ),
            )

        return Vector2.from_xy(
            from_mm(
                values["center_x"]
            ),
            from_mm(
                values["center_y"]
            ),
        )

    # ========================================================
    # Delete generated patterns
    # ========================================================

    def delete_previous_patterns(
        self,
        board,
    ):

        groups = board.get_groups()

        generated_groups = [
            group
            for group in groups
            if group.name.startswith(
                GROUP_PREFIX
            )
        ]

        if not generated_groups:
            return

        items = []

        for group in generated_groups:

            items.extend(
                group.items
            )

        commit = board.begin_commit()

        try:

            if items:
                board.remove_items(
                    items
                )

            board.remove_items(
                generated_groups
            )

            board.push_commit(
                commit,
                "Delete radial patterns",
            )

        except Exception:

            board.drop_commit(
                commit
            )

            raise

    # ========================================================
    # Create segment
    # ========================================================

    def make_segment(
        self,
        board,
        center,
        x1,
        y1,
        x2,
        y2,
        layer,
        width,
    ):

        start = Vector2.from_xy(
            center.x + from_mm(x1),
            center.y + from_mm(y1),
        )

        end = Vector2.from_xy(
            center.x + from_mm(x2),
            center.y + from_mm(y2),
        )

        segment = BoardSegment.from_coords(
            start,
            end,
        )

        segment.layer = layer

        segment.attributes.stroke.width = (
            from_mm(width)
        )

        return segment

    # ========================================================
    # Create pattern
    # ========================================================

    def create_pattern(
        self,
        board,
        center,
        values,
    ):

        copper_layer = (
            board.get_layer_by_name(
                values["copper_layer"]
            )
        )

        if (
            copper_layer
            == BoardLayer.BL_UNDEFINED
        ):
            raise RuntimeError(
                "Invalid copper layer."
            )

        mask_layer = None

        if values["add_mask"]:

            mask_layer = (
                board.get_layer_by_name(
                    values["mask_layer"]
                )
            )

            if (
                mask_layer
                == BoardLayer.BL_UNDEFINED
            ):
                raise RuntimeError(
                    "Invalid mask layer."
                )

        # ----------------------------------------------------
        # Generate geometry
        # ----------------------------------------------------

        lines = generate_radial_lines(
            radius=values["radius"],
            start_angle=values["start_angle"],
            total_angle=values["total_angle"],
            n_lines=values["n_lines"],
            line_length_start=
                values["line_length_start"],
            line_length_end=
                values["line_length_end"],
            density_exp=
                values["density_exp"],
            length_exp=
                values["length_exp"],
        )

        # ----------------------------------------------------
        # Build PCB objects
        # ----------------------------------------------------

        items = []

        for (
            x1,
            y1,
            x2,
            y2,
        ) in lines:

            # Copper
            copper = self.make_segment(
                board,
                center,
                x1,
                y1,
                x2,
                y2,
                copper_layer,
                values["copper_width"],
            )

            items.append(copper)

            # Mask
            if mask_layer is not None:

                mask = self.make_segment(
                    board,
                    center,
                    x1,
                    y1,
                    x2,
                    y2,
                    mask_layer,
                    values["mask_width"],
                )

                items.append(mask)

        # ----------------------------------------------------
        # Commit everything as one operation
        # ----------------------------------------------------

        commit = board.begin_commit()

        try:

            created_items = board.create_items(
                items
            )

            # ------------------------------------------------
            # Group copper + mask together
            # ------------------------------------------------

            group = Group()

            name = (
                values["pattern_name"]
                .strip()
            )

            if not name:
                name = GROUP_PREFIX

            group.name = name

            group.items = created_items

            board.create_items(
                group
            )

            board.push_commit(
                commit,
                "Create radial pattern",
            )

            return group

        except Exception:

            board.drop_commit(
                commit
            )

            raise

    # ========================================================
    # Run
    # ========================================================

    def run(self):

        try:

            board = self.get_board()

        except Exception as exc:

            wx.MessageBox(
                str(exc),
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        dialog = RadialPatternDialog(
            None
        )

        result = dialog.ShowModal()

        if result != wx.ID_OK:

            dialog.Destroy()
            return

        try:

            values = dialog.get_values()

        except ValueError:

            dialog.Destroy()

            wx.MessageBox(
                "Please enter valid numeric values.",
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        dialog.Destroy()

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if values["radius"] < 0:

            wx.MessageBox(
                "Inner radius must be >= 0.",
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        if values["n_lines"] < 1:

            wx.MessageBox(
                "Number of lines must be >= 1.",
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        if values["copper_width"] <= 0:

            wx.MessageBox(
                "Copper line width must be > 0.",
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        if (
            values["add_mask"]
            and values["mask_width"] <= 0
        ):

            wx.MessageBox(
                "Mask line width must be > 0.",
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        # ----------------------------------------------------
        # Center
        # ----------------------------------------------------

        try:

            center = self.get_center(
                board,
                values,
            )

        except Exception as exc:

            wx.MessageBox(
                str(exc),
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        # ----------------------------------------------------
        # Delete previous patterns
        # ----------------------------------------------------

        if values["delete_previous"]:

            try:

                self.delete_previous_patterns(
                    board
                )

            except Exception as exc:

                wx.MessageBox(
                    "Could not delete previous "
                    "radial patterns:\n\n"
                    + str(exc),
                    PLUGIN_NAME,
                    wx.OK | wx.ICON_ERROR,
                )

                return

        # ----------------------------------------------------
        # Create
        # ----------------------------------------------------

        try:

            group = self.create_pattern(
                board,
                center,
                values,
            )

        except Exception as exc:

            wx.MessageBox(
                "Could not create radial pattern:\n\n"
                + str(exc),
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        # ----------------------------------------------------
        # Select generated geometry
        # ----------------------------------------------------

        try:

            board.clear_selection()

            board.add_to_selection(
                group
            )

        except Exception:
            pass

        wx.MessageBox(
            "Radial pattern created.",
            PLUGIN_NAME,
            wx.OK | wx.ICON_INFORMATION,
        )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    app = wx.App()

    try:

        plugin = RadialPatternPlugin()
        plugin.run()

    finally:

        app.Destroy()

