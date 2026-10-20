"""
Xpedition HKP File Viewer using tkinter.
Supports preview for both footprints and symbols.
"""

import tkinter as tk
from tkinter import filedialog, messagebox


class XpeditionViewer:
    """Viewer for Xpedition HKP files (footprints and symbols)."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Xpedition HKP Viewer - Footprint & Symbol Preview")
        self.root.geometry("1000x700")
        
        self.canvas = None
        self.layers = {}  # Store layer visibility state
        self.layer_buttons = {}  # Store layer toggle buttons
        self.view_type = None  # 'footprint' or 'symbol'
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.drawing_commands = []  # Store drawing commands for redraw
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Top toolbar
        toolbar = tk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Button(toolbar, text="Load HKP File", command=self.load_hkp_file).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Fit View", command=self.fit_view).pack(side=tk.LEFT, padx=2)
        tk.Button(toolbar, text="Clear View", command=self.clear_view).pack(side=tk.LEFT, padx=2)
        
        # Main canvas
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="white", cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<MouseWheel>", self.on_canvas_scroll)
        self.canvas.bind("<Button-4>", self.on_canvas_scroll)  # Linux scroll up
        self.canvas.bind("<Button-5>", self.on_canvas_scroll)  # Linux scroll down
        
        # Layer controls frame
        controls_frame = tk.Frame(self.root)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        tk.Label(controls_frame, text="Layers:").pack(side=tk.LEFT, padx=5)
        
        # Scrollable layer controls
        self.layers_container = tk.Frame(controls_frame)
        self.layers_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_hkp_file(self):
        """Load and display an HKP file."""
        file_path = filedialog.askopenfilename(
            title="Open HKP File",
            filetypes=[("HKP Files", "*.hkp"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                self.parse_hkp_file(content)
                self.status_var.set(f"Loaded: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {e}")
                self.status_var.set(f"Error: {str(e)}")
    
    def parse_hkp_file(self, content):
        """Parse and display HKP file content."""
        self.clear_view()
        self.drawing_commands = []
        lines = content.strip().split('\n')
        
        file_type = self._detect_file_type(lines)
        if file_type == 'cell':
            self._parse_cell_file(lines)
        elif file_type == 'padstack':
            self._parse_padstack_file(lines)
        elif file_type == 'symbol':
            self._parse_symbol_file(lines)
        else:
            messagebox.showwarning("Warning", "Unknown file format")
        
        self.fit_view()
    
    def _detect_file_type(self, lines):
        """Detect the type of HKP file."""
        for line in lines[:20]:
            if '.CELL_LIBRARY' in line or '.PACKAGE_CELL' in line:
                return 'cell'
            elif '.PADSTACK_LIBRARY' in line:
                return 'padstack'
            elif '.SYMBOL' in line or 'V 50' in line:
                return 'symbol'
        return 'unknown'
    
    def _parse_cell_file(self, lines):
        """Parse a cell (footprint) file."""
        self.view_type = 'footprint'
        self.layers.clear()
        self._clear_layer_buttons()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('.PACKAGE_CELL'):
                # Extract package name
                self.status_var.set(f"Footprint: {line}")
            
            elif line.startswith('.PIN '):
                # Draw pins
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        pin_num = parts[1]
                        x = float(parts[2])
                        y = float(parts[3])
                        self.draw_pin(x, y, f"P{pin_num}")
                    except ValueError:
                        pass
            
            i += 1
        
        # Add layer controls
        self._update_layer_controls()
    
    def _parse_symbol_file(self, lines):
        """Parse a symbol file."""
        self.view_type = 'symbol'
        self.layers.clear()
        self._clear_layer_buttons()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Parse symbol shapes
            if line.startswith('L '):  # Line
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        x1, y1, x2, y2 = map(float, parts[1:5])
                        self.draw_line(x1, y1, x2, y2)
                    except ValueError:
                        pass
            
            elif line.startswith('C '):  # Circle
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        x, y, r = map(float, parts[1:4])
                        self.draw_circle(x, y, r)
                    except ValueError:
                        pass
            
            elif line.startswith('A '):  # Arc
                parts = line.split()
                if len(parts) >= 7:
                    try:
                        x1, y1, x2, y2, x3, y3 = map(float, parts[1:7])
                        self.draw_arc(x1, y1, x2, y2, x3, y3)
                    except ValueError:
                        pass
            
            elif line.startswith('U '):  # Pin annotation
                self._parse_pin_annotation(line)
            
            i += 1
        
        self._update_layer_controls()
    
    def _parse_padstack_file(self, lines):
        """Parse a padstack file."""
        self.view_type = 'footprint'
        self.status_var.set("Padstack: Viewing pad definitions")
        
        for line in lines:
            line = line.strip()
            if line.startswith('.PAD '):
                parts = line.split('"')
                if len(parts) >= 2:
                    pad_name = parts[1]
                    self.layers[f"Pad: {pad_name}"] = True
        
        self._update_layer_controls()
    
    def _parse_pin_annotation(self, line):
        """Parse pin annotation."""
        parts = line.split()
        if len(parts) >= 3:
            try:
                x, y = float(parts[1]), float(parts[2])
                text = ' '.join(parts[4:]) if len(parts) > 4 else "P"
                self.draw_text(x, y, text)
            except (ValueError, IndexError):
                pass
    
    def draw_pin(self, x, y, label="P", size=15):
        """Draw a pin at specified coordinates."""
        layer = 'Pins'
        if layer not in self.layers:
            self.layers[layer] = True
        
        self.drawing_commands.append(('pin', x, y, label, size, layer))
        self._draw_pin_impl(x, y, label, size, layer)
    
    def _draw_pin_impl(self, x, y, label, size, layer):
        """Implementation of pin drawing."""
        x_scaled = self._scale_x(x)
        y_scaled = self._scale_y(y)
        
        if self.layers.get(layer, True):
            self.canvas.create_rectangle(
                x_scaled - size, y_scaled - size,
                x_scaled + size, y_scaled + size,
                fill='yellow', outline='orange', width=2, tags=layer
            )
            self.canvas.create_text(
                x_scaled, y_scaled, text=label, font=("Arial", 8, "bold"),
                tags=layer
            )
    
    def draw_line(self, x1, y1, x2, y2, layer='Shapes'):
        """Draw a line."""
        if layer not in self.layers:
            self.layers[layer] = True
        
        self.drawing_commands.append(('line', x1, y1, x2, y2, layer))
        self._draw_line_impl(x1, y1, x2, y2, layer)
    
    def _draw_line_impl(self, x1, y1, x2, y2, layer):
        """Implementation of line drawing."""
        x1_scaled = self._scale_x(x1)
        y1_scaled = self._scale_y(y1)
        x2_scaled = self._scale_x(x2)
        y2_scaled = self._scale_y(y2)
        
        if self.layers.get(layer, True):
            self.canvas.create_line(
                x1_scaled, y1_scaled, x2_scaled, y2_scaled,
                fill='black', width=1, tags=layer
            )
    
    def draw_circle(self, x, y, r, layer='Shapes'):
        """Draw a circle."""
        if layer not in self.layers:
            self.layers[layer] = True
        
        self.drawing_commands.append(('circle', x, y, r, layer))
        self._draw_circle_impl(x, y, r, layer)
    
    def _draw_circle_impl(self, x, y, r, layer):
        """Implementation of circle drawing."""
        x_scaled = self._scale_x(x)
        y_scaled = self._scale_y(y)
        r_scaled = abs(r * self.zoom_level)
        
        if self.layers.get(layer, True):
            self.canvas.create_oval(
                x_scaled - r_scaled, y_scaled - r_scaled,
                x_scaled + r_scaled, y_scaled + r_scaled,
                outline='black', width=1, tags=layer
            )
    
    def draw_arc(self, x1, y1, x2, y2, x3, y3, layer='Shapes'):
        """Draw an arc."""
        if layer not in self.layers:
            self.layers[layer] = True
        
        self.drawing_commands.append(('arc', x1, y1, x2, y2, x3, y3, layer))
        self._draw_line_impl(x1, y1, x3, y3, layer)
    
    def draw_text(self, x, y, text, layer='Text'):
        """Draw text annotation."""
        if layer not in self.layers:
            self.layers[layer] = True
        
        self.drawing_commands.append(('text', x, y, text, layer))
        
        x_scaled = self._scale_x(x)
        y_scaled = self._scale_y(y)
        
        if self.layers.get(layer, True):
            self.canvas.create_text(
                x_scaled, y_scaled, text=text, font=("Arial", 8),
                tags=layer
            )
    
    def _scale_x(self, x):
        """Scale X coordinate for canvas."""
        return int(x * self.zoom_level + self.pan_x + 500)
    
    def _scale_y(self, y):
        """Scale Y coordinate for canvas."""
        return int(-y * self.zoom_level + self.pan_y + 300)
    
    def _clear_layer_buttons(self):
        """Clear layer control buttons."""
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
            
            cb = tk.Checkbutton(self.layers_container, text=layer_name, variable=var,
                               command=toggle_layer)
            cb.pack(side=tk.LEFT, padx=2)
            self.layer_buttons[layer_name] = (var, cb)
    
    def zoom_in(self):
        """Increase zoom level."""
        self.zoom_level *= 1.2
        self._redraw()
    
    def zoom_out(self):
        """Decrease zoom level."""
        self.zoom_level /= 1.2
        self._redraw()
    
    def fit_view(self):
        """Fit content to view."""
        self.zoom_level = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._redraw()
    
    def clear_view(self):
        """Clear the canvas."""
        self.canvas.delete("all")
        self.layers.clear()
        self._clear_layer_buttons()
        self.view_type = None
        self.drawing_commands = []
    
    def _redraw(self):
        """Redraw canvas with current transformations."""
        self.canvas.delete("all")
        
        for cmd in self.drawing_commands:
            if cmd[0] == 'line':
                _, x1, y1, x2, y2, layer = cmd
                self._draw_line_impl(x1, y1, x2, y2, layer)
            elif cmd[0] == 'circle':
                _, x, y, r, layer = cmd
                self._draw_circle_impl(x, y, r, layer)
            elif cmd[0] == 'pin':
                _, x, y, label, size, layer = cmd
                self._draw_pin_impl(x, y, label, size, layer)
            elif cmd[0] == 'text':
                _, x, y, text, layer = cmd
                x_scaled = self._scale_x(x)
                y_scaled = self._scale_y(y)
                if self.layers.get(layer, True):
                    self.canvas.create_text(
                        x_scaled, y_scaled, text=text, font=("Arial", 8),
                        tags=layer
                    )
    
    def on_canvas_scroll(self, event):
        """Handle canvas scroll for zooming."""
        if event.num == 5 or event.delta < 0:
            self.zoom_out()
        elif event.num == 4 or event.delta > 0:
            self.zoom_in()


def main():
    """Main entry point."""
    root = tk.Tk()
    viewer = XpeditionViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()