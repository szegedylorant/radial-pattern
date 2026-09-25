import math

import wx

from kipy import KiCad
from kipy.board_types import BoardLayer, BoardSegment, BoardArc
from kipy.geometry import Vector2
from kipy.util import from_mm


PLUGIN_NAME = "Radial Pattern"

CONFIG = wx.Config("radial-pattern")


# ============================================================
# Persistent configuration
# ============================================================

def config_get(key, default):
    return CONFIG.Read(key, str(default))


def config_get_bool(key, default):
    return CONFIG.ReadBool(key, default)


def config_set(key, value):
    CONFIG.Write(key, str(value))


def config_set_bool(key, value):
    CONFIG.WriteBool(key, value)


# ============================================================
# Layer definitions
# ============================================================

OUTPUT_LAYERS = [
    "F.Cu",
    "B.Cu",
    "F.Mask",
    "B.Mask",
    "F.Silkscreen",
    "B.Silkscreen",
]

COPPER_LAYERS = {
    "F.Cu",
    "B.Cu",
}

MASK_FOR_COPPER = {
    "F.Cu": "F.Mask",
    "B.Cu": "B.Mask",
}

USER_COMMENTS_LAYER = "User.Comments"

CIRCLE_WIDTH_MM = 0.15


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
        # Density interpolation
        # ----------------------------------------------------

        if density_exp == 0:

            t_density = t

        else:

            denominator = (
                math.exp(density_exp) - 1.0
            )

            if abs(denominator) < 1e-15:
                t_density = t
            else:
                t_density = (
                    math.exp(
                        density_exp * t
                    ) - 1.0
                ) / denominator

        # ----------------------------------------------------
        # Angle
        # ----------------------------------------------------

        angle_deg = (
            start_angle
            + total_angle * t_density
        )

        angle = math.radians(
            angle_deg
        )

        # ----------------------------------------------------
        # Length interpolation
        # ----------------------------------------------------

        if length_exp == 0:

            t_length = t

        else:

            denominator = (
                math.exp(length_exp) - 1.0
            )

            if abs(denominator) < 1e-15:
                t_length = t
            else:
                t_length = (
                    math.exp(
                        length_exp * t
                    ) - 1.0
                ) / denominator

        length = (
            line_length_start
            + (
                line_length_end
                - line_length_start
            )
            * t_length
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
            (
                x1,
                y1,
                x2,
                y2,
            )
        )

    return lines


# ============================================================
# UI helpers
# ============================================================

def add_field(
    sizer,
    parent,
    label,
    value,
):
    row = wx.BoxSizer(
        wx.HORIZONTAL
    )

    row.Add(
        wx.StaticText(
            parent,
            label=label,
        ),
        1,
        wx.ALIGN_CENTER_VERTICAL
        | wx.RIGHT,
        10,
    )

    field = wx.TextCtrl(
        parent,
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
            wx.Size(540, 760)
        )

        outer = wx.BoxSizer(
            wx.VERTICAL
        )

        # ====================================================
        # Scrollable content
        # ====================================================

        scrolled = wx.ScrolledWindow(
            self,
            style=wx.VSCROLL,
        )

        scrolled.SetScrollRate(
            10,
            10,
        )

        content = wx.BoxSizer(
            wx.VERTICAL
        )

        # ====================================================
        # Pattern center
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

        use_selected = config_get_bool(
            "use_selected",
            True,
        )

        if use_selected:
            self.center_selected.SetValue(
                True
            )
        else:
            self.center_coordinates.SetValue(
                True
            )

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
            value=config_get(
                "center_x",
                0,
            ),
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
            value=config_get(
                "center_y",
                0,
            ),
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
            config_get(
                "radius",
                3.6,
            ),
        )

        self.start_angle = add_field(
            geometry_box,
            scrolled,
            "Start angle (deg):",
            config_get(
                "start_angle",
                120,
            ),
        )

        self.total_angle = add_field(
            geometry_box,
            scrolled,
            "Total angle (deg):",
            config_get(
                "total_angle",
                300,
            ),
        )

        self.n_lines = add_field(
            geometry_box,
            scrolled,
            "Number of lines:",
            config_get(
                "n_lines",
                45,
            ),
        )

        self.length_start = add_field(
            geometry_box,
            scrolled,
            "Line length start (mm):",
            config_get(
                "line_length_start",
                2.5,
            ),
        )

        self.length_end = add_field(
            geometry_box,
            scrolled,
            "Line length end (mm):",
            config_get(
                "line_length_end",
                0.3,
            ),
        )

        self.density_exp = add_field(
            geometry_box,
            scrolled,
            "Density exponent:",
            config_get(
                "density_exp",
                -5,
            ),
        )

        self.length_exp = add_field(
            geometry_box,
            scrolled,
            "Length exponent:",
            config_get(
                "length_exp",
                -3,
            ),
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
        # Output layer
        # ====================================================

        output_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            scrolled,
            "Output Layer",
        )

        layer_row = wx.BoxSizer(
            wx.HORIZONTAL
        )

        layer_row.Add(
            wx.StaticText(
                scrolled,
                label="Layer:",
            ),
            1,
            wx.ALIGN_CENTER_VERTICAL
            | wx.RIGHT,
            10,
        )

        self.output_layer = wx.Choice(
            scrolled,
            choices=OUTPUT_LAYERS,
        )

        saved_layer = config_get(
            "output_layer",
            "F.Cu",
        )

        if saved_layer in OUTPUT_LAYERS:
            self.output_layer.SetStringSelection(
                saved_layer
            )
        else:
            self.output_layer.SetSelection(
                0
            )

        layer_row.Add(
            self.output_layer,
            1,
        )

        output_box.Add(
            layer_row,
            0,
            wx.EXPAND
            | wx.BOTTOM,
            6,
        )

        self.output_width = add_field(
            output_box,
            scrolled,
            "Line width (mm):",
            config_get(
                "output_width",
                0.3,
            ),
        )

        # ====================================================
        # Optional mask
        # ====================================================

        mask_box = wx.StaticBoxSizer(
            wx.VERTICAL,
            scrolled,
            "Additional Solder Mask",
        )

        self.add_mask = wx.CheckBox(
            scrolled,
            label="Also generate solder mask",
        )

        self.add_mask.SetValue(
            config_get_bool(
                "add_mask",
                False,
            )
        )

        mask_box.Add(
            self.add_mask,
            0,
            wx.BOTTOM,
            6,
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

        saved_mask = config_get(
            "mask_layer",
            "F.Mask",
        )

        if saved_mask in (
            "F.Mask",
            "B.Mask",
        ):
            self.mask_layer.SetStringSelection(
                saved_mask
            )

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
            "Mask width (mm):",
            config_get(
                "mask_width",
                0.3,
            ),
        )

        output_box.Add(
            mask_box,
            0,
            wx.EXPAND
            | wx.TOP,
            8,
        )

        content.Add(
            output_box,
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
            config_get(
                "pattern_name",
                "Radial Pattern",
            ),
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

        scrolled.SetSizer(
            content
        )

        outer.Add(
            scrolled,
            1,
            wx.EXPAND
            | wx.LEFT
            | wx.RIGHT
            | wx.TOP,
            8,
        )

        # ====================================================
        # Buttons
        # ====================================================

        button_sizer = (
            wx.StdDialogButtonSizer()
        )

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
            button_sizer,
            0,
            wx.EXPAND
            | wx.ALL,
            10,
        )

        self.SetSizer(
            outer
        )

        # ====================================================
        # Events
        # ====================================================

        self.output_layer.Bind(
            wx.EVT_CHOICE,
            self.on_layer_changed,
        )

        self.add_mask.Bind(
            wx.EVT_CHECKBOX,
            self.on_mask_changed,
        )

        self.update_layer_controls()

        self.generate_button.SetDefault()

        self.SetSize(
            wx.Size(540, 760)
        )

        self.Centre()

    # ========================================================
    # Layer changed
    # ========================================================

    def on_layer_changed(
        self,
        event,
    ):

        layer = (
            self.output_layer
            .GetStringSelection()
        )

        if layer == "F.Cu":

            self.mask_layer.SetStringSelection(
                "F.Mask"
            )

        elif layer == "B.Cu":

            self.mask_layer.SetStringSelection(
                "B.Mask"
            )

        self.update_layer_controls()

        event.Skip()

    # ========================================================
    # Mask checkbox
    # ========================================================

    def on_mask_changed(
        self,
        event,
    ):

        self.update_layer_controls()

        event.Skip()

    # ========================================================
    # Layer controls
    # ========================================================

    def update_layer_controls(
        self
    ):

        layer = (
            self.output_layer
            .GetStringSelection()
        )

        is_copper = (
            layer in COPPER_LAYERS
        )

        self.add_mask.Enable(
            is_copper
        )

        mask_enabled = (
            is_copper
            and self.add_mask.GetValue()
        )

        self.mask_layer.Enable(
            mask_enabled
        )

        self.mask_width.Enable(
            mask_enabled
        )

        if not is_copper:

            self.add_mask.SetValue(
                False
            )

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

            "output_layer":
                self.output_layer
                .GetStringSelection(),

            "output_width":
                float(
                    self.output_width.GetValue()
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

    # ========================================================
    # Save values
    # ========================================================

    def save_values(self):

        values = self.get_values()

        config_set(
            "radius",
            values["radius"],
        )

        config_set(
            "start_angle",
            values["start_angle"],
        )

        config_set(
            "total_angle",
            values["total_angle"],
        )

        config_set(
            "n_lines",
            values["n_lines"],
        )

        config_set(
            "line_length_start",
            values["line_length_start"],
        )

        config_set(
            "line_length_end",
            values["line_length_end"],
        )

        config_set(
            "density_exp",
            values["density_exp"],
        )

        config_set(
            "length_exp",
            values["length_exp"],
        )

        config_set(
            "output_layer",
            values["output_layer"],
        )

        config_set(
            "output_width",
            values["output_width"],
        )

        config_set_bool(
            "add_mask",
            values["add_mask"],
        )

        config_set(
            "mask_layer",
            values["mask_layer"],
        )

        config_set(
            "mask_width",
            values["mask_width"],
        )

        config_set(
            "pattern_name",
            values["pattern_name"],
        )

        config_set_bool(
            "use_selected",
            values["use_selected"],
        )

        config_set(
            "center_x",
            values["center_x"],
        )

        config_set(
            "center_y",
            values["center_y"],
        )

        CONFIG.Flush()


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

        if not values["use_selected"]:

            return Vector2.from_xy(
                from_mm(
                    values["center_x"]
                ),
                from_mm(
                    values["center_y"]
                ),
            )

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

        position = getattr(
            item,
            "position",
            None,
        )

        if position is not None:
            return position

        center = getattr(
            item,
            "center",
            None,
        )

        if center is not None:
            return center

        try:

            bbox = (
                board.get_item_bounding_box(
                    item
                )
            )

        except Exception:

            bbox = None

        if bbox is not None:

            min_point = getattr(
                bbox,
                "min",
                None,
            )

            max_point = getattr(
                bbox,
                "max",
                None,
            )

            if (
                min_point is not None
                and max_point is not None
            ):

                return Vector2.from_xy(
                    int(
                        (
                            min_point.x
                            + max_point.x
                        ) / 2
                    ),
                    int(
                        (
                            min_point.y
                            + max_point.y
                        ) / 2
                    ),
                )

        raise RuntimeError(
            "The selected item does not expose "
            "a usable position or center."
        )

    # ========================================================
    # Resolve layer
    # ========================================================

    @staticmethod
    def resolve_layer(
        board,
        layer_name,
    ):

        layer = (
            board.get_layer_by_name(
                layer_name
            )
        )

        if (
            layer == BoardLayer.BL_UNDEFINED
        ):

            raise RuntimeError(
                "Could not resolve PCB layer "
                f"'{layer_name}'."
            )

        return layer

    # ========================================================
    # Segment
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
    # Circle
    # ========================================================

    @staticmethod
    def make_circle(
        center,
        radius_mm,
        layer,
    ):
        """
        Create a full circle on User.Comments.

        The circle is represented as a BoardArc.
        """

        circle = BoardArc()

        radius = from_mm(
            radius_mm
        )

        center_point = Vector2.from_xy(
            center.x,
            center.y,
        )

        start_point = Vector2.from_xy(
            center.x + radius,
            center.y,
        )

        circle.center = center_point

        circle.start = start_point

        circle.mid = Vector2.from_xy(
            center.x - radius,
            center.y,
        )

        circle.end = start_point

        circle.layer = layer

        circle.attributes.stroke.width = (
            from_mm(CIRCLE_WIDTH_MM)
        )

        return circle

    # ========================================================
    # Create pattern
    # ========================================================

    def create_pattern(
        self,
        board,
        center,
        values,
    ):

        output_layer_name = (
            values["output_layer"]
        )

        output_layer = self.resolve_layer(
            board,
            output_layer_name,
        )

        # ----------------------------------------------------
        # Optional mask
        # ----------------------------------------------------

        add_mask = (
            values["add_mask"]
            and output_layer_name
            in COPPER_LAYERS
        )

        mask_layer = None

        if add_mask:

            mask_layer_name = (
                values["mask_layer"]
            )

            expected_mask = (
                MASK_FOR_COPPER[
                    output_layer_name
                ]
            )

            if (
                mask_layer_name
                != expected_mask
            ):

                raise RuntimeError(
                    f"{output_layer_name} requires "
                    f"{expected_mask} as its "
                    "additional mask layer."
                )

            mask_layer = (
                self.resolve_layer(
                    board,
                    mask_layer_name,
                )
            )

        # ----------------------------------------------------
        # User.Comments layer
        # ----------------------------------------------------

        comments_layer = (
            self.resolve_layer(
                board,
                USER_COMMENTS_LAYER,
            )
        )

        # ----------------------------------------------------
        # Generate radial lines
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

        if not lines:

            raise RuntimeError(
                "No geometry was generated."
            )

        items = []

        # ----------------------------------------------------
        # Primary layer
        # ----------------------------------------------------

        for (
            x1,
            y1,
            x2,
            y2,
        ) in lines:

            items.append(
                self.make_segment(
                    center,
                    x1,
                    y1,
                    x2,
                    y2,
                    output_layer,
                    values["output_width"],
                )
            )

        # ----------------------------------------------------
        # Optional mask
        # ----------------------------------------------------

        if mask_layer is not None:

            for (
                x1,
                y1,
                x2,
                y2,
            ) in lines:

                items.append(
                    self.make_segment(
                        center,
                        x1,
                        y1,
                        x2,
                        y2,
                        mask_layer,
                        values["mask_width"],
                    )
                )

        # ----------------------------------------------------
        # Reference circle
        #
        # radius =
        # inner radius
        # + longest line length
        # + 1 mm
        # ----------------------------------------------------

        longest_line = max(
            values["line_length_start"],
            values["line_length_end"],
        )

        circle_radius = (
            values["radius"]
            + longest_line
            + 1.0
        )

        circle = self.make_circle(
            center,
            circle_radius,
            comments_layer,
        )

        items.append(
            circle
        )

        # ----------------------------------------------------
        # Create board objects
        # ----------------------------------------------------

        commit = board.begin_commit()

        try:

            created_items = (
                board.create_items(
                    items
                )
            )

            if not created_items:

                raise RuntimeError(
                    "KiCad did not create any "
                    "radial-pattern items."
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

                dialog.save_values()

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
                "Starting line length must "
                "be >= 0.",
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        if values["line_length_end"] < 0:

            wx.MessageBox(
                "Ending line length must "
                "be >= 0.",
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        if values["output_width"] <= 0:

            wx.MessageBox(
                "Line width must be > 0.",
                PLUGIN_NAME,
                wx.OK | wx.ICON_ERROR,
            )

            return

        # ----------------------------------------------------
        # Mask validation
        # ----------------------------------------------------

        if (
            values["add_mask"]
            and values["output_layer"]
            in COPPER_LAYERS
        ):

            if values["mask_width"] <= 0:

                wx.MessageBox(
                    "Mask width must be > 0.",
                    PLUGIN_NAME,
                    wx.OK | wx.ICON_ERROR,
                )

                return

            expected_mask = (
                MASK_FOR_COPPER[
                    values["output_layer"]
                ]
            )

            if (
                values["mask_layer"]
                != expected_mask
            ):

                wx.MessageBox(
                    f"{values['output_layer']} "
                    f"must use {expected_mask} "
                    "as its additional mask layer.",
                    PLUGIN_NAME,
                    wx.OK | wx.ICON_ERROR,
                )

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
        # Create
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
        # Select all generated objects
        # ====================================================

        try:

            board.clear_selection()

            board.add_to_selection(
                created_items
            )

        except Exception:

            pass

        # ====================================================
        # Success information
        # ====================================================

        longest_line = max(
            values["line_length_start"],
            values["line_length_end"],
        )

        circle_radius = (
            values["radius"]
            + longest_line
            + 1.0
        )

        output_text = (
            f"Layer: "
            f"{values['output_layer']}"
            f"\nLine width: "
            f"{values['output_width']:.3f} mm"
            f"\nReference circle: "
            f"{circle_radius:.3f} mm"
            f"\nReference layer: "
            f"{USER_COMMENTS_LAYER}"
        )

        if (
            values["add_mask"]
            and values["output_layer"]
            in COPPER_LAYERS
        ):

            output_text += (
                f"\nMask: "
                f"{values['mask_layer']}"
                f"\nMask width: "
                f"{values['mask_width']:.3f} mm"
            )

        wx.MessageBox(
            "Radial pattern created.\n\n"
            + output_text,
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

