"""
EasyEDA Package Viewer using tkinter.
Supports preview for both footprints and symbols from EasyEDA.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import math

from easyeda2xpedition.easyeda.easyeda_api import EasyedaApi
from easyeda2xpedition.easyeda.easyeda_importer import EasyedaFootprintImporter, EasyedaSymbolImporter


class EasyedaViewer:
    """Viewer for EasyEDA components (footprints and symbols)."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("EasyEDA Package Viewer - Footprint & Symbol Preview")
        self.root.geometry("1200x750")
        
        self.canvas = None
        self.layers = {}
        self.layer_buttons = {}
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.drawing_commands = []
        self.current_data = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Top toolbar
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Label(toolbar, text="Package ID:").pack(side=tk.LEFT, padx=5)
        self.id_input = tk.Entry(toolbar, width=15)
        self.id_input.pack(side=tk.LEFT, padx=5)
        self.id_input.bind("<Return>", lambda e: self.load_package())
        
        tk.Button(toolbar, text="Load Footprint", command=self.load_footprint).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Load Symbol", command=self.load_symbol).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Fit View", command=self.fit_view).pack(side=tk.LEFT, padx=2)
        
        # Main canvas
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
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
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_package(self):
        """Load package by ID."""
        package_id = self.id_input.get().strip()
        if not package_id:
            messagebox.showwarning("Warning", "Please enter a package ID")
            return
        self.load_footprint()
    
    def load_footprint(self):
        """Load and display a footprint."""
        package_id = self.id_input.get().strip()
        if not package_id:
            messagebox.showwarning("Warning", "Please enter a package ID")
            return
        
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
    
    def display_symbol(self, symbol):
        """Display a symbol."""
        self.canvas.delete("all")
        self.drawing_commands = []
        self.layers.clear()
        self._clear_layer_buttons()
        
        # Draw rectangles
        for rect in getattr(symbol, "rectangles", []):
            layer = "Shapes"
            if layer not in self.layers:
                self.layers[layer] = True
            
            x = getattr(rect, "pos_x", 0)
            y = getattr(rect, "pos_y", 0)
            w = getattr(rect, "width", 0)
            h = getattr(rect, "height", 0)
            self.draw_rectangle(x, y - h, x + w, y, layer, "lightblue", "blue")
        
        # Draw circles
        for circ in getattr(symbol, "circles", []):
            layer = "Shapes"
            if layer not in self.layers:
                self.layers[layer] = True
            
            x = getattr(circ, "center_x", 0)
            y = getattr(circ, "center_y", 0)
            r = getattr(circ, "radius", 0)
            self.draw_circle(x, y, r, layer, "lightblue", "blue")
        
        # Draw polylines
        for polyline in getattr(symbol, "polylines", []):
            layer = "Shapes"
            if layer not in self.layers:
                self.layers[layer] = True
            
            points_str = getattr(polyline, "points", "")
            if points_str:
                pts = [float(v) for v in points_str.replace(",", " ").split()]
                for i in range(0, len(pts) - 2, 2):
                    self.draw_line(pts[i], pts[i+1], pts[i+2], pts[i+3], layer, "black")
        
        # Draw lines
        for line in getattr(symbol, "lines", []):
            layer = "Shapes"
            if layer not in self.layers:
                self.layers[layer] = True
            
            x1 = getattr(line, "x1", 0)
            y1 = getattr(line, "y1", 0)
            x2 = getattr(line, "x2", 0)
            y2 = getattr(line, "y2", 0)
            self.draw_line(x1, y1, x2, y2, layer, "black")
        
        # Draw pins
        for pin in getattr(symbol, "pins", []):
            layer = "Pins"
            if layer not in self.layers:
                self.layers[layer] = True
            
            x = getattr(pin, "x", 0) if hasattr(pin, "x") else 0
            y = getattr(pin, "y", 0) if hasattr(pin, "y") else 0
            label = getattr(pin, "name", "P") if hasattr(pin, "name") else "P"
            self.draw_pin(x, y, str(label), layer)
        
        self._update_layer_controls()
        self.fit_view()
    
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
    
    def _scale_x(self, x):
        """Scale X coordinate."""
        return int(x * self.zoom_level + self.pan_x + 600)
    
    def _scale_y(self, y):
        """Scale Y coordinate."""
        return int(-y * self.zoom_level + self.pan_y + 350)
    
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
        """Fit to view."""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._redraw()
    
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
