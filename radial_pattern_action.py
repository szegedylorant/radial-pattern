import math

import wx

from kipy import KiCad
from kipy.board_types import BoardLayer, BoardSegment, Group
from kipy.geometry import Vector2
from kipy.util import from_mm


PLUGIN_NAME = "Radial Pattern"
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
    Generate radial line geometry.

    All dimensions are in mm.
    Angles are in degrees.

    Returns:
        list of (x1, y1, x2, y2)
    """

    if n_lines < 1:
        return []

    lines = []

    for i in range(n_lines):

        if n_lines == 1:
            t = 0.0
        else:
            t = i / (n_lines - 1)

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
# UI helper
# ============================================================

def add_field(
    sizer,
    panel,
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

    sizer.Add(
        row,
        0,
        wx.EXPAND
        | wx.BOTTOM,
        6,
    )

    return field


# ============================================================
# Dialog
# ============================================================

class RadialPatternDialog(wx.Dialog):

    def __init__(self, parent):

        super().__init__(
            parent,
            title=PLUGIN_NAME,
        )

        self.SetMinSize(
            wx.Size(520, 650)
        )

        # ----------------------------------------------------
        # Outer layout
        # ----------------------------------------------------

        outer = wx.BoxSizer(
            wx.VERTICAL
        )

        # ----------------------------------------------------
        # Scrolled content
        # ----------------------------------------------------

        scrolled = wx.ScrolledWindow(
            self,
            style=wx.VSCROLL
            | wx.HSCROLL,
        )

        scrolled.SetScrollRate(
            10,
            10,
        )

        content = wx.BoxSizer(
            wx.VERTICAL
        )

        self.content = content
        self.scrolled = scrolled

        # ====================================================
        # Center
        # ====================================================

        center_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            scrolled,
            "Pattern Center",
        )

        self.center_selected = wx.RadioButton(
            scrolled,
            label="Use center of selected item",
            style=wx.RB_GROUP,
        )

        self.center_coordinates = wx.RadioButton(
            scrolled,
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

        xy_row = wx.BoxSizer(
            wx.HORIZONTAL
        )

        xy_row.Add(
            wx.StaticText(
                scrolled,
                label="X (mm):",
            ),
            0,
            wx.ALIGN_CENTER_VERTICAL
            | wx.RIGHT,
            5,
        )

        self.center_x = wx.TextCtrl(
            scrolled,
            value="0",
        )

        xy_row.Add(
            self.center_x,
            1,
            wx.RIGHT,
            15,
        )

        xy_row.Add(
            wx.StaticText(
                scrolled,
                label="Y (mm):",
            ),
            0,
            wx.ALIGN_CENTER_VERTICAL
            | wx.RIGHT,
            5,
        )

        self.center_y = wx.TextCtrl(
            scrolled,
            value="0",
        )

        xy_row.Add(
            self.center_y,
            1,
        )

        center_box.Add(
            xy_row,
            0,
            wx.EXPAND
            | wx.ALL,
            5,
        )

        content.Add(
            center_box,
            0,
            wx.EXPAND
            | wx.ALL,
            10,
        )

        # ====================================================
        # Geometry
        # ====================================================

        geometry_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            scrolled,
            "Geometry",
        )

        self.radius = add_field(
            geometry_box,
            scrolled,
            "Inner radius (mm):",
            35,
        )

        self.start_angle = add_field(
            geometry_box,
            scrolled,
            "Start angle (deg):",
            -60,
        )

        self.total_angle = add_field(
            geometry_box,
            scrolled,
            "Total angle (deg):",
            300,
        )

        self.n_lines = add_field(
            geometry_box,
            scrolled,
            "Number of lines:",
            45,
        )

        self.length_start = add_field(
            geometry_box,
            scrolled,
            "Line length start (mm):",
            1,
        )

        self.length_end = add_field(
            geometry_box,
            scrolled,
            "Line length end (mm):",
            11,
        )

        self.density_exp = add_field(
            geometry_box,
            scrolled,
            "Density exponent:",
            5,
        )

        self.length_exp = add_field(
            geometry_box,
            scrolled,
            "Length exponent:",
            3,
        )

        content.Add(
            geometry_box,
            0,
            wx.EXPAND
            | wx.LEFT
            | wx.RIGHT
            | wx.BOTTOM,
            10,
        )

        # ====================================================
        # Copper
        # ====================================================

        copper_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            scrolled,
            "Copper",
        )

        copper_row = wx.BoxSizer(
            wx.HORIZONTAL
        )

        copper_row.Add(
            wx.StaticText(
                scrolled,
                label="Layer:",
            ),
            1,
            wx.ALIGN_CENTER_VERTICAL
            | wx.RIGHT,
            10,
        )

        self.copper_layer = wx.Choice(
            scrolled,
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
            wx.EXPAND
            | wx.BOTTOM,
            6,
        )

        self.copper_width = add_field(
            copper_box,
            scrolled,
            "Line width (mm):",
            0.5,
        )

        content.Add(
            copper_box,
            0,
            wx.EXPAND
            | wx.LEFT
            | wx.RIGHT
            | wx.BOTTOM,
            10,
        )

        # ====================================================
        # Solder Mask
        # ====================================================

        mask_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            scrolled,
            "Solder Mask",
        )

        self.add_mask = wx.CheckBox(
            scrolled,
            label="Add corresponding solder-mask layer",
        )

        self.add_mask.SetValue(False)

        mask_box.Add(
            self.add_mask,
            0,
            wx.BOTTOM,
            8,
        )

        mask_layer_row = wx.BoxSizer(
            wx.HORIZONTAL
        )

        mask_layer_row.Add(
            wx.StaticText(
                scrolled,
                label="Mask layer:",
            ),
            1,
            wx.ALIGN_CENTER_VERTICAL
            | wx.RIGHT,
            10,
        )

        self.mask_layer = wx.Choice(
            scrolled,
            choices=[
                "F.Mask",
                "B.Mask",
            ],
        )

        self.mask_layer.SetSelection(0)

        mask_layer_row.Add(
            self.mask_layer,
            1,
        )

        mask_box.Add(
            mask_layer_row,
            0,
            wx.EXPAND
            | wx.BOTTOM,
            6,
        )

        self.mask_width = add_field(
            mask_box,
            scrolled,
            "Mask line width (mm):",
            0.6,
        )

        content.Add(
            mask_box,
            0,
            wx.EXPAND
            | wx.LEFT
            | wx.RIGHT
            | wx.BOTTOM,
            10,
        )

        # ====================================================
        # Pattern options
        # ====================================================

        options_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            scrolled,
            "Pattern",
        )

        self.pattern_name = add_field(
            options_box,
            scrolled,
            "Pattern name:",
            "Radial Pattern",
        )

        self.delete_previous = wx.CheckBox(
            scrolled,
            label="Delete previous generated patterns",
        )

        options_box.Add(
            self.delete_previous,
            0,
            wx.TOP,
            4,
        )

        content.Add(
            options_box,
            0,
            wx.EXPAND
            | wx.LEFT
            | wx.RIGHT
            | wx.BOTTOM,
            10,
        )

        # ----------------------------------------------------
        # Finish scrolled content
        # ----------------------------------------------------

        scrolled.SetSizer(content)

        # ====================================================
        # Bottom buttons
        # ====================================================

        button_sizer = wx.StdDialogButtonSizer()

        self.generate_button = wx.Button(
            self,
            wx.ID_OK,
            "Generate",
        )

        self.cancel_button = wx.Button(
            self,
            wx.ID_CANCEL,
            "Cancel",
        )

        button_sizer.AddButton(
            self.generate_button
        )

        button_sizer.AddButton(
            self.cancel_button
        )

        button_sizer.Realize()

        outer.Add(
            scrolled,
            1,
            wx.EXPAND
            | wx.LEFT
            | wx.RIGHT
            | wx.TOP,
            8,
        )

        outer.Add(
            button_sizer,
            0,
            wx.EXPAND
            | wx.ALL,
            10,
        )

        self.SetSizer(outer)

        # ----------------------------------------------------
        # Events
        # ----------------------------------------------------

        self.copper_layer.Bind(
            wx.EVT_CHOICE,
            self.on_copper_layer_changed,
        )

        self.add_mask.Bind(
            wx.EVT_CHECKBOX,
            self.on_mask_checkbox,
        )

        # ----------------------------------------------------
        # Initial state
        # ----------------------------------------------------

        self.mask_layer.Enable(False)
        self.mask_width.Enable(False)

        # ----------------------------------------------------
        # Fit
        # ----------------------------------------------------

        self.Layout()

        self.SetSize(
            wx.Size(520, 720)
        )

        self.Centre()

        # Make sure the default button works.
        self.generate_button.SetDefault()

    # ========================================================
    # Copper / mask
    # ========================================================

    def on_copper_layer_changed(
        self,
        event,
    ):

        copper = (
            self.copper_layer
            .GetStringSelection()
        )

        if copper == "F.Cu":

            self.mask_layer.SetStringSelection(
                "F.Mask"
            )

        else:

            self.mask_layer.SetStringSelection(
                "B.Mask"
            )

        event.Skip()

    def on_mask_checkbox(
        self,
        event,
    ):

        enabled = (
            self.add_mask.GetValue()
        )

        self.mask_layer.Enable(
            enabled
        )

        self.mask_width.Enable(
            enabled
        )

        event.Skip()

    # ========================================================
    # Get values
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
                self.delete_previous.GetValue(),

            "use_selected":
                self.center_selected.GetValue(),

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
# Plugin
# ============================================================

class RadialPatternPlugin:

    def __init__(self):

        self.kicad = KiCad(
            client_name="radial-pattern"
        )

    # ========================================================
    # Board
    # ========================================================

    def get_board(self):

        board = self.kicad.get_board()

        if board is None:
            raise RuntimeError(
                "No PCB is currently open."
            )

        return board

    # ========================================================
    # Center
    # ========================================================

    def get_center(
        self,
        board,
        values,
    ):

        if values["use_selected"]:

            try:
                selection = (
                    board.get_selection()
                )
            except Exception as exc:
                raise RuntimeError(
                    "Could not read the current "
                    "PCB selection:\n\n"
                    + str(exc)
                )

            if len(selection) != 1:

                raise RuntimeError(
                    "Select exactly one PCB item "
                    "to use as the pattern center."
                )

            item = selection[0]

            bbox = (
                board.get_item_bounding_box(
                    item
                )
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
    # Create one PCB graphic segment
    # ========================================================

    @staticmethod
    def make_segment(
        center,
        x1,
        y1,
        x2,
        y2,
        layer,
        width,
    ):
        """
        Create a native KiCad graphic segment.

        Coordinates are relative to center and in mm.
        """

        segment = BoardSegment()

        segment.start = Vector2.from_xy(
            center.x + from_mm(x1),
            center.y + from_mm(y1),
        )

        segment.end = Vector2.from_xy(
            center.x + from_mm(x2),
            center.y + from_mm(y2),
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
                "Could not resolve copper layer "
                f"{values['copper_layer']}."
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
                    "Could not resolve mask layer "
                    f"{values['mask_layer']}."
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

        items = []

        # ----------------------------------------------------
        # Copper
        # ----------------------------------------------------

        for (
            x1,
            y1,
            x2,
            y2,
        ) in lines:

            segment = self.make_segment(
                center,
                x1,
                y1,
                x2,
                y2,
                copper_layer,
                values["copper_width"],
            )

            items.append(segment)

        # ----------------------------------------------------
        # Mask
        # ----------------------------------------------------

        if mask_layer is not None:

            for (
                x1,
                y1,
                x2,
                y2,
            ) in lines:

                segment = self.make_segment(
                    center,
                    x1,
                    y1,
                    x2,
                    y2,
                    mask_layer,
                    values["mask_width"],
                )

                items.append(segment)

        if not items:

            raise RuntimeError(
                "No geometry was generated."
            )

        # ----------------------------------------------------
        # One undo operation
        # ----------------------------------------------------

        commit = board.begin_commit()

        try:

            created_items = (
                board.create_items(items)
            )

            board.push_commit(
                commit,
                "Create radial pattern",
            )

            return created_items

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

        try:

            result = dialog.ShowModal()

            if result != wx.ID_OK:
                return

            try:

                values = dialog.get_values()

            except ValueError:

                wx.MessageBox(
                    "Please enter valid numeric "
                    "values.",
                    PLUGIN_NAME,
                    wx.OK | wx.ICON_ERROR,
                )

                return

        finally:

            dialog.Destroy()

        # ====================================================
        # Validation
        # ====================================================

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

        if values["line_length_start"] < 0:

            wx.MessageBox(
                "Starting line length must be >= 0.",
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        if values["line_length_end"] < 0:

            wx.MessageBox(
                "Ending line length must be >= 0.",
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

        # ====================================================
        # Validate mask pairing
        # ====================================================

        if values["add_mask"]:

            expected_mask = (
                "F.Mask"
                if values["copper_layer"] == "F.Cu"
                else "B.Mask"
            )

            if values["mask_layer"] != expected_mask:

                answer = wx.MessageBox(
                    "The selected mask layer does not "
                    "match the selected copper layer.\n\n"
                    f"Copper: {values['copper_layer']}\n"
                    f"Mask:   {values['mask_layer']}\n\n"
                    f"Expected: {expected_mask}\n\n"
                    "Continue anyway?",
                    PLUGIN_NAME,
                    wx.YES_NO | wx.ICON_WARNING,
                )

                if answer != wx.YES:

                    return

        # ====================================================
        # Center
        # ====================================================

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

        # ====================================================
        # Generate
        # ====================================================

        try:

            created_items = (
                self.create_pattern(
                    board,
                    center,
                    values,
                )
            )

        except Exception as exc:

            wx.MessageBox(
                "Could not create radial pattern:\n\n"
                + str(exc),
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        # ====================================================
        # Select generated geometry
        # ====================================================

        try:

            board.clear_selection()

            board.add_to_selection(
                created_items
            )

        except Exception:
            pass

        # ====================================================
        # Done
        # ====================================================

        mask_text = (
            f"\nMask: {values['mask_layer']} "
            f"({values['mask_width']:.3f} mm)"
            if values["add_mask"]
            else ""
        )

        wx.MessageBox(
            "Radial pattern created.\n\n"
            f"Copper: {values['copper_layer']} "
            f"({values['copper_width']:.3f} mm)"
            f"{mask_text}",
            PLUGIN_NAME,
            wx.OK | wx.ICON_INFORMATION,
        )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    app = wx.App(False)

    try:

        plugin = RadialPatternPlugin()
        plugin.run()

    except Exception as exc:

        wx.MessageBox(
            "Unexpected plugin error:\n\n"
            + str(exc),
            PLUGIN_NAME,
            wx.OK | wx.ICON_ERROR,
        )

    finally:

        app.Destroy()

