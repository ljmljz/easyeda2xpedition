from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QFileDialog, QVBoxLayout, QWidget, QPushButton, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QGraphicsEllipseItem, QCheckBox, QHBoxLayout
from PyQt5.QtCore import QRectF
import sys

class HKPViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HKP File Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.layers = {}  # Store layers and their visibility
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.graphics_view = QGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.graphics_view.setScene(self.scene)
        layout.addWidget(self.graphics_view)

        load_button = QPushButton("Load HKP File", self)
        load_button.clicked.connect(self.load_hkp_file)
        layout.addWidget(load_button)

        self.layer_controls = QHBoxLayout()  # Layout for layer visibility controls
        layout.addLayout(self.layer_controls)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_hkp_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open HKP File", "", "HKP Files (*.hkp);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'r', encoding='latin-1') as file:  # Changed encoding to 'latin-1'
                    content = file.readlines()
                    self.parse_hkp_file(content)
            except UnicodeDecodeError as e:
                self.scene.clear()
                self.scene.addText(f"Error reading file: {e}")
                print(f"Error reading file: {e}")

    def parse_hkp_file(self, lines):
        self.scene.clear()
        self.layers.clear()
        self.layer_controls.setParent(None)  # Clear existing layer controls
        self.layer_controls = QHBoxLayout()

        lines = iter(lines)  # Convert lines to an iterator
        for line in lines:
            line = line.strip()
            if line.startswith(".PAD"):
                pad_name = line.split('"')[1]
                shape_line = next(lines).strip()
                layer_name = f"Layer_{pad_name}"  # Generate layer name
                self.layers[layer_name] = True  # Default visibility is True

                checkbox = QCheckBox(layer_name, self)
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(lambda state, layer=layer_name: self.toggle_layer_visibility(layer, state))
                self.layer_controls.addWidget(checkbox)

                if "..SQUARE" in shape_line:
                    width = float(next(lines).strip().split()[1])
                    item = QGraphicsRectItem(QRectF(0, 0, width, width))
                    item.setData(0, layer_name)  # Associate item with layer
                    self.scene.addItem(item)
                elif "..RECTANGLE" in shape_line:
                    width = float(next(lines).strip().split()[1])
                    height = float(next(lines).strip().split()[1])
                    item = QGraphicsRectItem(QRectF(0, 0, width, height))
                    item.setData(0, layer_name)
                    self.scene.addItem(item)
                elif "..ROUND" in shape_line:
                    diameter = float(next(lines).strip().split()[1])
                    item = QGraphicsEllipseItem(QRectF(0, 0, diameter, diameter))
                    item.setData(0, layer_name)
                    self.scene.addItem(item)
                elif "..OBLONG" in shape_line:
                    width = float(next(lines).strip().split()[1])
                    height = float(next(lines).strip().split()[1])
                    item = QGraphicsRectItem(QRectF(0, 0, width, height))
                    item.setData(0, layer_name)
                    self.scene.addItem(item)

        self.centralWidget().layout().addLayout(self.layer_controls)  # Add updated layer controls

    def toggle_layer_visibility(self, layer_name, state):
        self.layers[layer_name] = bool(state)
        for item in self.scene.items():
            if item.data(0) == layer_name:
                item.setVisible(self.layers[layer_name])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = HKPViewer()
    viewer.show()
    sys.exit(app.exec_())