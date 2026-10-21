"""
EasyEDA Package Viewer using tkinter.
Supports preview for parts, footprints and symbols from EasyEDA.
"""

import math
import os
import re
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

if __package__ in (None, ""):
    sys.path.insert(
        0,
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    )

from easyeda2xpedition.easyeda.easyeda_api import EasyedaApi
from easyeda2xpedition.easyeda.easyeda_importer import EasyedaFootprintImporter, EasyedaSymbolImporter


class EasyedaViewer:
    """Viewer for EasyEDA components (parts, footprints and symbols)."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("EasyEDA Component Viewer - Part, Footprint & Symbol Preview")
        self.root.geometry("1400x800")
        
        self.canvas = None
        self.layers = {}
        self.layer_buttons = {}
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.drawing_commands = []
        self.current_data = None
        self.current_cad_data = None
        self.current_part_symbol = None
        self.current_part_footprint = None
        self.current_symbol = None
        self.current_sub_index = 0
        self._fit_pending = False
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Top toolbar
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Label(toolbar, text="LCSC ID:").pack(side=tk.LEFT, padx=5)
        self.id_input = tk.Entry(toolbar, width=15)
        self.id_input.pack(side=tk.LEFT, padx=5)
        self.id_input.bind("<Return>", lambda e: self.load_package())
        
        tk.Button(toolbar, text="Load Part", command=self.load_part).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Load Footprint", command=self.load_footprint).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Load Symbol", command=self.load_symbol).pack(side=tk.LEFT, padx=2)
        self.part_symbol_button = tk.Button(
            toolbar, text="Part Symbol", command=self.show_part_symbol, state=tk.DISABLED
        )
        self.part_symbol_button.pack(side=tk.LEFT, padx=2)
        self.part_footprint_button = tk.Button(
            toolbar, text="Part Footprint", command=self.show_part_footprint, state=tk.DISABLED
        )
        self.part_footprint_button.pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Fit View", command=self.fit_view).pack(side=tk.LEFT, padx=2)
        
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        properties_frame = tk.LabelFrame(content_frame, text="Part Properties")
        properties_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        self.properties_text = scrolledtext.ScrolledText(
            properties_frame, width=48, wrap=tk.WORD, state=tk.DISABLED
        )
        self.properties_text.pack(fill=tk.BOTH, expand=True)
        
        canvas_frame = tk.Frame(content_frame)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.symbol_selector_frame = tk.Frame(canvas_frame)
        self.symbol_selector_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 4))
        tk.Label(self.symbol_selector_frame, text="Subpart:").pack(side=tk.LEFT, padx=(0, 5))
        self.sub_selector = ttk.Combobox(
            self.symbol_selector_frame, state="disabled", width=40
        )
        self.sub_selector.pack(side=tk.LEFT)
        self.sub_selector.bind("<<ComboboxSelected>>", self._on_sub_selected)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<MouseWheel>", self.on_canvas_scroll)
        self.canvas.bind("<Button-4>", self.on_canvas_scroll)
        self.canvas.bind("<Button-5>", self.on_canvas_scroll)
        
        # Layer controls frame
        controls_frame = tk.Frame(self.root)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        tk.Label(controls_frame, text="Layers:").pack(side=tk.LEFT, padx=5)
        self.layers_container = tk.Frame(controls_frame)
        self.layers_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Load a part, footprint or symbol by LCSC ID")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_package(self):
        """Load package by ID."""
        package_id = self.id_input.get().strip()
        if not package_id:
            messagebox.showwarning("Warning", "Please enter a package ID")
            return
        self.load_part()
    
    def load_part(self):
        """Load and display a part with its properties, symbol and footprint."""
        package_id = self.id_input.get().strip()
        if not package_id:
            messagebox.showwarning("Warning", "Please enter a package ID")
            return
        
        try:
            self.status_var.set(f"Loading part {package_id}...")
            self.root.update()
            
            api = EasyedaApi()
            cad_data = api.get_cad_data_of_component(package_id)
            if not cad_data:
                raise Exception("No CAD data found")
            
            symbol = EasyedaSymbolImporter(cad_data).get_symbol()
            footprint = EasyedaFootprintImporter(cad_data).get_footprint()
            
            self.current_cad_data = cad_data
            self.current_part_symbol = symbol
            self.current_part_footprint = footprint
            self.current_data = cad_data
            self._set_properties_text(
                self._format_easyeda_part_properties(symbol, footprint, cad_data)
            )
            self.part_symbol_button.config(state=tk.NORMAL)
            self.part_footprint_button.config(state=tk.NORMAL)
            self.display_symbol(symbol)
            self.status_var.set(
                f"Loaded part {package_id}: {symbol.info.name} / {footprint.info.name}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load part: {e}")
            self.status_var.set(f"Error: {str(e)}")
    
    def show_part_symbol(self):
        """Show the symbol of the currently loaded part."""
        if self.current_part_symbol is None:
            messagebox.showwarning("Warning", "Load a part first")
            return
        self.display_symbol(self.current_part_symbol)
        self.status_var.set(f"Part symbol: {self.current_part_symbol.info.name}")
    
    def show_part_footprint(self):
        """Show the footprint of the currently loaded part."""
        if self.current_part_footprint is None:
            messagebox.showwarning("Warning", "Load a part first")
            return
        self.display_footprint(self.current_part_footprint)
        self.status_var.set(f"Part footprint: {self.current_part_footprint.info.name}")
    
    def _clear_part_state(self):
        self.current_cad_data = None
        self.current_part_symbol = None
        self.current_part_footprint = None
        if hasattr(self, "part_symbol_button"):
            self.part_symbol_button.config(state=tk.DISABLED)
            self.part_footprint_button.config(state=tk.DISABLED)
        if hasattr(self, "properties_text"):
            self._set_properties_text("")
    
    def _set_properties_text(self, text):
        self.properties_text.config(state=tk.NORMAL)
        self.properties_text.delete("1.0", tk.END)
        self.properties_text.insert("1.0", text)
        self.properties_text.config(state=tk.DISABLED)
    
    @staticmethod
    def _format_easyeda_part_properties(symbol, footprint, cad_data=None):
        info = getattr(symbol, "info", None)
        fp_info = getattr(footprint, "info", None)
        c_para = {}
        if cad_data:
            c_para = (
                cad_data.get("dataStr", {}).get("head", {}).get("c_para", {}) or {}
            )
        
        rows = [
            ("LCSC ID", getattr(info, "lcsc_id", "") or c_para.get("Supplier Part", "")),
            ("Name", getattr(info, "name", "") or c_para.get("name", "")),
            ("Manufacturer Part", getattr(info, "mpn", "") or c_para.get("Manufacturer Part", "")),
            ("Manufacturer", getattr(info, "manufacturer", "") or c_para.get("Manufacturer", "")),
            ("Reference Prefix", getattr(info, "prefix", "") or c_para.get("pre", "")),
            ("Package", getattr(info, "package", "") or c_para.get("package", "")),
            ("JLCPCB Part Class", getattr(info, "jlc_id", "") or c_para.get("JLCPCB Part Class", "")),
            ("Datasheet", getattr(info, "datasheet", "") or c_para.get("Datasheet", "")),
            ("Footprint Type", getattr(fp_info, "fp_type", "")),
            ("3D Model", getattr(fp_info, "model_3d_name", "") or c_para.get("3DModel", "")),
        ]
        
        subs = getattr(symbol, "subs", []) or []
        pin_count = sum(len(getattr(sub, "pins", [])) for sub in subs)
        lines = ["Part Properties", "=" * 16]
        for label, value in rows:
            if value:
                lines.append(f"{label}: {value}")
        
        lines.extend(
            [
                "",
                "Contents",
                "=" * 16,
                f"Symbol subparts: {len(subs)}",
                f"Symbol pins: {pin_count}",
                f"Footprint pads: {len(getattr(footprint, 'pads', []))}",
                f"Footprint tracks: {len(getattr(footprint, 'tracks', []))}",
                f"Footprint holes: {len(getattr(footprint, 'holes', []))}",
                f"Footprint circles: {len(getattr(footprint, 'circles', []))}",
                f"Footprint rectangles: {len(getattr(footprint, 'rectangles', []))}",
            ]
        )
        
        known = {
            "Supplier Part",
            "name",
            "Manufacturer Part",
            "Manufacturer",
            "pre",
            "package",
            "JLCPCB Part Class",
            "Datasheet",
            "3DModel",
        }
        extra_rows = [
            (key, c_para[key])
            for key in sorted(c_para)
            if key not in known and c_para[key] not in (None, "")
        ]
        if extra_rows:
            lines.extend(["", "Additional EasyEDA Fields", "=" * 16])
            for key, value in extra_rows:
                lines.append(f"{key}: {value}")
        
        return "\n".join(lines) + "\n"
    
    def load_footprint(self):
        """Load and display a footprint."""
        package_id = self.id_input.get().strip()
        if not package_id:
            messagebox.showwarning("Warning", "Please enter a package ID")
            return
        
        self._clear_part_state()
        try:
            self.status_var.set(f"Loading footprint {package_id}...")
            self.root.update()
            
            api = EasyedaApi()
            cad_data = api.get_cad_data_of_component(package_id)
            if not cad_data:
                raise Exception("No CAD data found")
            
            importer = EasyedaFootprintImporter(cad_data)
            footprint = importer.get_footprint()
            
            self.display_footprint(footprint)
            self.status_var.set(f"Loaded footprint: {footprint.info.name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load footprint: {e}")
            self.status_var.set(f"Error: {str(e)}")
    
    def load_symbol(self):
        """Load and display a symbol."""
        package_id = self.id_input.get().strip()
        if not package_id:
            messagebox.showwarning("Warning", "Please enter a package ID")
            return
        
        self._clear_part_state()
        try:
            self.status_var.set(f"Loading symbol {package_id}...")
            self.root.update()
            
            api = EasyedaApi()
            cad_data = api.get_cad_data_of_component(package_id)
            if not cad_data:
                raise Exception("No CAD data found")
            
            importer = EasyedaSymbolImporter(cad_data)
            symbol = importer.get_symbol()
            
            self.display_symbol(symbol)
            self.status_var.set(f"Loaded symbol: {symbol.info.name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load symbol: {e}")
            self.status_var.set(f"Error: {str(e)}")
    
    def display_footprint(self, footprint):
        """Display a footprint."""
        self.canvas.delete("all")
        self.drawing_commands = []
        self.layers.clear()
        self._clear_layer_buttons()
        self.current_symbol = None
        self._clear_symbol_selector()
        
        # Draw pads
        for pad in getattr(footprint, "pads", []):
            layer = "Pads"
            if layer not in self.layers:
                self.layers[layer] = True
            
            x = getattr(pad, "center_x", 0)
            y = getattr(pad, "center_y", 0)
            w = getattr(pad, "width", 0)
            h = getattr(pad, "height", 0)
            shape = getattr(pad, "shape", "RECT").upper()
            
            if shape == "RECT":
                self.draw_rectangle(x - w/2, y - h/2, x + w/2, y + h/2, layer, "yellow", "orange")
            elif shape in ("ROUND", "CIRCLE"):
                r = w / 2
                self.draw_ellipse(x, y, r, layer, "yellow", "orange")
            elif shape in ("OVAL", "OBLONG"):
                self.draw_oblong(x - w/2, y - h/2, w, h, layer, "yellow", "orange")
            
            # Draw hole if present
            hole_radius = getattr(pad, "hole_radius", 0)
            if hole_radius > 0:
                self.draw_circle(x, y, hole_radius, "Holes", "gray", None)
        
        # Draw circles
        for circ in getattr(footprint, "circles", []):
            layer = "Circles"
            if layer not in self.layers:
                self.layers[layer] = True
            
            cx = getattr(circ, "cx", 0)
            cy = getattr(circ, "cy", 0)
            r = getattr(circ, "radius", 0)
            self.draw_circle(cx, cy, r, layer, "blue", None)
        
        # Draw rectangles
        for rect in getattr(footprint, "rectangles", []):
            layer = "Rectangles"
            if layer not in self.layers:
                self.layers[layer] = True
            
            x = getattr(rect, "x", 0)
            y = getattr(rect, "y", 0)
            w = getattr(rect, "width", 0)
            h = getattr(rect, "height", 0)
            self.draw_rectangle(x, y, x + w, y + h, layer, "cyan", "blue")
        
        # Draw tracks
        for track in getattr(footprint, "tracks", []):
            layer = "Tracks"
            if layer not in self.layers:
                self.layers[layer] = True
            
            points_str = getattr(track, "points", "")
            if points_str:
                pts = [float(v) for v in points_str.replace(",", " ").split()]
                for i in range(0, len(pts) - 2, 2):
                    self.draw_line(pts[i], pts[i+1], pts[i+2], pts[i+3], layer, "green")
        
        # Draw holes
        for hole in getattr(footprint, "holes", []):
            layer = "Holes"
            if layer not in self.layers:
                self.layers[layer] = True
            
            x = getattr(hole, "center_x", 0)
            y = getattr(hole, "center_y", 0)
            r = getattr(hole, "radius", 0)
            self.draw_circle(x, y, r, layer, "gray", None)
        
        self._update_layer_controls()
        self.fit_view()
    
    def display_symbol(self, symbol, sub_index=None):
        """Display a symbol, showing one subpart at a time."""
        self.canvas.delete("all")
        self.drawing_commands = []
        self.layers.clear()
        self._clear_layer_buttons()
        
        previous_symbol = self.current_symbol
        self.current_symbol = symbol
        subs = self._get_symbol_subs(symbol)
        if sub_index is None:
            if symbol is previous_symbol and 0 <= self.current_sub_index < len(subs):
                sub_index = self.current_sub_index
            else:
                sub_index = 0
        sub_index = max(0, min(int(sub_index), len(subs) - 1)) if subs else 0
        self.current_sub_index = sub_index
        self._update_sub_selector(subs, sub_index)
        
        if subs:
            sub = subs[sub_index]
            for rect in getattr(sub, "rectangles", []):
                x = getattr(rect, "pos_x", 0)
                y = getattr(rect, "pos_y", 0)
                w = getattr(rect, "width", 0)
                h = getattr(rect, "height", 0)
                fill = getattr(rect, "fill_color", None)
                if not fill or str(fill).lower() == "none":
                    fill = "lightblue"
                self.draw_rectangle(x, y, x + w, y + h, "Shapes", fill, "blue")
            
            for circ in getattr(sub, "circles", []):
                fill = "lightblue" if getattr(circ, "fill_color", False) else ""
                self.draw_circle(
                    getattr(circ, "center_x", 0),
                    getattr(circ, "center_y", 0),
                    getattr(circ, "radius", 0),
                    "Shapes",
                    "blue",
                    fill,
                )
            
            for ellipse in getattr(sub, "ellipses", []):
                fill = "lightblue" if getattr(ellipse, "fill_color", False) else ""
                self.draw_circle(
                    getattr(ellipse, "center_x", 0),
                    getattr(ellipse, "center_y", 0),
                    getattr(ellipse, "radius_x", 0),
                    "Shapes",
                    "blue",
                    fill,
                )
            
            for polyline in getattr(sub, "polylines", []):
                self._draw_symbol_points(getattr(polyline, "points", ""), closed=False)
            
            for polygon in getattr(sub, "polygons", []):
                self._draw_symbol_points(getattr(polygon, "points", ""), closed=True)
            
            for line in getattr(sub, "lines", []):
                self.draw_line(
                    getattr(line, "x1", 0),
                    getattr(line, "y1", 0),
                    getattr(line, "x2", 0),
                    getattr(line, "y2", 0),
                    "Shapes",
                    "black",
                )
            
            for pin in getattr(sub, "pins", []):
                start, end = self._symbol_pin_endpoints(pin)
                name_obj = getattr(pin, "name", None)
                number_obj = getattr(pin, "number", None)
                name = getattr(name_obj, "text", "")
                number = getattr(number_obj, "text", "")
                label = number or name or "P"
                self.draw_line(
                    start[0], start[1], end[0], end[1], "Pins", "black"
                )
                self.draw_pin(start[0], start[1], str(label), "Pins")

                if name and getattr(name_obj, "is_displayed", True):
                    name_x = getattr(name_obj, "pos_x", None)
                    name_y = getattr(name_obj, "pos_y", None)
                    if name_x is None or name_y is None:
                        name_x, name_y = self._pin_name_position(start, end)
                    anchor = self._easyeda_text_anchor(
                        getattr(name_obj, "text_anchor", "middle")
                    )
                    self.draw_text(
                        name_x, name_y, str(name), "PinNames", 6, anchor, "black"
                    )
        
        self._update_layer_controls()
        self.fit_view()
    
    @staticmethod
    def _get_symbol_subs(symbol):
        """Return the list of subparts for an EasyEDA symbol."""
        if symbol is None:
            return []
        subs = getattr(symbol, "subs", None)
        if subs:
            return list(subs)
        return [symbol]
    
    @staticmethod
    def _symbol_sub_label(sub, index):
        name = getattr(sub, "name", "") or f"Subpart {index + 1}"
        pins = getattr(sub, "pins", None)
        if pins is not None:
            return f"{name} ({len(pins)} pins)"
        return name
    
    def _update_sub_selector(self, subs, index):
        if not hasattr(self, "sub_selector"):
            return
        labels = [self._symbol_sub_label(sub, i) for i, sub in enumerate(subs)]
        self.sub_selector.config(
            values=labels, state="readonly" if len(labels) > 1 else "disabled"
        )
        self.sub_selector.set(labels[index] if 0 <= index < len(labels) else "")
    
    def _clear_symbol_selector(self):
        if hasattr(self, "sub_selector"):
            self.sub_selector.config(values=[], state="disabled")
            self.sub_selector.set("")
    
    def _on_sub_selected(self, event=None):
        if self.current_symbol is None or not hasattr(self, "sub_selector"):
            return
        index = self.sub_selector.current()
        if index < 0:
            return
        self.display_symbol(self.current_symbol, sub_index=index)
    
    @staticmethod
    def _symbol_pin_endpoints(pin):
        settings = getattr(pin, "settings", None)
        fallback_x = getattr(settings, "pos_x", 0)
        fallback_y = getattr(settings, "pos_y", 0)
        path = getattr(getattr(pin, "pin_path", None), "path", "")
        match = re.search(
            r"M\s*(-?\d+(?:\.\d+)?)[\s,]+(-?\d+(?:\.\d+)?)\s*([hHvV])\s*"
            r"(-?\d+(?:\.\d+)?)",
            path,
        )
        if not match:
            return (fallback_x, fallback_y), (fallback_x, fallback_y)
        
        x = float(match.group(1))
        y = float(match.group(2))
        delta = float(match.group(4))
        if match.group(3).lower() == "h":
            return (x, y), (x + delta, y)
        return (x, y), (x, y + delta)
    
    @staticmethod
    def _pin_name_position(start, end, offset=8):
        """Place a pin name just inside the symbol body when no position is given."""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.hypot(dx, dy)
        if length == 0:
            return end
        return end[0] + dx / length * offset, end[1] + dy / length * offset
    
    @staticmethod
    def _easyeda_text_anchor(text_anchor):
        return {
            "start": "w",
            "end": "e",
            "middle": "center",
            "center": "center",
        }.get(str(text_anchor).lower(), "center")
    
    def _draw_symbol_points(self, points_str, closed=False):
        if not points_str:
            return
        try:
            values = [float(v) for v in points_str.replace(",", " ").split()]
        except ValueError:
            return
        points = list(zip(values[0::2], values[1::2]))
        if len(points) < 2:
            return
        for start, end in zip(points, points[1:]):
            self.draw_line(start[0], start[1], end[0], end[1], "Shapes", "black")
        if closed and len(points) > 2:
            self.draw_line(
                points[-1][0], points[-1][1], points[0][0], points[0][1], "Shapes", "black"
            )
    
    def draw_line(self, x1, y1, x2, y2, layer, color):
        """Draw a line."""
        if layer not in self.layers:
            self.layers[layer] = True
        
        self.drawing_commands.append(('line', x1, y1, x2, y2, layer, color))
        self._draw_line_impl(x1, y1, x2, y2, layer, color)
    
    def _draw_line_impl(self, x1, y1, x2, y2, layer, color):
        """Implementation of line drawing."""
        x1_s = self._scale_x(x1)
        y1_s = self._scale_y(y1)
        x2_s = self._scale_x(x2)
        y2_s = self._scale_y(y2)
        
        if self.layers.get(layer, True):
            self.canvas.create_line(x1_s, y1_s, x2_s, y2_s, fill=color, width=1, tags=layer)
    
    def draw_rectangle(self, x1, y1, x2, y2, layer, fill, outline):
        """Draw a rectangle."""
        if layer not in self.layers:
            self.layers[layer] = True
        
        self.drawing_commands.append(('rect', x1, y1, x2, y2, layer, fill, outline))
        self._draw_rect_impl(x1, y1, x2, y2, layer, fill, outline)
    
    def _draw_rect_impl(self, x1, y1, x2, y2, layer, fill, outline):
        """Implementation of rectangle drawing."""
        x1_s = self._scale_x(x1)
        y1_s = self._scale_y(y1)
        x2_s = self._scale_x(x2)
        y2_s = self._scale_y(y2)
        
        if self.layers.get(layer, True):
            self.canvas.create_rectangle(x1_s, y1_s, x2_s, y2_s, fill=fill, outline=outline, width=1, tags=layer)
    
    def draw_circle(self, x, y, r, layer, color, fill):
        """Draw a circle."""
        if layer not in self.layers:
            self.layers[layer] = True
        
        self.drawing_commands.append(('circle', x, y, r, layer, color, fill))
        self._draw_circle_impl(x, y, r, layer, color, fill)
    
    def _draw_circle_impl(self, x, y, r, layer, color, fill):
        """Implementation of circle drawing."""
        x_s = self._scale_x(x)
        y_s = self._scale_y(y)
        r_s = abs(r * self.zoom_level)
        
        if self.layers.get(layer, True):
            self.canvas.create_oval(x_s - r_s, y_s - r_s, x_s + r_s, y_s + r_s,
                                   outline=color, fill=fill if fill else "", width=1, tags=layer)
    
    def draw_ellipse(self, x, y, r, layer, fill, outline):
        """Draw an ellipse."""
        self.draw_circle(x, y, r, layer, outline, fill)
    
    def draw_oblong(self, x, y, w, h, layer, fill, outline):
        """Draw an oblong shape."""
        self.draw_rectangle(x, y, x + w, y + h, layer, fill, outline)
    
    def draw_pin(self, x, y, label, layer):
        """Draw a pin."""
        if layer not in self.layers:
            self.layers[layer] = True
        
        self.drawing_commands.append(('pin', x, y, label, layer))
        
        x_s = self._scale_x(x)
        y_s = self._scale_y(y)
        size = 10
        
        if self.layers.get(layer, True):
            self.canvas.create_rectangle(x_s - size, y_s - size, x_s + size, y_s + size,
                                        fill='yellow', outline='orange', width=2, tags=layer)
            self.canvas.create_text(x_s, y_s, text=label, font=("Arial", 7, "bold"), tags=layer)
    
    def draw_text(self, x, y, text, layer="Text", size=7, anchor="center", color="black"):
        """Draw a text label."""
        if layer not in self.layers:
            self.layers[layer] = True
        
        self.drawing_commands.append(('text', x, y, text, layer, size, anchor, color))
        self._draw_text_impl(x, y, text, layer, size, anchor, color)
    
    def _draw_text_impl(self, x, y, text, layer, size, anchor, color):
        x_s = self._scale_x(x)
        y_s = self._scale_y(y)
        
        if self.layers.get(layer, True):
            self.canvas.create_text(
                x_s,
                y_s,
                text=text,
                fill=color,
                font=("Arial", max(6, int(size))),
                anchor=anchor,
                tags=layer,
            )
    
    def _scale_x(self, x):
        """Scale X coordinate."""
        return int(x * self.zoom_level + self.pan_x)
    
    def _scale_y(self, y):
        """Scale Y coordinate."""
        return int(-y * self.zoom_level + self.pan_y)
    
    def _clear_layer_buttons(self):
        """Clear layer buttons."""
        for widget in self.layers_container.winfo_children():
            widget.destroy()
        self.layer_buttons.clear()
    
    def _update_layer_controls(self):
        """Update layer visibility controls."""
        self._clear_layer_buttons()
        
        for layer_name in sorted(self.layers.keys()):
            var = tk.BooleanVar(value=self.layers[layer_name])
            
            def toggle_layer(layer_name=layer_name, var=var):
                self.layers[layer_name] = var.get()
                state = tk.NORMAL if var.get() else tk.HIDDEN
                self.canvas.itemconfig(layer_name, state=state)
            
            cb = tk.Checkbutton(self.layers_container, text=layer_name, variable=var, command=toggle_layer)
            cb.pack(side=tk.LEFT, padx=2)
            self.layer_buttons[layer_name] = (var, cb)
    
    def zoom_in(self):
        """Zoom in."""
        self.zoom_level *= 1.2
        self._redraw()
    
    def zoom_out(self):
        """Zoom out."""
        self.zoom_level /= 1.2
        self._redraw()
    
    def fit_view(self):
        """Fit the drawing to the canvas."""
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
            self.pan_x = 0
            self.pan_y = 0
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
                _, x1, y1, x2, y2, _, _, _ = command
                add(x1, y1)
                add(x2, y2)
            elif kind == "circle":
                _, x, y, radius, _, _, _ = command
                add(x - radius, y - radius)
                add(x + radius, y + radius)
            elif kind == "pin":
                _, x, y, _, _ = command
                add(x, y)
            elif kind == "text":
                _, x, y, _, _, _, _, _ = command
                add(x, y)
        
        if min_x == float("inf"):
            return None
        return min_x, min_y, max_x, max_y
    
    def _redraw(self):
        """Redraw canvas."""
        self.canvas.delete("all")
        
        for cmd in self.drawing_commands:
            if cmd[0] == 'line':
                _, x1, y1, x2, y2, layer, color = cmd
                self._draw_line_impl(x1, y1, x2, y2, layer, color)
            elif cmd[0] == 'rect':
                _, x1, y1, x2, y2, layer, fill, outline = cmd
                self._draw_rect_impl(x1, y1, x2, y2, layer, fill, outline)
            elif cmd[0] == 'circle':
                _, x, y, r, layer, color, fill = cmd
                self._draw_circle_impl(x, y, r, layer, color, fill)
            elif cmd[0] == 'pin':
                _, x, y, label, layer = cmd
                x_s = self._scale_x(x)
                y_s = self._scale_y(y)
                size = 10
                if self.layers.get(layer, True):
                    self.canvas.create_rectangle(x_s - size, y_s - size, x_s + size, y_s + size,
                                                fill='yellow', outline='orange', width=2, tags=layer)
                    self.canvas.create_text(x_s, y_s, text=label, font=("Arial", 7, "bold"), tags=layer)
            elif cmd[0] == 'text':
                _, x, y, text, layer, size, anchor, color = cmd
                self._draw_text_impl(x, y, text, layer, size, anchor, color)
    
    def on_canvas_scroll(self, event):
        """Handle scroll wheel."""
        if event.num == 5 or event.delta < 0:
            self.zoom_out()
        elif event.num == 4 or event.delta > 0:
            self.zoom_in()


def main():
    """Main entry point."""
    root = tk.Tk()
    viewer = EasyedaViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
