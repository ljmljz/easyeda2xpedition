import random

from xpedition.symbol.pin import SymbolPinGroup


class SymbolShapeBase(object):
    def __init__(self):
        self.color = 2


class SymbolShapeLine(SymbolShapeBase):
    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.color = 2

    def __str__(self):
        line_string = "l "
        line_string += f"{self.color} "
        line_string += f"{self.x1} {self.y1} "
        line_string += f"{self.x2} {self.y2}\n"
        line_string += "|GRPHSTL -1 0 0 1\n"

        return line_string
    
class SymbolShapeCircle(SymbolShapeBase):
    def __init__(self, x: float, y: float, radius: float):
        self.x = x
        self.y = y
        self.radius = radius

    def __str__(self):
        circle_string = "c "
        circle_string += f"{self.x} {self.y} {self.radius}\n"
        circle_string += "|GRPHSTL_EXT01 255 -1 0 1 1\n"

        return circle_string
    

class SymbolShapeArc(SymbolShapeBase):
    def __init__(self, start_x: float, start_y: float, mid_x: float, mid_y: float, end_x: float, end_y: float):
        self.start_x = start_x
        self.start_y = start_y
        self.mid_x = mid_x
        self.mid_y = mid_y
        self.end_x = end_x
        self.end_y = end_y

    def __str__(self):
        arc_string = "a "
        arc_string += f"{self.start_x} {self.start_y} "
        arc_string += f"{self.mid_x} {self.mid_y} "
        arc_string += f"{self.end_x} {self.end_y}\n"
        arc_string += "|GRPHSTL_EXT01 255 -1 0 1 1\n"
        return arc_string
    
class Symbol(object):
    def __init__(self, name: str, dev_name: str = "", mfg_name: str = "", mpn: str = "", refdes: str = "U?", value: str = "Value?"):
        self.name = name
        self.dev_name = dev_name
        self.mfg_name = mfg_name
        self.mpn = mpn
        self.refdes = refdes
        self.value = value
        self.pin_groups = []
        self.shapes = []
        self.bbox = (0, 0, 0, 0)

    def _calc_bbox(self):
        min_pin_x = min(self.pin_groups, key=lambda x: x.pin.pos.end_x)
        min_pin_y = min(self.pin_groups, key=lambda x: x.pin.pos.end_y)
        max_pin_x = max(self.pin_groups, key=lambda x: x.pin.pos.end_x)
        max_pin_y = max(self.pin_groups, key=lambda x: x.pin.pos.end_y)

        min_line_x = min(self.lines, key=lambda x: x.x1)
        min_line_y = min(self.lines, key=lambda x: x.y1)
        max_line_x = max(self.lines, key=lambda x: x.x2)
        max_line_y = max(self.lines, key=lambda x: x.y2)

        min_x = min(min_pin_x, min_line_x)
        min_y = min(min_pin_y, min_line_y)
        max_x = max(max_pin_x, max_line_x)
        max_y = max(max_pin_y, max_line_y)

        self.bbox = (min_x, min_y, max_x, max_y)

    def add_pin_group(self, group: SymbolPinGroup):
        self.pin_groups.append(group)

    def add_shape(self, shape: SymbolShapeBase):
        self.shapes.append(shape)

    def set_bbox(self, x: int, width: int, height: int, y: int ):
        self.bbox = (x, width, height, y)

    def __str__(self):
        # self._calc_bbox()

        sym_string = "V 50\n"
        sym_string += f"K {random.randint(1000000000, 9999999999)} {self.name}\n"
        sym_string += "Y 1\n"
        sym_string += f"D {self.bbox[0]} {self.bbox[1]} {self.bbox[2]} {self.bbox[3]}\n"
        sym_string += "Z 0\n"
        sym_string += "i 0\n"

        sym_string += f"U 0 0 10 0 5 0 {self.name}\n"
        sym_string += "U 0 0 5 0 5 0 Copyright=EasyEDA to Xpedition\n"
        if self.mfg_name:
            sym_string += f"U 0 0 5 0 5 0 Mfr_name={self.mfg_name}\n"
        if self.mpn:
            sym_string += f"U 0 0 5 0 5 0 Manufacturer_Part_Number={self.mpn}\n"

        for pin_group in self.pin_groups:
            sym_string += str(pin_group)

        for shape in self.shapes:
            sym_string += str(shape)

        sym_string += f"U 140 40 8 0 5 3 REFDES={self.refdes.upper()}\n"
        sym_string += "U 140 30 8 0 5 0 TYPE=Type?\n"
        sym_string += f"U 140 30 8 0 5 0 VALUE={self.value}\n"
        sym_string += "E\n"

        return sym_string


