import math
import random
import re

from easyeda2xpedition.easyeda.easyeda_importer import EasyedaSymbolImporter
from easyeda2xpedition.easyeda.parameters_easyeda import EeSymbolPin, EeSymbolSub
from easyeda2xpedition.easyeda.easyeda_api import EasyedaApi

from easyeda2xpedition.xpedition.symbol.pin import SymbolPinPosition, SymbolPin, SymbolLabel, SymbolAnnotation, SymbolPinGroup
from easyeda2xpedition.xpedition.symbol.symbol import Symbol as XpeditionSymbol
from easyeda2xpedition.xpedition.symbol.symbol import SymbolShapeLine, SymbolShapeCircle, SymbolShapeArc


def ee_unit_to_th(value: float) -> float:
    """Convert an EasyEDA symbol unit (10 mil) to the Xpedition V 50 symbol unit (also 10 mil)."""
    return round(value * 1, 2)


SYMBOL_GRID = 10.0
SYMBOL_PIN_LENGTH = 20.0


def _snap_to_grid(value: float, grid: float = SYMBOL_GRID) -> float:
    """Snap a V 50 coordinate to the Symbol Editor's 0.1 inch grid."""
    return math.floor(value / grid + 0.5) * grid


class EeSymbolToXpeditionSymbol(object):
    def __init__(self, easyeda_cad_data: dict):
        self.easyeda_cad_data = easyeda_cad_data
        self.easyeda_symbol = EasyedaSymbolImporter(easyeda_cad_data).get_symbol()
        self.xpedition_symbol = XpeditionSymbol(self.easyeda_symbol.info.name)

        self._pin_name_list = []
        self._grid_offset_x = 0.0
        self._grid_offset_y = 0.0

    def convert(self):
        self.xpedition_symbol.refdes = self.easyeda_symbol.info.prefix
        self.xpedition_symbol.value = self.easyeda_symbol.info.mpn
        self.xpedition_symbol.mfg_name = self.easyeda_symbol.info.manufacturer
        self.xpedition_symbol.mpn = self.easyeda_symbol.info.mpn
        self.xpedition_symbol.dev_name = self.easyeda_symbol.info.name
        self.xpedition_symbol.name = self.easyeda_symbol.info.name

        # Convert all subparts
        if self.easyeda_symbol.subs:
            for idx, subpart in enumerate(self.easyeda_symbol.subs):
                part_name = f"{self.easyeda_symbol.info.name}.{idx + 1}"
                self._pin_name_list = []  # Reset pin name list for each subpart
                self.convert_subpart(subpart, part_name)
        else:
            # If there are no subs, convert the main symbol as a single part
            self._pin_name_list = []  # Reset pin name list
            self._align_to_grid(self.easyeda_symbol.bbox, getattr(self.easyeda_symbol, "pins", []))
            self.convert_pin_groups()
            self.convert_shapes()

        return self.xpedition_symbol

    def convert_subpart(self, subpart: EeSymbolSub, part_name: str):
        """Convert a single subpart (symbol part) to Xpedition format."""
        self._align_to_grid(subpart.bbox, subpart.pins)
        self.convert_pin_groups_for_subpart(subpart, part_name)
        self.convert_shapes_for_subpart(subpart, part_name)

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------
    def _align_to_grid(self, bbox, pins):
        """Shift the symbol origin so its pins land on the 0.1 inch grid.

        EasyEDA symbol coordinates are on a 10 mil grid, but the imported bbox
        origin is arbitrary.  Subtracting that origin leaves every pin slightly
        off the Xpedition Symbol Editor grid.  Aligning the first pin preserves
        the geometry while putting all shapes that share its grid phase on the
        same 0.1 inch grid.
        """
        self._grid_offset_x = 0.0
        self._grid_offset_y = 0.0

        pins = pins or []
        if not pins:
            return

        pin_x, pin_y, _, _ = self._parse_pin_path(pins[0].pin_path.path)
        translated_x = pin_x - bbox.x
        translated_y = bbox.y - pin_y
        self._grid_offset_x = _snap_to_grid(translated_x) - translated_x
        self._grid_offset_y = _snap_to_grid(translated_y) - translated_y

    def _x(self, raw_x: float, bbox) -> float:
        return ee_unit_to_th(float(raw_x) - bbox.x + self._grid_offset_x)

    def _y(self, raw_y: float, bbox) -> float:
        return ee_unit_to_th(bbox.y - float(raw_y) + self._grid_offset_y)

    def _point(self, raw_x: float, raw_y: float, bbox):
        return (self._x(raw_x, bbox), self._y(raw_y, bbox))

    # ------------------------------------------------------------------
    # Pin handling
    # ------------------------------------------------------------------
    def _parse_pin_path(self, path: str):
        """Return (x, y, axis, delta) for an EasyEDA pin path such as ``M 100 200 h 10``.

        Both comma and space separated variants are accepted, including negative
        deltas (e.g. ``M330,145h-10`` or ``M 330 145 v -20``).
        """
        match = re.search(
            r"M\s*(-?\d+(?:\.\d+)?)[\s,]+(-?\d+(?:\.\d+)?)\s*([hHvV])\s*(-?\d+(?:\.\d+)?)",
            path,
        )
        if not match:
            raise ValueError(f"Unsupported EasyEDA pin path: {path!r}")

        x = float(match.group(1))
        y = float(match.group(2))
        axis = match.group(3).lower()
        delta = float(match.group(4))
        return x, y, axis, delta

    def _rotate_pin_side(self, original_points, side):
        if side == 0:  # top
            return original_points
        elif side == 1:  # bottom
            return (original_points[1], original_points[0], original_points[3], original_points[2])
        elif side == 2:  # left
            return (original_points[2], original_points[3], original_points[0], original_points[1])
        elif side == 3:  # right
            return (original_points[3], original_points[2], original_points[1], original_points[0])
        else:
            raise ValueError("side must be 0, 1, 2 or 3")

    def _calc_pin_position(self, pin: EeSymbolPin):
        x, y, axis, delta = self._parse_pin_path(pin.pin_path.path)
        side = 0
        rotation = int(pin.settings.rotation or 0)

        if axis == "h":
            x1, y1 = x, y
            x2, y2 = x + delta, y

            if x1 > x2:
                side = 3  # right
                if rotation == 90:
                    x1, y1, x2, y2 = x1, y1, x1, y1 - delta
                    side = 0
                elif rotation == 270:
                    x1, y1, x2, y2 = x1, y1, x1, y1 + delta
                    side = 1
            else:
                side = 2  # left
                if rotation == 90:
                    x1, y1, x2, y2 = x1, y1, x1, y1 + delta
                    side = 0
                elif rotation == 270:
                    x1, y1, x2, y2 = x1, y1, x1, y1 - delta
                    side = 1
        else:  # vertical pin
            x1, y1 = x, y
            x2, y2 = x, y + delta

            if y1 > y2:
                side = 1  # bottom
                if rotation == 90:
                    x1, y1, x2, y2 = x1, y1, x1 - delta, y1
                    side = 2
                elif rotation == 180:
                    side = 0
                elif rotation == 270:
                    x1, y1, x2, y2 = x1, y1, x1 + delta, y1
                    side = 3
            else:
                side = 0  # top
                if rotation == 90:
                    x1, y1, x2, y2 = x1, y1, x1 + delta, y1
                    side = 3
                elif rotation == 180:
                    side = 1
                elif rotation == 270:
                    x1, y1, x2, y2 = x1, y1, x1 - delta, y1
                    side = 2

        # endx, endy, startx, starty
        return ((x2, y2, x1, y1), side)

    def _pin_endpoints(self, pin: EeSymbolPin, bbox):
        """Return body and outer pin endpoints in V 50 coordinates.

        The outer endpoint is placed exactly ``SYMBOL_PIN_LENGTH`` units from the
        body so every generated pin has a consistent 0.2 inch length.
        """
        pos, side = self._calc_pin_position(pin)
        body_x = self._x(pos[0], bbox)
        body_y = self._y(pos[1], bbox)

        if side == 0:  # top
            end_x, end_y = body_x, body_y + SYMBOL_PIN_LENGTH
        elif side == 1:  # bottom
            end_x, end_y = body_x, body_y - SYMBOL_PIN_LENGTH
        elif side == 2:  # left
            end_x, end_y = body_x - SYMBOL_PIN_LENGTH, body_y
        else:  # right
            end_x, end_y = body_x + SYMBOL_PIN_LENGTH, body_y

        return body_x, body_y, end_x, end_y, side

    def _calc_rotation_from_angle(self, angle):
        if angle == 0:
            return 0
        elif angle == 90:
            return 1
        elif angle == 180:
            return 2
        elif angle == 270:
            return 3
        else:
            raise ValueError("angle must be 0, 90, 180 or 270")

    def _calc_lable_rotation_from_side(self, side):
        if side == 0:  # top
            return 3  # 270
        elif side == 1:  # bottom
            return 1  # 90
        elif side == 2:  # left
            return 0  # 0
        elif side == 3:  # right
            return 0  # 0
        else:
            raise ValueError("side must be 0, 1, 2 or 3")

    def _get_anchor_from_side(self, side):
        if side == 0:  # top
            return (2, 3)  # middle left
        elif side == 1:  # bottom
            return (8, 9)  # middle right, lower right
        elif side == 2:  # left
            return (2, 3)  # lower left
        elif side == 3:  # right
            return (8, 9)  # lower right

    def _get_xpedition_pin_type(self, pin: EeSymbolPin):
        ee_pin_types = ['Undefined', 'Input', 'Output', 'I/O', 'Power']
        ee_pin_type = pin.settings.type
        ee_pin_type_str = ""
        if ee_pin_type in ee_pin_types:
            ee_pin_type_str = ee_pin_type
        else:
            ee_pin_type_str = "Undefined"

        pin_type_map = {
            "Input": "Input",
            "Output": "Ouput",
            "I/O": "BI",
        }

        if ee_pin_type_str in pin_type_map:
            return pin_type_map[ee_pin_type_str]
        else:
            return None

    def _cubic_bezier_point(self, p0, p1, p2, p3, t):
        x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0]
        y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1]
        return (x, y)

    def _determine_pin_name(self, pin: EeSymbolPin):
        pin_name = pin.name.text
        if pin_name in self._pin_name_list:
            index = 1
            while True:
                alt_pin_name = f"{pin_name}_{index}"
                if alt_pin_name not in self._pin_name_list:
                    break
                index += 1

            pin_name = alt_pin_name

        self._pin_name_list.append(pin_name)
        return pin_name

    # ------------------------------------------------------------------
    # Shape helpers
    # ------------------------------------------------------------------
    def _add_rect(self, rect, bbox, part_name=None):
        x_left = self._x(rect.pos_x, bbox)
        x_right = self._x(rect.pos_x + rect.width, bbox)
        y_bottom = self._y(rect.pos_y, bbox)
        y_top = self._y(rect.pos_y + rect.height, bbox)

        for x1, y1, x2, y2 in (
            (x_left, y_top, x_right, y_top),
            (x_left, y_bottom, x_right, y_bottom),
            (x_left, y_top, x_left, y_bottom),
            (x_right, y_top, x_right, y_bottom),
        ):
            self.xpedition_symbol.add_shape(SymbolShapeLine(x1, y1, x2, y2), part_name)

    def _add_circle(self, circle, bbox, part_name=None):
        self.xpedition_symbol.add_shape(
            SymbolShapeCircle(
                self._x(circle.center_x, bbox),
                self._y(circle.center_y, bbox),
                ee_unit_to_th(circle.radius),
            ),
            part_name,
        )

    def _add_ellipse(self, ellipse, bbox, part_name=None):
        """Add an ellipse.

        Xpedition symbols only have circle and circular-arc primitives, so a true
        ellipse is approximated with several circular arcs (or an exact circle
        when the radii are equal).
        """
        rx = ee_unit_to_th(ellipse.radius_x)
        ry = ee_unit_to_th(ellipse.radius_y)
        cx = self._x(ellipse.center_x, bbox)
        cy = self._y(ellipse.center_y, bbox)

        if round(rx, 4) == round(ry, 4):
            self.xpedition_symbol.add_shape(SymbolShapeCircle(cx, cy, rx), part_name)
            return

        segments = 8
        step = 2 * math.pi / segments
        for i in range(segments):
            a0 = i * step
            a1 = (i + 1) * step
            am = (i + 0.5) * step
            start = (cx + rx * math.cos(a0), cy + ry * math.sin(a0))
            mid = (cx + rx * math.cos(am), cy + ry * math.sin(am))
            end = (cx + rx * math.cos(a1), cy + ry * math.sin(a1))
            self.xpedition_symbol.add_shape(
                SymbolShapeArc(
                    round(start[0], 4), round(start[1], 4),
                    round(mid[0], 4), round(mid[1], 4),
                    round(end[0], 4), round(end[1], 4),
                ),
                part_name,
            )

    def _add_polyline(self, polyline, bbox, part_name=None):
        values = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", polyline.points)]
        points = [self._point(values[i], values[i + 1], bbox) for i in range(0, len(values) - 1, 2)]
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            self.xpedition_symbol.add_shape(SymbolShapeLine(x1, y1, x2, y2), part_name)

    def _add_line(self, line, bbox, part_name=None):
        self.xpedition_symbol.add_shape(
            SymbolShapeLine(
                self._x(line.x1, bbox),
                self._y(line.y1, bbox),
                self._x(line.x2, bbox),
                self._y(line.y2, bbox),
            ),
            part_name,
        )

    def _add_arc(self, arc, bbox, part_name=None):
        values = [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?", arc.path)]
        if len(values) < 4:
            return

        start_point = self._point(values[0], values[1], bbox)
        end_point = self._point(values[-2], values[-1], bbox)

        if len(values) >= 8:
            ctrl_point1 = self._point(values[2], values[3], bbox)
            ctrl_point2 = self._point(values[4], values[5], bbox)
            mid_point = self._cubic_bezier_point(start_point, ctrl_point1, ctrl_point2, end_point, 0.5)
        else:
            mid_point = ((start_point[0] + end_point[0]) / 2, (start_point[1] + end_point[1]) / 2)

        self.xpedition_symbol.add_shape(
            SymbolShapeArc(
                round(start_point[0], 4), round(start_point[1], 4),
                round(mid_point[0], 4), round(mid_point[1], 4),
                round(end_point[0], 4), round(end_point[1], 4),
            ),
            part_name,
        )

    def _convert_shapes(self, subpart, bbox, part_name=None):
        self.xpedition_symbol.set_bbox(0, ee_unit_to_th(bbox.width), ee_unit_to_th(bbox.height), 0, part_name)

        for rect in subpart.rectangles:
            self._add_rect(rect, bbox, part_name)

        for circle in subpart.circles:
            self._add_circle(circle, bbox, part_name)

        for ellipse in subpart.ellipses:
            self._add_ellipse(ellipse, bbox, part_name)

        for polyline in subpart.polylines:
            self._add_polyline(polyline, bbox, part_name)

        for polygon in getattr(subpart, "polygons", []):
            self._add_polyline(polygon, bbox, part_name)

        for line in subpart.lines:
            self._add_line(line, bbox, part_name)

        for arc in subpart.arcs:
            self._add_arc(arc, bbox, part_name)

    # ------------------------------------------------------------------
    # Conversion entry points
    # ------------------------------------------------------------------
    def convert_pin_groups_for_subpart(self, subpart: EeSymbolSub, part_name: str):
        """Convert pin groups for a single subpart."""
        bbox = subpart.bbox
        index = 1

        for pin in subpart.pins:
            body_x, body_y, end_x, end_y, side = self._pin_endpoints(pin, bbox)
            sym_pos = SymbolPinPosition(start_x=body_x,
                                        start_y=body_y,
                                        end_x=end_x,
                                        end_y=end_y)
            xpedition_pin = SymbolPin(index, sym_pos, 0, side=side)

            anchors = self._get_anchor_from_side(side)
            rotation = self._calc_rotation_from_angle(int(pin.name.rotation or 0))
            xpedition_label = SymbolLabel(self._determine_pin_name(pin), body_x, body_y, rotation, anchor=anchors[0])

            rotation = self._calc_rotation_from_angle(int(pin.number.rotation or 0))
            xpedition_annotation = SymbolAnnotation(f"#={pin.number.text}", end_x, end_y, rotation, anchor=anchors[1])

            # create a Xpedition PIN Group
            pin_group = SymbolPinGroup(xpedition_pin, xpedition_label, [xpedition_annotation])

            xpedition_pin_type = self._get_xpedition_pin_type(pin)
            if xpedition_pin_type is not None:
                xpedition_annotation = SymbolAnnotation(f"PINTYPE={xpedition_pin_type}", 0, 0, 0, visible=0)
                pin_group.add_annotation(xpedition_annotation)

            self.xpedition_symbol.add_pin_group(pin_group, part_name)
            index += 1

    def convert_shapes_for_subpart(self, subpart: EeSymbolSub, part_name: str):
        """Convert shapes for a single subpart."""
        self._convert_shapes(subpart, subpart.bbox, part_name)

    def convert_pin_groups(self):
        bbox = self.easyeda_symbol.bbox
        index = 1

        for pin in self.easyeda_symbol.pins:
            body_x, body_y, end_x, end_y, side = self._pin_endpoints(pin, bbox)
            sym_pos = SymbolPinPosition(start_x=body_x,
                                        start_y=body_y,
                                        end_x=end_x,
                                        end_y=end_y)
            xpedition_pin = SymbolPin(index, sym_pos, 0, side=side)

            anchors = self._get_anchor_from_side(side)
            rotation = self._calc_rotation_from_angle(int(pin.name.rotation or 0))
            xpedition_label = SymbolLabel(self._determine_pin_name(pin), body_x, body_y, rotation, anchor=anchors[0])

            rotation = self._calc_rotation_from_angle(int(pin.number.rotation or 0))
            xpedition_annotation = SymbolAnnotation(f"#={pin.number.text}", end_x, end_y, rotation, anchor=anchors[1])

            # create a Xpedition PIN Group
            pin_group = SymbolPinGroup(xpedition_pin, xpedition_label, [xpedition_annotation])

            xpedition_pin_type = self._get_xpedition_pin_type(pin)
            if xpedition_pin_type is not None:
                xpedition_annotation = SymbolAnnotation(f"PINTYPE={xpedition_pin_type}", 0, 0, 0, visible=0)
                pin_group.add_annotation(xpedition_annotation)

            self.xpedition_symbol.add_pin_group(pin_group)
            index += 1

    def convert_shapes(self):
        bbox = self.easyeda_symbol.bbox
        self._convert_shapes(self.easyeda_symbol, bbox)

    def save_to_file(self, file_path: str):
        """
        Save the symbol to file(s). If the symbol has multiple parts (subparts),
        save each part to a separate file with suffix .1, .2, .3, etc.
        If the symbol has only one part or no parts, save to a single file.

        Args:
            file_path: Base file path without extension (e.g., "output/symbol_name")
        """
        def _generate_symbol_string(part, part_name=None):
            # Place the reference designator above the symbol body and the
            # value/type below it, centred on the part bounding box.
            bbox = getattr(part, "bbox", (0, 0, 0, 0))
            try:
                width = float(bbox[1])
                height = float(bbox[2])
            except (TypeError, ValueError, IndexError):
                width = height = 0.0

            text_size = 8
            margin = 20
            line_step = text_size + 4
            center_x = round(width / 2, 2)
            # Symbol geometry uses Y up with the top of the bounding box at Y=0.
            refdes_y = margin
            type_y = margin - line_step
            value_y = round(-height - margin, 2)
            hetero_y = round(value_y - line_step, 2)

            sym_string = "V 50\n"
            sym_string += f"K {random.randint(1000000000, 9999999999)} {self.xpedition_symbol.name}\n"
            sym_string += "Y 1\n"
            sym_string += "Z 0\n"
            sym_string += "i 0\n"

            sym_string += f"U 0 0 10 0 5 0 {self.xpedition_symbol.name}\n"
            sym_string += "U 0 0 5 0 5 0 Copyright=EasyEDA to Xpedition\n"
            if self.xpedition_symbol.mfg_name:
                sym_string += f"U 0 0 5 0 5 0 Mfr_name={self.xpedition_symbol.mfg_name}\n"
            if self.xpedition_symbol.mpn:
                sym_string += f"U 0 0 5 0 5 0 Manufacturer_Part_Number={self.xpedition_symbol.mpn}\n"

            sym_string += str(part)

            def _fmt(value):
                return f"{float(value):g}"

            sym_string += f"U {_fmt(center_x)} {_fmt(refdes_y)} {text_size} 0 5 3 REFDES={self.xpedition_symbol.refdes.upper()}\n"
            sym_string += f"U {_fmt(center_x)} {_fmt(type_y)} {text_size} 0 5 0 TYPE=Type?\n"
            sym_string += f"U {_fmt(center_x)} {_fmt(value_y)} {text_size} 0 5 0 VALUE={self.xpedition_symbol.value}\n"

            if part_name:
                sym_string += f"U {_fmt(center_x)} {_fmt(hetero_y)} {text_size} 0 5 0 HETERO=" + ",".join(
                    f"({sym_name.replace('.', '_')})" for sym_name in self.xpedition_symbol.parts.keys()
                ) + "\n"

            sym_string += "E\n"
            return sym_string

        # Check if the symbol has multiple parts
        if len(self.xpedition_symbol.parts) > 1:
            # Save each part to a separate file
            for part_name in sorted(self.xpedition_symbol.parts.keys()):
                part_num = part_name.split('.')[-1] if '.' in part_name else "1"
                output_file = f"{file_path}.{part_num}"
                part = self.xpedition_symbol.parts[part_name]

                with open(output_file, "w") as f:
                    f.write(_generate_symbol_string(part, part_name))
        else:
            # Save as a single file. A symbol may have one subpart whose name
            # differs from the symbol name (e.g. "NAME.1"), so use the only part
            # rather than looking it up by the symbol name.
            if len(self.xpedition_symbol.parts) == 1:
                part = next(iter(self.xpedition_symbol.parts.values()))
            else:
                part = self.xpedition_symbol.parts.get(self.xpedition_symbol.name)
            if part:
                with open(file_path, "w") as f:
                    f.write(_generate_symbol_string(part))


if __name__ == "__main__":
    # lcsc_id = "C165948"  # 可替换为其它LCSC ID
    lcsc_id = "C730227"
    cad_data = EasyedaApi().get_cad_data_of_component(lcsc_id)
    converter = EeSymbolToXpeditionSymbol(cad_data)
    converter.convert()
    # save_to_file will automatically add .1, .2, .3 for multi-part symbols
    converter.save_to_file(f".\\output\\{lcsc_id}_xpedition")
