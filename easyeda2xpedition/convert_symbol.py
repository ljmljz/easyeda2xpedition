from easyeda.easyeda_importer import EasyedaSymbolImporter
from easyeda.parameters_easyeda import EeSymbol, EeSymbolPin
from easyeda.easyeda_api import EasyedaApi

from xpedition.symbol.pin import SymbolPinPosition, SymbolPin, SymbolLabel, SymbolAnnotation, SymbolPinGroup
from xpedition.symbol.symbol import Symbol as XpeditionSymbol
from xpedition.symbol.symbol import SymbolShapeLine, SymbolShapeCircle, SymbolShapeArc


def ee_unit_to_th(value: float) -> float:
    return value * 1

class EeSymbolToXpeditionSymbol(object):
    def __init__(self, easyeda_cad_data: dict):
        self.easyeda_cad_data = easyeda_cad_data
        self.easyeda_symbol = EasyedaSymbolImporter(easyeda_cad_data).get_symbol()
        self.xpedition_symbol = XpeditionSymbol(self.easyeda_symbol.info.name)

        self._pin_name_list = []

    def convert(self):
        self.xpedition_symbol.refdes = self.easyeda_symbol.info.prefix
        self.xpedition_symbol.value = self.easyeda_symbol.info.mpn
        self.xpedition_symbol.mfg_name = self.easyeda_symbol.info.manufacturer
        self.xpedition_symbol.mpn = self.easyeda_symbol.info.mpn
        self.xpedition_symbol.dev_name = self.easyeda_symbol.info.name
        self.xpedition_symbol.name = self.easyeda_symbol.info.name
        # self.xpedition_symbol.bbox = self.easyeda_symbol.bbox
        
        self.convert_pin_groups()
        self.convert_shapes()
        
        return self.xpedition_symbol
    
    def _rotate_pin_side(self, original_points, side):
        if side == 0: # top
            return original_points
        elif side == 1: # bottom
            return (original_points[1], original_points[0], original_points[3], original_points[2])
        elif side == 2: # left
            return (original_points[2], original_points[3], original_points[0], original_points[1])
        elif side == 3: # right
            return (original_points[3], original_points[2], original_points[1], original_points[0])
        else:
            raise ValueError("side must be 0, 1, 2 or 3")

    
    def _calc_pin_position(self, pin: EeSymbolPin):
        path = pin.pin_path.path
        side = 0
        rotation = pin.settings.rotation
        # this is a h pin
        if "h" in path:
            path_list = path.replace("M", "").replace("h", "").split()
            x1 = float(path_list[0])
            y1 = float(path_list[1])
            x2 = float(path_list[0]) + float(path_list[2])
            y2 = float(path_list[1])

            if x1 > x2:
                side = 3 # right
                if rotation == 90:
                    x1, y1, x2, y2 = x1, y1, x1, y1 - float(path_list[2])
                    side = 0
                elif rotation == 180:
                    # x1, y1, x2, y2 = x2, y2, x1, y1
                    # side = 2
                    pass
                elif rotation == 270:
                    x1, y1, x2, y2 = x1, y1, x1, y1 + float(path_list[2])
                    side = 1
            else:
                side = 2 # left
                if rotation == 90:
                    x1, y1, x2, y2 = x1, y1, x1, y1 + float(path_list[2])
                    side = 0
                elif rotation == 180:
                    # x1, y1, x2, y2 = x2, y2, x1, y1
                    # side = 3
                    pass
                elif rotation == 270:
                    x1, y1, x2, y2 = x1, y1, x1, y1 - float(path_list[2])
                    side = 1
        else: # this is a v pin
            path_list = path.replace("M", "").replace("v", "").split()
            x1 = float(path_list[0])
            y1 = float(path_list[1])
            x2 = float(path_list[0])
            y2 = float(path_list[1]) + float(path_list[2])

            if y1 > y2:
                side = 1 # bottom
                if rotation == 90:
                    x1, y1, x2, y2 = x1, y1, x1 - float(path_list[2]), y1
                    side = 2
                elif rotation == 180:
                    # x1, y1, x2, y2 = x2, y2, x1, y1
                    side = 0
                elif rotation == 270:
                    x1, y1, x2, y2 = x1, y1, x1 + float(path_list[2]), y1
                    side = 3
            else:
                side = 0 # top
                if rotation == 90:
                    x1, y1, x2, y2 = x1, y1, x1 + float(path_list[2]), y1
                    side = 3
                elif rotation == 180:
                    # x1, y1, x2, y2 = x2, y2, x1, y1
                    side = 1
                elif rotation == 270:
                    x1, y1, x2, y2 = x1, y1, x1 - float(path_list[2]), y1
                    side = 2

        # endx, endy, startx, starty
        return ((x2, y2, x1, y1), side)
    
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
        if side == 0: # top
            return 3 # 270
        elif side == 1: # bottom
            return 1 # 90
        elif side == 2: # left
            return 0 # 0
        elif side == 3: # right
            return 0 # 0
        else:
            raise ValueError("side must be 0, 1, 2 or 3")
        
    def _get_anchor_from_side(self, side):
        if side == 0: # top
            return (2, 3) # middle left
        elif side == 1: # bottom
            return (8, 9) # middle right, lower right
        elif side == 2: # left
            return (2, 3) # lower left
        elif side == 3: # right
            return (8, 9) # lower right
        
    def _get_xpedition_pin_type(self, pin: EeSymbolPin):
        ee_pin_types = ['Undefined', 'Input','Output','I/O','Power']
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
        x = (1 - t)**3 * p0[0] + 3 * (1 - t)**2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
        y = (1 - t)**3 * p0[1] + 3 * (1 - t)**2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
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

    def convert_pin_groups(self):
        bbox = self.easyeda_symbol.bbox
        index = 1

        for pin in self.easyeda_symbol.pins:
            pos, side = self._calc_pin_position(pin)
            sym_pos = SymbolPinPosition(start_x=int(pos[0] - bbox.x), 
                                        start_y=int(bbox.y - pos[1]), 
                                        end_x=int(pos[2] - bbox.x), 
                                        end_y=int(bbox.y - pos[3]))
            xpedition_pin = SymbolPin(index, sym_pos, 0, side=side)

            anchors = self._get_anchor_from_side(side)
            rotation = self._calc_rotation_from_angle(pin.name.rotation)
            xpedition_label = SymbolLabel(self._determine_pin_name(pin), int(pos[0] - bbox.x), int(bbox.y - pos[1]), rotation, anchor=anchors[0])

            rotation = self._calc_rotation_from_angle(pin.number.rotation)
            xpedition_annotation = SymbolAnnotation(f"#={pin.number.text}", int(pos[2] - bbox.x), int(bbox.y - pos[3]), rotation, anchor=anchors[1])

            # create a Xpedtion PIN Group
            pin_group = SymbolPinGroup(xpedition_pin, xpedition_label, [xpedition_annotation])

            xpedition_pin_type = self._get_xpedition_pin_type(pin)
            if xpedition_pin_type is not None:
                xpedition_annotation = SymbolAnnotation(f"PINTYPE={xpedition_pin_type}", 0, 0, 0, visible=0)
                pin_group.add_annotation(xpedition_annotation)

            self.xpedition_symbol.add_pin_group(pin_group)
            index += 1

    def convert_shapes(self):
        bbox = self.easyeda_symbol.bbox
        self.xpedition_symbol.set_bbox(0, int(bbox.width), int(bbox.height), 0)
        # convert rectangles
        for rect in self.easyeda_symbol.rectangles:
            xpedition_line = SymbolShapeLine(int(rect.pos_x - bbox.x), 
                                             int(bbox.y - (rect.pos_y + rect.height)), 
                                             int(rect.pos_x + rect.width - bbox.x), 
                                             int(bbox.y - (rect.pos_y + rect.height)))
            self.xpedition_symbol.add_shape(xpedition_line)

            xpedition_line = SymbolShapeLine(int(rect.pos_x - bbox.x), 
                                             int(bbox.y - rect.pos_y), 
                                             int(rect.pos_x + rect.width - bbox.x), 
                                             int(bbox.y - rect.pos_y))
            self.xpedition_symbol.add_shape(xpedition_line)

            xpedition_line = SymbolShapeLine(int(rect.pos_x - bbox.x), 
                                             int(bbox.y - (rect.pos_y + rect.height)), 
                                             int(rect.pos_x - bbox.x), 
                                             int(bbox.y - rect.pos_y))
            self.xpedition_symbol.add_shape(xpedition_line)

            xpedition_line = SymbolShapeLine(int(rect.pos_x + rect.width - bbox.x), 
                                             int(bbox.y - (rect.pos_y + rect.height)), 
                                             int(rect.pos_x + rect.width - bbox.x), 
                                             int(bbox.y - rect.pos_y))
            self.xpedition_symbol.add_shape(xpedition_line)

        # convert circles
        for circle in self.easyeda_symbol.circles:
            xpedition_circle = SymbolShapeCircle(int(circle.center_x - bbox.x), 
                                                 int(bbox.y - circle.center_y), 
                                                 int(circle.radius))
            self.xpedition_symbol.add_shape(xpedition_circle)

        # convert polylines
        for polyline in self.easyeda_symbol.polylines:
            points = polyline.points.split(" ")
            for i in range(0, len(points) - 2, 2):
                x1 = float(points[i]) - bbox.x
                y1 = bbox.y - float(points[i + 1])
                x2 = float(points[i + 2]) - bbox.x
                y2 = bbox.y - float(points[i + 3])
                xpedition_line = SymbolShapeLine(int(x1), int(y1), int(x2), int(y2))
                self.xpedition_symbol.add_shape(xpedition_line)

        # convert lines
        for line in self.easyeda_symbol.lines:
            xpedition_line = SymbolShapeLine(int(line.x1 - bbox.x), 
                                             int(bbox.y - line.y1), 
                                             int(line.x2 - bbox.x), 
                                             int(bbox.y - line.y2))
            self.xpedition_symbol.add_shape(xpedition_line)

        for arc in self.easyeda_symbol.arcs:
            points = arc.path.replace("M").replace("C").split(" ")
            start_point = (int(float(points[0]) - bbox.x), int(bbox.y - float(points[1])))
            ctrl_point1 = (int(float(points[2]) - bbox.x), int(bbox.y - float(points[3])))
            ctrl_point2 = (int(float(points[4]) - bbox.x), int(bbox.y - float(points[5])))
            end_point = (int(float(points[6]) - bbox.x), int(bbox.y - float(points[7])))
            mid_point = self._cubic_bezier_point(start_point, ctrl_point1, ctrl_point2, end_point, 0.5)

            xpedition_arc = SymbolShapeArc(int(start_point[0]), int(start_point[1]), 
                                          int(mid_point[0]), int(mid_point[1]), 
                                          int(end_point[0]), int(end_point[1]))
            self.xpedition_symbol.add_shape(xpedition_arc)

        for ellipse in self.easyeda_symbol.ellipses:
            xpedition_ellipse = SymbolShapeCircle(int(ellipse.center_x - bbox.x), 
                                                  int(bbox.y - ellipse.center_y), 
                                                  int(ellipse.radius_x))
            self.xpedition_symbol.add_shape(xpedition_ellipse)

    def save_to_file(self, file_path: str):
        with open(file_path, "w") as f:
            sym_string = str(self.xpedition_symbol)
            f.write(sym_string)


if __name__ == "__main__":
    lcsc_id = "C165948"  # 可替换为其它LCSC ID
    cad_data = EasyedaApi().get_cad_data_of_component(lcsc_id)
    converter = EeSymbolToXpeditionSymbol(cad_data)
    converter.convert()
    converter.save_to_file(f"..\\output\\{lcsc_id}_xpedition.1")
