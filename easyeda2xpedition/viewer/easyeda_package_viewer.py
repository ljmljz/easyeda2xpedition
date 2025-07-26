import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
    QGraphicsScene, QGraphicsView, QCheckBox, QHBoxLayout, QLabel, QLineEdit
)
from PyQt5.QtGui import QColor, QBrush, QPen, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPointF
# 导入easyeda_api
from easyeda.easyeda_api import EasyedaApi
from easyeda.easyeda_importer import EasyedaFootprintImporter
from PyQt5.QtGui import QPainterPath
import re

# 颜色映射
LAYER_COLORS = {
    "top": QColor(255, 0, 0, 120),
    "top_paste": QColor(0, 255, 0, 120),
    "top_silk": QColor(0, 0, 255, 120),
    "top_mask": QColor(255, 255, 0, 120),
    "bottom": QColor(255, 0, 255, 120),
    "bottom_paste": QColor(0, 255, 255, 120),
    "bottom_silk": QColor(128, 0, 255, 120),
    "bottom_mask": QColor(255, 128, 0, 120),
    "outline": QColor(0, 0, 0, 255),
}
OBJ_COLORS = {
    "pad": QColor(255, 128, 0, 180),
    "text": QColor(0, 0, 0, 255),
    "default": QColor(128, 128, 128, 120),
}

def fetch_easyeda_footprint(package_id):
    api = EasyedaApi()
    cad_data = api.get_cad_data_of_component(package_id)
    if not cad_data:
        raise Exception("No CAD data found in EasyEDA API response")
    importer = EasyedaFootprintImporter(cad_data)
    return importer.get_footprint()

def get_layer_name(layer_id, footprint):
    # 从footprint.info.layers查找layer_id对应的layer_name
    if hasattr(footprint.info, "layers"):
        for l in footprint.info.layers:
            if hasattr(l, "layer_id") and int(l.layer_id) == int(layer_id):
                return getattr(l, "layer_name", str(layer_id))
            if isinstance(l, dict) and int(l.get("layer_id", -1)) == int(layer_id):
                return l.get("layer_name", str(layer_id))
    return str(layer_id)

class EasyEDAPackageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EasyEDA Package Viewer")
        self.setGeometry(100, 100, 1000, 700)
        self.layers = {}
        self.layer_items = {}
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        top_bar = QHBoxLayout()

        self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("Enter EasyEDA Package ID")
        top_bar.addWidget(QLabel("Package ID:"))
        top_bar.addWidget(self.id_input)

        load_btn = QPushButton("Load Package", self)
        load_btn.clicked.connect(self.load_package)
        top_bar.addWidget(load_btn)

        layout.addLayout(top_bar)

        self.graphics_view = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        layout.addWidget(self.graphics_view)

        self.layer_controls = QHBoxLayout()
        layout.addLayout(self.layer_controls)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def svg_path_to_qpainterpath(self, svg_path_str):
        path = QPainterPath()
        tokens = re.findall(r'[MmLlHhVvZz]|-?\d*\.?\d+(?:e[-+]?\d+)?', svg_path_str)
        i = 0
        current_pos = QPointF(0, 0)
        start_point = QPointF(0, 0)
        while i < len(tokens):
            cmd = tokens[i]
            if cmd in 'Mm':
                i += 1
                x = float(tokens[i])
                i += 1
                y = float(tokens[i])
                current_pos = QPointF(x, y)
                path.moveTo(current_pos)
                start_point = QPointF(x, y)
                i += 1
            elif cmd in 'Ll':
                i += 1
                x = float(tokens[i])
                i += 1
                y = float(tokens[i])
                current_pos = QPointF(x, y)
                path.lineTo(current_pos)
                i += 1
            elif cmd in 'Hh':
                i += 1
                x = float(tokens[i])
                current_pos.setX(x)
                path.lineTo(current_pos)
                i += 1
            elif cmd in 'Vv':
                i += 1
                y = float(tokens[i])
                current_pos.setY(y)
                path.lineTo(current_pos)
                i += 1
            elif cmd in 'Zz':
                path.closeSubpath()
                current_pos = start_point
                i += 1
            else:
                # If number, treat as L
                x = float(tokens[i])
                i += 1
                y = float(tokens[i])
                current_pos = QPointF(x, y)
                path.lineTo(current_pos)
                i += 1
        return path

    def load_package(self):
        package_id = self.id_input.text().strip()
        if not package_id:
            return
        try:
            footprint = fetch_easyeda_footprint(package_id)
            self.display_footprint(footprint)
        except Exception as e:
            self.scene.clear()
            self.scene.addText(f"Error: {e}")

    def display_footprint(self, footprint):
        self.scene.clear()
        self.layers = {}
        self.layer_items = {}
        # 清除旧的layer控件
        while self.layer_controls.count():
            item = self.layer_controls.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 收集所有对象，按layer分组
        def add_to_layer(layer_name, item):
            if layer_name not in self.layers:
                self.layers[layer_name] = True
                self.layer_items[layer_name] = []
            self.layer_items[layer_name].append(item)

        # Pads
        for pad in getattr(footprint, "pads", []):
            layer_name = get_layer_name(getattr(pad, "layer_id", 0), footprint)
            color = OBJ_COLORS.get("pad", QColor(255, 128, 0, 180))
            x = getattr(pad, "center_x", 0)
            y = getattr(pad, "center_y", 0)
            w = getattr(pad, "width", 0)
            h = getattr(pad, "height", 0)
            shape = getattr(pad, "shape", "").lower()
            item = None
            if shape == "ellipse":
                item = self.scene.addEllipse(x - w/2, y - h/2, w, h, QPen(color), QBrush(color))
            elif shape == "rect":
                item = self.scene.addRect(x - w/2, y - h/2, w, h, QPen(color), QBrush(color))
            elif shape == "oval":
                # "oval" (racetrack/obround) pad: draw as a rectangle with semicircle ends using QPainterPath
                path = QPainterPath()
                if w > h:
                    # Horizontal obround
                    rx = h / 2
                    path.moveTo(x - w/2 + rx, y - h/2)
                    path.lineTo(x + w/2 - rx, y - h/2)
                    # Arc at right end (top to bottom, sweep 180 deg CCW)
                    path.arcTo(x + w/2 - h, y - h/2, h, h, 90, 180)
                    path.lineTo(x - w/2 + rx, y + h/2)
                    # Arc at left end (bottom to top, sweep 180 deg CCW)
                    path.arcTo(x - w/2, y - h/2, h, h, 270, 180)
                    path.closeSubpath()
                elif h > w:
                    # Vertical obround
                    ry = w / 2
                    path.moveTo(x - w/2, y - h/2 + ry)
                    path.lineTo(x - w/2, y + h/2 - ry)
                    # Arc at bottom (left to right, sweep 180 deg CCW)
                    path.arcTo(x - w/2, y + h/2 - w, w, w, 180, 180)
                    path.lineTo(x + w/2, y - h/2 + ry)
                    # Arc at top (right to left, sweep 180 deg CCW)
                    path.arcTo(x - w/2, y - h/2, w, w, 0, 180)
                    path.closeSubpath()
                else:
                    # If w == h, treat as circle
                    path.addEllipse(x - w/2, y - h/2, w, h)
                item = self.scene.addPath(path, QPen(color), QBrush(color))
            elif shape == "polygon":
                points = getattr(pad, "points", "")
                if points:
                    qp_path = self.svg_path_to_qpainterpath(points)
                    item = self.scene.addPath(qp_path, QPen(color), QBrush(color))
            
            if item:
                item.setData(0, layer_name)
                add_to_layer(layer_name, item)

            # Draw hole if present in pad
            hole_radius = getattr(pad, "hole_radius", 0)
            hole_points = getattr(pad, "hole_point", "")
            if hole_points:
                # hole_points存在时，hole_radius为半径，hole_points为相对pad中心的多个点
                hx = getattr(pad, "center_x", 0)
                hy = getattr(pad, "center_y", 0)
                hole_color = QColor(80, 80, 80, 180)
                # hole_points格式: "x1 y1 x2 y2 ..."
                pts = [float(v) for v in hole_points.replace(",", " ").split()]
                for i in range(0, len(pts) - 2, 2):
                    x1, y1, x2, y2 = pts[i], pts[i+1], pts[i+2], pts[i+3]
                    hole_item = self.scene.addLine(x1, y1, x2, y2, QPen(hole_color, hole_radius * 2, Qt.SolidLine, Qt.RoundCap))

                    hole_item.setData(0, "hole")
                    add_to_layer("hole", hole_item)
            elif hole_radius and hole_radius > 0:
                hx = getattr(pad, "center_x", 0)
                hy = getattr(pad, "center_y", 0)
                hole_color = QColor(80, 80, 80, 180)
                hole_item = self.scene.addEllipse(hx - hole_radius, hy - hole_radius, hole_radius * 2, hole_radius * 2, QPen(hole_color), QBrush(Qt.NoBrush))
                hole_item.setData(0, "hole")
                add_to_layer("hole", hole_item)

        # Rectangles
        for rect in getattr(footprint, "rectangles", []):
            layer_name = get_layer_name(getattr(rect, "layer_id", 0), footprint)
            color = LAYER_COLORS.get(layer_name, QColor(128, 128, 128, 80))
            x = getattr(rect, "x", 0)
            y = getattr(rect, "y", 0)
            w = getattr(rect, "width", 0)
            h = getattr(rect, "height", 0)
            item = self.scene.addRect(x, y, w, h, QPen(color), QBrush(color))
            item.setData(0, layer_name)
            add_to_layer(layer_name, item)

        # Circles
        for circ in getattr(footprint, "circles", []):
            layer_name = get_layer_name(getattr(circ, "layer_id", 0), footprint)
            color = LAYER_COLORS.get(layer_name, QColor(128, 128, 128, 80))
            cx = getattr(circ, "cx", 0)
            cy = getattr(circ, "cy", 0)
            r = getattr(circ, "radius", 0)
            item = self.scene.addEllipse(cx - r, cy - r, r * 2, r * 2, QPen(color), QBrush(Qt.NoBrush))
            item.setData(0, layer_name)
            add_to_layer(layer_name, item)

        # Arcs (not fully supported, just as lines)
        for arc in getattr(footprint, "arcs", []):
            layer_name = get_layer_name(getattr(arc, "layer_id", 0), footprint)
            color = LAYER_COLORS.get(layer_name, QColor(128, 128, 128, 80))
            # arc.path is SVG path, not directly supported, skip or implement if needed
            continue

        # Tracks (as polylines)
        for track in getattr(footprint, "tracks", []):
            layer_name = get_layer_name(getattr(track, "layer_id", 0), footprint)
            color = LAYER_COLORS.get(layer_name, QColor(128, 128, 128, 80))
            points = getattr(track, "points", "")
            if points:
                pts = [float(x) for x in points.replace(",", " ").split()]
                for i in range(0, len(pts) - 2, 2):
                    x1, y1, x2, y2 = pts[i], pts[i+1], pts[i+2], pts[i+3]
                    item = self.scene.addLine(x1, y1, x2, y2, QPen(color, 1))
                    item.setData(0, layer_name)
                    add_to_layer(layer_name, item)

        # Texts
        for text in getattr(footprint, "texts", []):
            layer_name = get_layer_name(getattr(text, "layer_id", 0), footprint)
            color = OBJ_COLORS.get("text", QColor(0, 0, 0, 255))
            x = getattr(text, "center_x", 0)
            y = getattr(text, "center_y", 0)
            font_size = getattr(text, "font_size", 10)
            content = getattr(text, "text", "")
            font = QFont("Arial", int(font_size))
            item = self.scene.addText(content, font)
            item.setDefaultTextColor(color)
            item.setPos(x, y)
            item.setData(0, layer_name)
            add_to_layer(layer_name, item)

        # Holes (as circles)
        for hole in getattr(footprint, "holes", []):
            x = getattr(hole, "center_x", 0)
            y = getattr(hole, "center_y", 0)
            r = getattr(hole, "radius", 0)
            color = QColor(80, 80, 80, 180)
            item = self.scene.addEllipse(x - r, y - r, r * 2, r * 2, QPen(color), QBrush(Qt.NoBrush))
            item.setData(0, "hole")
            add_to_layer("hole", item)

        # Solid regions, copper areas, vias 可按需补充
        for region in getattr(footprint, "solid_regions", []):
            layer_name = get_layer_name(getattr(region, "layer_id", 0), footprint)
            color = LAYER_COLORS.get(layer_name, QColor(128, 128, 128, 80))
            points = getattr(region, "points", "")
            if points:
                qp_path = self.svg_path_to_qpainterpath(points)
                item = self.scene.addPath(qp_path, QPen(color), QBrush(color))
                item.setData(0, layer_name)
                add_to_layer(layer_name, item)

        for area in getattr(footprint, "copper_areas", []):
            layer_name = get_layer_name(getattr(area, "layer_id", 0), footprint)
            color = LAYER_COLORS.get(layer_name, QColor(128, 128, 128, 80))
            points = getattr(area, "points", "")
            if points:
                qp_path = self.svg_path_to_qpainterpath(points)
                item = self.scene.addPath(qp_path, QPen(color), QBrush(color))
                item.setData(0, layer_name)
                add_to_layer(layer_name, item)

        for via in getattr(footprint, "vias", []):
            layer_name = get_layer_name(getattr(via, "layer_id", 0), footprint)
            color = LAYER_COLORS.get(layer_name, QColor(128, 128, 128, 80))
            x = getattr(via, "center_x", 0)
            y = getattr(via, "center_y", 0)
            r = getattr(via, "radius", 0)
            item = self.scene.addEllipse(x - r, y - r, r * 2, r * 2, QPen(color), QBrush(Qt.NoBrush))
            item.setData(0, layer_name)
            add_to_layer(layer_name, item)

        # 创建layer控件
        for layer_name in self.layer_items:
            checkbox = QCheckBox(layer_name)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, l=layer_name: self.toggle_layer(l, state))
            self.layer_controls.addWidget(checkbox)

        self.graphics_view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)

    def toggle_layer(self, layer_name, state):
        visible = bool(state)
        for item in self.layer_items.get(layer_name, []):
            item.setVisible(visible)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = EasyEDAPackageViewer()
    viewer.show()
    sys.exit(app.exec_())
