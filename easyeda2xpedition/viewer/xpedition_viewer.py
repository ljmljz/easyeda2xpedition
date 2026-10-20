"""
Xpedition HKP File Viewer using tkinter.

Supports preview for footprints, padstacks and symbols.
"""

import math
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox


POINT_RE = re.compile(
    r"\(\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*,\s*"
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*\)"
)

CELL_SECTION_HEADERS = {
    "..PIN",
    "..SILKSCREEN_OUTLINE",
    "..ASSEMBLY_OUTLINE",
    "..SOLDER_MASK",
    "..SOLDER_PASTE",
    "..PLACEMENT_OUTLINE",
}

CELL_LAYER_NAMES = {
    "..SILKSCREEN_OUTLINE": "SILKSCREEN_OUTLINE",
    "..ASSEMBLY_OUTLINE": "ASSEMBLY_OUTLINE",
    "..SOLDER_MASK": "SOLDER_MASK",
    "..SOLDER_PASTE": "SOLDER_PASTE",
    "..PLACEMENT_OUTLINE": "PLACEMENT_OUTLINE",
}


class XpeditionViewer:
    """Viewer for Xpedition HKP files (footprints and symbols)."""

    LAYER_STYLE = {
        "Pads": {"fill": "#d9a05b", "outline": "#8b5a2b", "width": 1},
        "Holes": {"fill": "#ffffff", "outline": "#222222", "width": 1},
        "SILKSCREEN_OUTLINE": {"fill": "", "outline": "#1f5f1f", "width": 2},
        "ASSEMBLY_OUTLINE": {"fill": "", "outline": "#777777", "width": 1, "dash": (4, 3)},
        "SOLDER_MASK": {"fill": "", "outline": "#4a90d9", "width": 1, "dash": (2, 2)},
        "SOLDER_PASTE": {"fill": "#ececec", "outline": "#a0a0a0", "width": 1, "stipple": "gray50"},
        "PLACEMENT_OUTLINE": {"fill": "", "outline": "#c000c0", "width": 1, "dash": (6, 3)},
        "Pins": {"fill": "#ffd000", "outline": "#a06000", "width": 1},
        "Body": {"fill": "", "outline": "#111111", "width": 2},
        "PinLines": {"fill": "", "outline": "#333333", "width": 1},
        "PinNames": {"fill": "#204080"},
        "PinNumbers": {"fill": "#b00000"},
        "SymbolText": {"fill": "#101010"},
        "Shapes": {"fill": "", "outline": "#111111", "width": 1},
        "Text": {"fill": "#444444"},
    }

    LAYER_ORDER = {
        "SOLDER_MASK": 0,
        "SOLDER_PASTE": 1,
        "ASSEMBLY_OUTLINE": 2,
        "SILKSCREEN_OUTLINE": 3,
        "PLACEMENT_OUTLINE": 4,
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Xpedition HKP Viewer - Footprint & Symbol Preview")
        self.root.geometry("1100x760")

        self.canvas = None
        self.layers = {}
        self.layer_buttons = {}
        self.view_type = None
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.drawing_commands = []
        self.pads = {}
        self.padstacks = {}
        self.holes = {}
        self.current_file_path = None
        self._last_pan = None
        self._fit_pending = False

        self.init_ui()

    def init_ui(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Button(toolbar, text="Load Footprint", command=self.load_footprint_file).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Load Symbol", command=self.load_symbol_file).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Fit View", command=self.fit_view).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Clear View", command=self.clear_view).pack(side=tk.LEFT, padx=2)

        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(canvas_frame, bg="white", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<MouseWheel>", self.on_canvas_scroll)
        self.canvas.bind("<Button-4>", self.on_canvas_scroll)
        self.canvas.bind("<Button-5>", self.on_canvas_scroll)
        self.canvas.bind("<ButtonPress-1>", self.on_pan_start)
        self.canvas.bind("<B1-Motion>", self.on_pan_move)

        controls_frame = tk.Frame(self.root)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        tk.Label(controls_frame, text="Layers:").pack(side=tk.LEFT, padx=5)
        self.layers_container = tk.Frame(controls_frame)
        self.layers_container.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_var = tk.StringVar(value="Load a footprint (.hkp) or a symbol file")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_footprint_file(self):
        self._choose_and_load(
            "Open Footprint",
            [
                ("Xpedition footprint / HKP", "*.hkp *_cell.hkp *_Cell.hkp"),
                ("All files", "*.*"),
            ],
        )

    def load_symbol_file(self):
        self._choose_and_load(
            "Open Symbol",
            [
                ("Xpedition symbol", "*_xpedition* *_sym* *.sym *.1 *.2 *.3 *.4"),
                ("All files", "*.*"),
            ],
        )

    def load_hkp_file(self):
        self.load_footprint_file()

    def _choose_and_load(self, title, filetypes):
        file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()

            lines = content.strip().splitlines()
            file_type = self._detect_file_type(lines)

            self._clear_pad_library()
            pad_path = None
            if file_type == "cell":
                pad_path = self._find_pad_file(file_path)
                if pad_path:
                    self._load_pad_library(pad_path)

            self.current_file_path = file_path
            self.parse_hkp_file(content)

            extra = f" + {os.path.basename(pad_path)}" if pad_path else ""
            self.status_var.set(f"Loaded: {file_path}{extra}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            self.status_var.set(f"Error: {str(e)}")

    def parse_hkp_file(self, content):
        self.clear_view()
        lines = content.strip().splitlines()

        file_type = self._detect_file_type(lines)
        if file_type == "cell":
            self._parse_cell_file(lines)
        elif file_type == "padstack":
            self._parse_padstack_file(lines)
        elif file_type == "symbol":
            self._parse_symbol_file(lines)
        else:
            messagebox.showwarning("Warning", "Unknown file format")

        self.fit_view()

    def _detect_file_type(self, lines):
        for line in lines[:20]:
            text = line.strip()
            if text.startswith(".PACKAGE_CELL") or ".CELL_LIBRARY" in text:
                return "cell"
            if "PADSTACK_LIBRARY" in text:
                return "padstack"
            if text.startswith("V 50"):
                return "symbol"
        return "unknown"

    def _find_pad_file(self, cell_path):
        cell_path = os.path.abspath(cell_path)
        directory = os.path.dirname(cell_path)
        base = os.path.basename(cell_path)

        candidates = []
        if "cell" in base.lower():
            candidates.append(os.path.join(directory, re.sub("cell", "pads", base, flags=re.I)))
        candidates.extend(
            [
                os.path.join(directory, "_Pads.hkp"),
                os.path.join(directory, "_pads.hkp"),
                os.path.join(directory, "pads.hkp"),
            ]
        )

        for candidate in candidates:
            if os.path.isfile(candidate) and os.path.abspath(candidate) != cell_path:
                return candidate
        return None

    def _clear_pad_library(self):
        self.pads = {}
        self.padstacks = {}
        self.holes = {}

    def _load_pad_library(self, file_path):
        with open(file_path, "r", encoding="latin-1") as f:
            lines = f.read().strip().splitlines()
        self._parse_pad_library_lines(lines)

    def _parse_pad_library_lines(self, lines):
        self._clear_pad_library()
        blocks = []
        current = None

        for raw in lines:
            text = raw.strip()
            if not text:
                continue
            lower = text.lower()
            if text.startswith('.PAD "') or text.startswith(".PADSTACK ") or lower.startswith('.hole "'):
                if current:
                    blocks.append(current)
                current = {"header": text, "body": []}
            elif current is not None:
                current["body"].append(text)

        if current:
            blocks.append(current)

        for block in blocks:
            header = block["header"]
            body = block["body"]
            lower = header.lower()
            if header.startswith('.PAD "'):
                pad = self._parse_pad_section(header, body)
                if pad:
                    self.pads[pad["name"]] = pad
            elif lower.startswith('.hole "'):
                hole = self._parse_hole_section(header, body)
                if hole:
                    self.holes[hole["name"]] = hole
            elif header.startswith(".PADSTACK "):
                padstack = self._parse_padstack_section(header, body)
                if padstack:
                    self.padstacks[padstack["name"]] = padstack

    def _parse_pad_section(self, header, body):
        name = self._quoted(header)
        if not name:
            return None

        pad = {
            "name": name,
            "kind": "",
            "width": 0.0,
            "height": 0.0,
            "diameter": 0.0,
            "points": [],
        }
        self._read_pad_geometry(pad, body)
        return pad

    def _parse_hole_section(self, header, body):
        name = self._quoted(header)
        if not name:
            return None

        hole = {
            "name": name,
            "kind": "",
            "width": 0.0,
            "height": 0.0,
            "diameter": 0.0,
        }
        for text in body:
            if text.startswith("..ROUND"):
                hole["kind"] = "round"
            elif text.startswith("..SLOT"):
                hole["kind"] = "slot"
            elif text.startswith("..RECTANGLE"):
                hole["kind"] = "rect"
            elif text.startswith("...WIDTH"):
                hole["width"] = self._last_float(text)
            elif text.startswith("...HEIGHT"):
                hole["height"] = self._last_float(text)
            elif text.startswith("...DIAMETER"):
                hole["diameter"] = self._last_float(text)
        return hole

    def _read_pad_geometry(self, pad, body):
        for text in body:
            if text.startswith("..RECTANGLE"):
                pad["kind"] = "rect"
            elif text.startswith("..ROUND"):
                pad["kind"] = "round"
            elif text.startswith("..OBLONG"):
                pad["kind"] = "oblong"
            elif text.startswith("..CUSTOM"):
                pad["kind"] = "custom"
            elif text.startswith("...WIDTH"):
                pad["width"] = self._last_float(text)
            elif text.startswith("...HEIGHT"):
                pad["height"] = self._last_float(text)
            elif text.startswith("...DIAMETER"):
                pad["diameter"] = self._last_float(text)
            elif text.startswith("....XY") or text.startswith("("):
                pad["points"].extend(self._points(text))

    def _parse_padstack_section(self, header, body):
        name = self._quoted(header)
        if not name:
            return None

        padstack = {
            "name": name,
            "pad": "",
            "hole": "",
            "type": "",
            "soldermask": "",
            "solderpaste": "",
        }
        for text in body:
            if text.startswith("..PADSTACK_TYPE"):
                parts = text.split()
                if len(parts) >= 2:
                    padstack["type"] = parts[1]
            elif text.startswith("...TOP_PAD"):
                padstack["pad"] = self._quoted(text)
            elif text.startswith("...HOLE_NAME"):
                padstack["hole"] = self._quoted(text)
            elif text.startswith("...TOP_SOLDERMASK_PAD"):
                padstack["soldermask"] = self._quoted(text)
            elif text.startswith("...BOTTOM_SOLDERMASK_PAD") and not padstack["soldermask"]:
                padstack["soldermask"] = self._quoted(text)
            elif text.startswith("...TOP_SOLDERPASTE_PAD"):
                padstack["solderpaste"] = self._quoted(text)
        return padstack

    def _parse_cell_file(self, lines):
        self.view_type = "footprint"
        self.layers.clear()
        self._clear_layer_buttons()

        pins = []
        shapes = []

        for section in self._cell_sections(lines):
            header = section["header"]
            if header == "..PIN":
                pin = self._parse_cell_pin(section)
                if pin:
                    pins.append(pin)
            elif header in CELL_LAYER_NAMES:
                shape = self._parse_cell_shape(section)
                if shape:
                    shapes.append(shape)

        has_cell_mask = any(shape["layer"] == "SOLDER_MASK" for shape in shapes)
        for pin in pins:
            self._draw_pin_pad(pin, draw_mask=not has_cell_mask)

        shapes.sort(key=lambda item: self.LAYER_ORDER.get(item["layer"], 9))
        for shape in shapes:
            self._draw_cell_shape(shape)

        for pin in pins:
            self.draw_pin(pin["x"], pin["y"], f"P{pin['number']}")

        self._update_layer_controls()

    def _cell_sections(self, lines):
        sections = []
        current = None

        for raw in lines:
            text = raw.strip()
            if not text:
                continue

            if text.startswith("..") and not text.startswith("..."):
                if current:
                    sections.append(current)
                    current = None
                header = text.split()[0]
                if header in CELL_SECTION_HEADERS:
                    current = {"header": header, "line": text, "body": []}
                continue

            if current is not None:
                current["body"].append(text)

        if current:
            sections.append(current)
        return sections

    def _parse_cell_pin(self, section):
        number = self._quoted(section["line"]) or ""
        pin = {"number": number, "x": 0.0, "y": 0.0, "padstack": "", "rotation": 0.0}

        for text in section["body"]:
            if text.startswith("...XY"):
                points = self._points(text)
                if points:
                    pin["x"], pin["y"] = points[0]
            elif text.startswith("...PADSTACK"):
                pin["padstack"] = self._quoted(text)
            elif text.startswith("...ROTATION"):
                pin["rotation"] = self._last_float(text)
        return pin

    def _parse_cell_shape(self, section):
        layer = CELL_LAYER_NAMES[section["header"]]
        shape = {
            "layer": layer,
            "kind": "path",
            "points": [],
            "width": 1.0,
            "radius": 0.0,
            "filled": False,
        }

        for text in section["body"]:
            if text.startswith("...POLYLINE_SHAPE"):
                shape["kind"] = "shape"
            elif text.startswith("...POLYLINE_PATH") or text.startswith("...POLYARC_PATH"):
                shape["kind"] = "path"
            elif text.startswith("...CIRCLE_PATH"):
                shape["kind"] = "circle"
            elif text.startswith("....WIDTH"):
                shape["width"] = self._last_float(text)
            elif text.startswith("....RADIUS"):
                shape["radius"] = self._last_float(text)
            elif text.startswith("....XY") or text.startswith("....XYR") or text.startswith("("):
                shape["points"].extend(self._points(text))
            elif text.startswith("....SHAPE_OPTIONS"):
                shape["filled"] = "FILLED" in text and "NOT_FILLED" not in text

        if shape["kind"] == "circle":
            if not shape["points"] or shape["radius"] <= 0:
                return None
        elif len(shape["points"]) < 2:
            return None
        return shape

    def _draw_cell_shape(self, shape):
        layer = shape["layer"]
        if shape["kind"] == "circle":
            x, y = shape["points"][0]
            self.draw_circle(x, y, shape["radius"], layer)
            return

        filled = shape["filled"] and layer in ("SOLDER_MASK", "SOLDER_PASTE")
        closed = shape["kind"] == "shape"
        self.draw_polyline(shape["points"], layer, shape["width"], closed=closed, filled=filled)

    def _draw_pin_pad(self, pin, draw_mask=True):
        padstack = self.padstacks.get(pin["padstack"])
        pad_name = ""
        hole_name = ""
        mask_name = ""

        if padstack:
            pad_name = padstack.get("pad", "")
            hole_name = padstack.get("hole", "")
            mask_name = padstack.get("soldermask", "")
        else:
            pad_name = pin["padstack"]
            for suffix in ("_SMD", "_TH"):
                if pad_name.endswith(suffix):
                    pad_name = pad_name[: -len(suffix)]
                    break

        pad = self.pads.get(pad_name)
        if pad:
            self._draw_pad_geometry(pad, pin, "Pads", filled=True)

        if draw_mask:
            if not mask_name and pad_name:
                mask_name = f"{pad_name}L"
            mask = self.pads.get(mask_name)
            if mask and mask is not pad:
                self._draw_pad_geometry(mask, pin, "SOLDER_MASK", filled=False)

        hole = self.holes.get(hole_name)
        if hole:
            self._draw_hole_geometry(hole, pin)

    def _draw_pad_geometry(self, pad, pin, layer, filled=True):
        kind = pad["kind"]
        if kind == "round":
            radius = (pad["diameter"] or pad["width"] or pad["height"]) / 2.0
            if radius > 0:
                self.draw_circle(pin["x"], pin["y"], radius, layer, filled=filled)
            return

        points = self._pad_points(pad)
        if len(points) < 3:
            return
        points = self._rotate_and_move(points, pin["rotation"], pin["x"], pin["y"])
        self.draw_polyline(points, layer, 1, closed=True, filled=filled)

    def _draw_hole_geometry(self, hole, pin):
        kind = hole["kind"]
        if kind == "round":
            radius = (hole["diameter"] or hole["width"] or hole["height"]) / 2.0
            if radius > 0:
                self.draw_circle(pin["x"], pin["y"], radius, "Holes", filled=True)
            return

        if kind == "slot":
            width = hole["width"] or hole["diameter"]
            height = hole["height"] or hole["diameter"]
            points = self._capsule_points(width, height)
        elif kind == "rect":
            points = self._rect_points(hole["width"], hole["height"])
        else:
            return

        if len(points) >= 3:
            points = self._rotate_and_move(points, pin["rotation"], pin["x"], pin["y"])
            self.draw_polyline(points, "Holes", 1, closed=True, filled=True)

    def _pad_points(self, pad):
        kind = pad["kind"]
        if kind == "rect":
            return self._rect_points(pad["width"], pad["height"])
        if kind == "oblong":
            return self._capsule_points(pad["width"], pad["height"])
        if kind == "custom":
            return list(pad["points"])
        return []

    def _rect_points(self, width, height):
        half_w = width / 2.0
        half_h = height / 2.0
        return [(-half_w, -half_h), (half_w, -half_h), (half_w, half_h), (-half_w, half_h)]

    def _capsule_points(self, width, height, segments=12):
        if width <= 0 or height <= 0:
            return []

        points = []
        if width >= height:
            radius = height / 2.0
            left = -width / 2.0 + radius
            right = width / 2.0 - radius
            for i in range(segments + 1):
                angle = math.radians(-90 + 180 * i / segments)
                points.append((right + radius * math.cos(angle), radius * math.sin(angle)))
            for i in range(segments + 1):
                angle = math.radians(90 + 180 * i / segments)
                points.append((left + radius * math.cos(angle), radius * math.sin(angle)))
        else:
            radius = width / 2.0
            bottom = -height / 2.0 + radius
            top = height / 2.0 - radius
            for i in range(segments + 1):
                angle = math.radians(180 + 180 * i / segments)
                points.append((radius * math.cos(angle), bottom + radius * math.sin(angle)))
            for i in range(segments + 1):
                angle = math.radians(0 + 180 * i / segments)
                points.append((radius * math.cos(angle), top + radius * math.sin(angle)))
        return points

    def _rotate_and_move(self, points, rotation, offset_x, offset_y):
        angle = math.radians(rotation or 0)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        result = []
        for x, y in points:
            rx = x * cos_a - y * sin_a + offset_x
            ry = x * sin_a + y * cos_a + offset_y
            result.append((rx, ry))
        return result

    def _parse_symbol_file(self, lines):
        self.view_type = "symbol"
        self.layers.clear()
        self._clear_layer_buttons()

        for raw in lines:
            text = raw.strip()
            if not text:
                continue

            parts = text.split()
            tag = parts[0]
            try:
                if tag == "D" and len(parts) >= 5:
                    x = float(parts[1])
                    width = float(parts[2])
                    height = float(parts[3])
                    y = float(parts[4])
                    self.draw_rect(x, y, x + width, y - height, "Body")
                elif tag == "P" and len(parts) >= 7:
                    end_x = float(parts[2])
                    end_y = float(parts[3])
                    start_x = float(parts[4])
                    start_y = float(parts[5])
                    self.draw_line(end_x, end_y, start_x, start_y, "PinLines", 1)
                    self.draw_pin(end_x, end_y, "", size=2)
                elif tag == "L" and len(parts) >= 9:
                    x = float(parts[1])
                    y = float(parts[2])
                    label = " ".join(parts[9:]) if len(parts) > 9 else ""
                    if label:
                        self.draw_text(x, y, label, "PinNames", 6, "center")
                elif tag == "A" and len(parts) >= 8:
                    x = float(parts[1])
                    y = float(parts[2])
                    annotation = " ".join(parts[7:])
                    if annotation.startswith("#"):
                        self.draw_text(x, y, annotation, "PinNumbers", 5, "center")
                elif tag == "l" and len(parts) >= 6:
                    self.draw_line(
                        float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5]), "Shapes", 1
                    )
                elif tag == "c" and len(parts) >= 4:
                    self.draw_circle(float(parts[1]), float(parts[2]), float(parts[3]), "Shapes")
                elif tag == "a" and len(parts) >= 7:
                    self.draw_arc(
                        float(parts[1]),
                        float(parts[2]),
                        float(parts[3]),
                        float(parts[4]),
                        float(parts[5]),
                        float(parts[6]),
                        "Shapes",
                    )
                elif tag == "U":
                    self._parse_symbol_text(parts)
            except (ValueError, IndexError):
                continue

        self._update_layer_controls()

    def _parse_symbol_text(self, parts):
        if len(parts) < 8:
            return

        x = float(parts[1])
        y = float(parts[2])
        text = " ".join(parts[7:])

        if x == 0 and y == 0 and not text.startswith(("REFDES", "VALUE", "TYPE", "HETERO")):
            return

        if text.startswith(("REFDES", "VALUE", "TYPE", "HETERO")):
            layer = "SymbolText"
            size = 8
        else:
            layer = "Text"
            size = 5
        self.draw_text(x, y, text, layer, size, "center")

    def _parse_padstack_file(self, lines):
        self.view_type = "footprint"
        self._parse_pad_library_lines(lines)
        self.status_var.set(
            f"Padstack library: {len(self.pads)} pads, {len(self.padstacks)} padstacks"
        )
        self._update_layer_controls()

    def draw_pin(self, x, y, label="P", size=3, layer="Pins"):
        self.layers.setdefault(layer, True)
        command = ("pin", x, y, label, size, layer)
        self.drawing_commands.append(command)
        self._draw_command(command)

    def draw_line(self, x1, y1, x2, y2, layer="Shapes", width=1):
        self.layers.setdefault(layer, True)
        command = ("line", x1, y1, x2, y2, layer, width)
        self.drawing_commands.append(command)
        self._draw_command(command)

    def draw_rect(self, x1, y1, x2, y2, layer="Body"):
        self.layers.setdefault(layer, True)
        command = ("rect", x1, y1, x2, y2, layer)
        self.drawing_commands.append(command)
        self._draw_command(command)

    def draw_circle(self, x, y, r, layer="Shapes", filled=False):
        self.layers.setdefault(layer, True)
        command = ("circle", x, y, r, layer, filled)
        self.drawing_commands.append(command)
        self._draw_command(command)

    def draw_arc(self, x1, y1, x2, y2, x3, y3, layer="Shapes"):
        self.layers.setdefault(layer, True)
        command = ("arc", x1, y1, x2, y2, x3, y3, layer)
        self.drawing_commands.append(command)
        self._draw_command(command)

    def draw_polyline(self, points, layer="Shapes", width=1, closed=False, filled=False):
        if not points:
            return
        self.layers.setdefault(layer, True)
        command = ("polyline", list(points), layer, width, closed, filled)
        self.drawing_commands.append(command)
        self._draw_command(command)

    def draw_text(self, x, y, text, layer="Text", size=8, anchor="center"):
        self.layers.setdefault(layer, True)
        command = ("text", x, y, text, layer, size, anchor)
        self.drawing_commands.append(command)
        self._draw_command(command)

    def _draw_command(self, command):
        kind = command[0]
        if kind == "line":
            _, x1, y1, x2, y2, layer, width = command
            if not self.layers.get(layer, True):
                return
            style = self._style(layer)
            self.canvas.create_line(
                self._scale_x(x1),
                self._scale_y(y1),
                self._scale_x(x2),
                self._scale_y(y2),
                fill=style.get("outline", "#000000"),
                width=max(1, width * self.zoom_level),
                dash=style.get("dash"),
                tags=layer,
            )
        elif kind == "rect":
            _, x1, y1, x2, y2, layer = command
            if not self.layers.get(layer, True):
                return
            style = self._style(layer)
            self.canvas.create_rectangle(
                self._scale_x(x1),
                self._scale_y(y1),
                self._scale_x(x2),
                self._scale_y(y2),
                outline=style.get("outline", "#000000"),
                width=max(1, style.get("width", 1) * self.zoom_level),
                tags=layer,
            )
        elif kind == "circle":
            _, x, y, radius, layer, filled = command
            if not self.layers.get(layer, True):
                return
            style = self._style(layer)
            x_scaled = self._scale_x(x)
            y_scaled = self._scale_y(y)
            r_scaled = max(1.0, abs(radius * self.zoom_level))
            self.canvas.create_oval(
                x_scaled - r_scaled,
                y_scaled - r_scaled,
                x_scaled + r_scaled,
                y_scaled + r_scaled,
                fill=style.get("fill", "") if filled else "",
                outline=style.get("outline", "#000000"),
                width=max(1, style.get("width", 1) * self.zoom_level),
                tags=layer,
            )
        elif kind == "arc":
            _, x1, y1, x2, y2, x3, y3, layer = command
            if not self.layers.get(layer, True):
                return
            style = self._style(layer)
            points = []
            for i in range(21):
                t = i / 20.0
                mt = 1.0 - t
                x = mt * mt * x1 + 2.0 * mt * t * x2 + t * t * x3
                y = mt * mt * y1 + 2.0 * mt * t * y2 + t * t * y3
                points.extend([self._scale_x(x), self._scale_y(y)])
            self.canvas.create_line(
                points,
                fill=style.get("outline", "#000000"),
                width=max(1, style.get("width", 1) * self.zoom_level),
                tags=layer,
            )
        elif kind == "polyline":
            _, raw_points, layer, width, closed, filled = command
            if not self.layers.get(layer, True):
                return
            style = self._style(layer)
            points = []
            for x, y in raw_points:
                points.extend([self._scale_x(x), self._scale_y(y)])
            if closed and len(points) >= 4:
                points.extend(points[:2])
            if filled and len(points) >= 6:
                self.canvas.create_polygon(
                    points,
                    fill=style.get("fill", "") or "#d9a05b",
                    outline=style.get("outline", "#000000"),
                    width=max(1, style.get("width", 1) * self.zoom_level),
                    stipple=style.get("stipple"),
                    tags=layer,
                )
            else:
                self.canvas.create_line(
                    points,
                    fill=style.get("outline", "#000000"),
                    width=max(1, width * self.zoom_level),
                    dash=style.get("dash"),
                    tags=layer,
                )
        elif kind == "pin":
            _, x, y, label, size, layer = command
            if not self.layers.get(layer, True):
                return
            style = self._style(layer)
            x_scaled = self._scale_x(x)
            y_scaled = self._scale_y(y)
            self.canvas.create_oval(
                x_scaled - size,
                y_scaled - size,
                x_scaled + size,
                y_scaled + size,
                fill=style.get("fill", "#ffd000"),
                outline=style.get("outline", "#a06000"),
                tags=layer,
            )
            if label:
                self.canvas.create_text(
                    x_scaled + size + 2,
                    y_scaled - size - 2,
                    text=label,
                    fill="#7a3e00",
                    font=("Arial", 6, "bold"),
                    anchor="sw",
                    tags=layer,
                )
        elif kind == "text":
            _, x, y, text, layer, size, anchor = command
            if not self.layers.get(layer, True):
                return
            style = self._style(layer)
            self.canvas.create_text(
                self._scale_x(x),
                self._scale_y(y),
                text=text,
                fill=style.get("fill", "#000000"),
                font=("Arial", max(6, int(size))),
                anchor=anchor,
                tags=layer,
            )

    def _style(self, layer):
        return self.LAYER_STYLE.get(layer, {"fill": "", "outline": "#000000", "width": 1})

    def _scale_x(self, x):
        return x * self.zoom_level + self.pan_x

    def _scale_y(self, y):
        return -y * self.zoom_level + self.pan_y

    def _clear_layer_buttons(self):
        for widget in self.layers_container.winfo_children():
            widget.destroy()
        self.layer_buttons.clear()

    def _update_layer_controls(self):
        self._clear_layer_buttons()

        for layer_name in sorted(self.layers.keys()):
            var = tk.BooleanVar(value=self.layers[layer_name])

            def toggle_layer(layer_name=layer_name, var=var):
                self.layers[layer_name] = var.get()
                state = tk.NORMAL if var.get() else tk.HIDDEN
                self.canvas.itemconfig(layer_name, state=state)

            cb = tk.Checkbutton(
                self.layers_container,
                text=layer_name,
                variable=var,
                command=toggle_layer,
            )
            cb.pack(side=tk.LEFT, padx=2)
            self.layer_buttons[layer_name] = (var, cb)

    def _zoom(self, factor, screen_x=None, screen_y=None):
        if not self.drawing_commands:
            return

        if screen_x is None:
            screen_x = self.canvas.winfo_width() / 2.0
        if screen_y is None:
            screen_y = self.canvas.winfo_height() / 2.0

        old_zoom = self.zoom_level
        new_zoom = max(1e-5, old_zoom * factor)
        if new_zoom == old_zoom:
            return

        file_x = (screen_x - self.pan_x) / old_zoom
        file_y = (self.pan_y - screen_y) / old_zoom
        self.pan_x = screen_x - file_x * new_zoom
        self.pan_y = screen_y + file_y * new_zoom
        self.zoom_level = new_zoom
        self._redraw()

    def zoom_in(self):
        self._zoom(1.2)

    def zoom_out(self):
        self._zoom(1.0 / 1.2)

    def fit_view(self):
        self.root.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 50 or height < 50:
            if not self._fit_pending:
                self._fit_pending = True
                self.root.after(50, self._retry_fit)
            return

        bounds = self._command_bounds()
        if not bounds:
            self.zoom_level = 1.0
            self.pan_x = width / 2.0
            self.pan_y = height / 2.0
            self._redraw()
            return

        min_x, min_y, max_x, max_y = bounds
        span_x = max(max_x - min_x, 1e-6)
        span_y = max(max_y - min_y, 1e-6)
        margin = 60
        scale_x = (width - margin) / span_x
        scale_y = (height - margin) / span_y
        self.zoom_level = max(1e-5, min(scale_x, scale_y))

        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        self.pan_x = width / 2.0 - center_x * self.zoom_level
        self.pan_y = height / 2.0 + center_y * self.zoom_level
        self._redraw()

    def _retry_fit(self):
        self._fit_pending = False
        self.fit_view()

    def _command_bounds(self):
        if not self.drawing_commands:
            return None

        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        def add(x, y):
            nonlocal min_x, min_y, max_x, max_y
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)

        for command in self.drawing_commands:
            kind = command[0]
            if kind == "line":
                _, x1, y1, x2, y2, _, _ = command
                add(x1, y1)
                add(x2, y2)
            elif kind == "rect":
                _, x1, y1, x2, y2, _ = command
                add(x1, y1)
                add(x2, y2)
            elif kind == "circle":
                _, x, y, radius, _, _ = command
                add(x - radius, y - radius)
                add(x + radius, y + radius)
            elif kind == "arc":
                _, x1, y1, x2, y2, x3, y3, _ = command
                add(x1, y1)
                add(x2, y2)
                add(x3, y3)
            elif kind == "polyline":
                for x, y in command[1]:
                    add(x, y)
            elif kind == "pin":
                _, x, y, _, _, _ = command
                add(x, y)
            elif kind == "text":
                _, x, y, _, _, _, _ = command
                add(x, y)

        if min_x == float("inf"):
            return None
        return min_x, min_y, max_x, max_y

    def clear_view(self):
        self.canvas.delete("all")
        self.layers.clear()
        self._clear_layer_buttons()
        self.view_type = None
        self.drawing_commands = []
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

    def _redraw(self):
        self.canvas.delete("all")
        for command in self.drawing_commands:
            self._draw_command(command)

    def on_canvas_scroll(self, event):
        if event.num == 5 or event.delta < 0:
            self._zoom(1.0 / 1.2, event.x, event.y)
        elif event.num == 4 or event.delta > 0:
            self._zoom(1.2, event.x, event.y)

    def on_pan_start(self, event):
        self._last_pan = (event.x, event.y)

    def on_pan_move(self, event):
        if not self._last_pan:
            return
        dx = event.x - self._last_pan[0]
        dy = event.y - self._last_pan[1]
        self._last_pan = (event.x, event.y)
        self.pan_x += dx
        self.pan_y += dy
        self._redraw()

    def _quoted(self, text):
        match = re.search(r'"([^"]*)"', text)
        return match.group(1) if match else ""

    def _last_float(self, text):
        numbers = re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", text)
        if not numbers:
            return 0.0
        try:
            return float(numbers[-1])
        except ValueError:
            return 0.0

    def _points(self, text):
        result = []
        for x, y in POINT_RE.findall(text):
            try:
                result.append((float(x), float(y)))
            except ValueError:
                continue
        return result


def main():
    root = tk.Tk()
    viewer = XpeditionViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
