import math

import wx

from kipy import KiCad
from kipy.board_types import (
    BoardLayer,
    BoardSegment,
    Group,
)
from kipy.geometry import Vector2
from kipy.util import from_mm


PLUGIN_NAME = "Radial Pattern"

# ============================================================
# Persistent configuration
# ============================================================

CONFIG = wx.Config("radial-pattern")


def config_get(key, default):
    return CONFIG.Read(
        key,
        str(default),
    )


def config_get_bool(key, default):
    return CONFIG.ReadBool(
        key,
        default,
    )


def config_set(key, value):
    CONFIG.Write(
        key,
        str(value),
    )


def config_set_bool(key, value):
    CONFIG.WriteBool(
        key,
        value,
    )


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
    reverse_direction=False,
):
    """
    Generate radial line geometry.

    All dimensions are in mm.
    Angles are in degrees.

    Normal direction:
        start_angle -> start_angle + total_angle

    Reversed direction:
        start_angle -> start_angle - total_angle
    """

    if n_lines < 1:
        return []

    lines = []

    direction = (
        -1 if reverse_direction else 1
    )

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

            denominator = (
                math.exp(density_exp) - 1.0
            )

            t_density = (
                math.exp(
                    density_exp * t
                ) - 1.0
            ) / denominator

        # ----------------------------------------------------
        # Angular position
        # ----------------------------------------------------

        angle_deg = (
            start_angle
            + direction
            * total_angle
            * t_density
        )

        angle = math.radians(
            angle_deg
        )

        # ----------------------------------------------------
        # Line length
        # ----------------------------------------------------

        if length_exp == 0:

            t_length = t

        else:

            denominator = (
                math.exp(length_exp) - 1.0
            )

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
        # Coordinates
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
            wx.Size(520, 650)
        )

        outer = wx.BoxSizer(
            wx.VERTICAL
        )

        # ----------------------------------------------------
        # Scrollable content
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Remember center mode
        # ----------------------------------------------------

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
                3.7,
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
                285,
            ),
        )

        # ----------------------------------------------------
        # Reverse angular direction
        # ----------------------------------------------------

        self.reverse_direction = wx.CheckBox(
            scrolled,
            label="Reverse angular direction",
        )

        self.reverse_direction.SetValue(
            config_get_bool(
                "reverse_direction",
                False,
            )
        )

        geometry_box.Add(
            self.reverse_direction,
            0,
            wx.TOP
            | wx.BOTTOM,
            4,
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

        self.copper_layer.SetStringSelection(
            config_get(
                "copper_layer",
                "F.Cu",
            )
        )

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
            config_get(
                "copper_width",
                0.3,
            ),
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
        # Solder mask
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

        self.mask_layer.SetStringSelection(
            config_get(
                "mask_layer",
                "F.Mask",
            )
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
            "Mask line width (mm):",
            config_get(
                "mask_width",
                0.3,
            ),
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

        self.copper_layer.Bind(
            wx.EVT_CHOICE,
            self.on_copper_layer_changed,
        )

        self.add_mask.Bind(
            wx.EVT_CHECKBOX,
            self.on_mask_checkbox,
        )

        # ====================================================
        # Initial state
        # ====================================================

        self.update_mask_controls()

        self.generate_button.SetDefault()

        self.SetSize(
            wx.Size(520, 720)
        )

        self.Centre()

    # ========================================================
    # Copper layer changed
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

        self.update_mask_controls()

        event.Skip()

    # ========================================================
    # Mask checkbox
    # ========================================================

    def on_mask_checkbox(
        self,
        event,
    ):

        self.update_mask_controls()

        event.Skip()

    # ========================================================
    # Update mask controls
    # ========================================================

    def update_mask_controls(self):

        enabled = (
            self.add_mask.GetValue()
        )

        self.mask_layer.Enable(
            enabled
        )

        self.mask_width.Enable(
            enabled
        )

    # ========================================================
    # Read values
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

            "reverse_direction":
                self.reverse_direction.GetValue(),

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
                self.pattern_name
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

        config_set_bool(
            "reverse_direction",
            values["reverse_direction"],
        )

        config_set(
            "copper_layer",
            values["copper_layer"],
        )

        config_set(
            "copper_width",
            values["copper_width"],
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
    # Get board
    # ========================================================

    def get_board(self):

        board = (
            self.kicad.get_board()
        )

        if board is None:

            raise RuntimeError(
                "No PCB is currently open."
            )

        return board

    # ========================================================
    # Get pattern center
    # ========================================================

    def get_center(
        self,
        board,
        values,
    ):

        # ----------------------------------------------------
        # Explicit coordinates
        # ----------------------------------------------------

        if not values["use_selected"]:

            return Vector2.from_xy(
                from_mm(
                    values["center_x"]
                ),
                from_mm(
                    values["center_y"]
                ),
            )

        # ----------------------------------------------------
        # Selected item
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Position
        # ----------------------------------------------------

        position = getattr(
            item,
            "position",
            None,
        )

        if position is not None:

            return position

        # ----------------------------------------------------
        # Center
        # ----------------------------------------------------

        center = getattr(
            item,
            "center",
            None,
        )

        if center is not None:

            return center

        # ----------------------------------------------------
        # Bounding box
        #
        # Box2 does not have top_left.
        # ----------------------------------------------------

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
    # Make segment
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
            center.x
            + from_mm(x1),
            center.y
            + from_mm(y1),
        )

        segment.end = Vector2.from_xy(
            center.x
            + from_mm(x2),
            center.y
            + from_mm(y2),
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

        # ----------------------------------------------------
        # Copper layer
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Mask layer
        # ----------------------------------------------------

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
            reverse_direction=
                values["reverse_direction"],
        )

        if not lines:

            raise RuntimeError(
                "No geometry was generated."
            )

        items = []

        # ----------------------------------------------------
        # Copper segments
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

            items.append(
                segment
            )

        # ----------------------------------------------------
        # Mask segments
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

                items.append(
                    segment
                )

        # ----------------------------------------------------
        # One undo transaction
        # ----------------------------------------------------

        commit = board.begin_commit()

        try:

            # ------------------------------------------------
            # Create segments first.
            # ------------------------------------------------

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

            # ------------------------------------------------
            # Create group.
            #
            # Group.name has no setter in the Python
            # wrapper, therefore use group.proto.name.
            # ------------------------------------------------

            group = Group()

            group.proto.name = (
                values["pattern_name"]
            )

            # The Group.items property converts the
            # BoardItem objects into their KIIDs.
            group.items = created_items

            # ------------------------------------------------
            # Add group to board.
            # ------------------------------------------------

            created_groups = (
                board.create_items(
                    group
                )
            )

            if not created_groups:

                raise RuntimeError(
                    "KiCad did not create the "
                    "radial-pattern group."
                )

            created_group = (
                created_groups[0]
            )

            # ------------------------------------------------
            # Commit.
            # ------------------------------------------------

            board.push_commit(
                commit,
                "Create radial pattern",
            )

            return (
                created_items,
                created_group,
            )

        except Exception:

            board.drop_commit(
                commit
            )

            raise

    # ========================================================
    # Run
    # ========================================================

    def run(self):

        # ----------------------------------------------------
        # Get board
        # ----------------------------------------------------

        try:

            board = self.get_board()

        except Exception as exc:

            wx.MessageBox(
                str(exc),
                PLUGIN_NAME,
                wx.OK
                | wx.ICON_ERROR,
            )

            return

        # ----------------------------------------------------
        # Dialog
        # ----------------------------------------------------

        dialog = RadialPatternDialog(
            None
        )

        try:

            result = (
                dialog.ShowModal()
            )

            if result != wx.ID_OK:

                return

            try:

                values = (
                    dialog.get_values()
                )

                # ------------------------------------------------
                # Save immediately when Generate is pressed.
                # ------------------------------------------------

                dialog.save_values()

            except ValueError:

                wx.MessageBox(
                    "Please enter valid numeric "
                    "values.",
                    PLUGIN_NAME,
                    wx.OK
                    | wx.ICON_ERROR,
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
                wx.OK
                | wx.ICON_ERROR,
            )

            return

        if values["n_lines"] < 1:

            wx.MessageBox(
                "Number of lines must be >= 1.",
                PLUGIN_NAME,
                wx.OK
                | wx.ICON_ERROR,
            )

            return

        if (
            values["line_length_start"]
            < 0
        ):

            wx.MessageBox(
                "Starting line length must "
                "be >= 0.",
                PLUGIN_NAME,
                wx.OK
                | wx.ICON_ERROR,
            )

            return

        if (
            values["line_length_end"]
            < 0
        ):

            wx.MessageBox(
                "Ending line length must "
                "be >= 0.",
                PLUGIN_NAME,
                wx.OK
                | wx.ICON_ERROR,
            )

            return

        if (
            values["copper_width"]
            <= 0
        ):

            wx.MessageBox(
                "Copper line width must "
                "be > 0.",
                PLUGIN_NAME,
                wx.OK
                | wx.ICON_ERROR,
            )

            return

        if (
            values["add_mask"]
            and values["mask_width"] <= 0
        ):

            wx.MessageBox(
                "Mask line width must "
                "be > 0.",
                PLUGIN_NAME,
                wx.OK
                | wx.ICON_ERROR,
            )

            return

        # ====================================================
        # Mask pairing
        # ====================================================

        if values["add_mask"]:

            expected_mask = (
                "F.Mask"
                if values["copper_layer"]
                == "F.Cu"
                else "B.Mask"
            )

            if (
                values["mask_layer"]
                != expected_mask
            ):

                answer = wx.MessageBox(
                    "The selected mask layer "
                    "does not match the selected "
                    "copper layer.\n\n"
                    f"Copper: "
                    f"{values['copper_layer']}\n"
                    f"Mask: "
                    f"{values['mask_layer']}\n\n"
                    f"Expected: "
                    f"{expected_mask}\n\n"
                    "Continue anyway?",
                    PLUGIN_NAME,
                    wx.YES_NO
                    | wx.ICON_WARNING,
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
                wx.OK
                | wx.ICON_ERROR,
            )

            return

        # ====================================================
        # Generate
        # ====================================================

        try:

            (
                created_items,
                created_group,
            ) = self.create_pattern(
                board,
                center,
                values,
            )

        except Exception as exc:

            wx.MessageBox(
                "Could not create radial pattern:\n\n"
                + str(exc),
                PLUGIN_NAME,
                wx.OK
                | wx.ICON_ERROR,
            )

            return

        # ====================================================
        # Select generated items
        # ====================================================

        try:

            board.clear_selection()

            board.add_to_selection(
                created_items
            )

        except Exception:
            pass

        # ====================================================
        # Success message
        # ====================================================

        mask_text = ""

        if values["add_mask"]:

            mask_text = (
                "\nMask: "
                f"{values['mask_layer']} "
                f"({values['mask_width']:.3f} mm)"
            )

        direction_text = (
            "Reverse"
            if values["reverse_direction"]
            else "Normal"
        )

        wx.MessageBox(
            "Radial pattern created.\n\n"
            f"Copper: "
            f"{values['copper_layer']} "
            f"({values['copper_width']:.3f} mm)"
            f"{mask_text}\n"
            f"Direction: "
            f"{direction_text}\n\n"
            f"Group: "
            f"{values['pattern_name']}",
            PLUGIN_NAME,
            wx.OK
            | wx.ICON_INFORMATION,
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
            wx.OK
            | wx.ICON_ERROR,
        )

    finally:

        app.Destroy()

