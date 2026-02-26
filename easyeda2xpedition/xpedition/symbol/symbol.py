import random

from xpedition.symbol.pin import SymbolPinGroup


class SymbolPart(object):
    """Represents a single part within a symbol that may have multiple subparts."""
    def __init__(self, name: str):
        self.name = name
        self.pin_groups = []
        self.shapes = []
        self.bbox = (0, 0, 0, 0)

    def add_pin_group(self, group: SymbolPinGroup):
        self.pin_groups.append(group)

    def add_shape(self, shape: 'SymbolShapeBase'):
        self.shapes.append(shape)

    def set_bbox(self, x: int, width: int, height: int, y: int):
        self.bbox = (x, width, height, y)

    def move(self, dx: float, dy: float):
        """Move all elements in the part by the given offset."""
        for pin_group in self.pin_groups:
            pin_group.move(dx, dy)
        for shape in self.shapes:
            shape.move(dx, dy)
        # Update bbox
        self.bbox = (self.bbox[0] + dx, self.bbox[1] + dy, self.bbox[2] + dx, self.bbox[3] + dy)

    def __str__(self):
        part_string = ""
        
        part_string += f"D {self.bbox[0]} {self.bbox[1]} {self.bbox[2]} {self.bbox[3]}\n"
        
        for pin_group in self.pin_groups:
            part_string += str(pin_group)

        for shape in self.shapes:
            part_string += str(shape)

        return part_string



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

    def move(self, dx: float, dy: float):
        """Move the line by the given offset."""
        self.x1 += dx
        self.y1 += dy
        self.x2 += dx
        self.y2 += dy

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

    def move(self, dx: float, dy: float):
        """Move the circle by the given offset."""
        self.x += dx
        self.y += dy

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

    def move(self, dx: float, dy: float):
        """Move the arc by the given offset."""
        self.start_x += dx
        self.start_y += dy
        self.mid_x += dx
        self.mid_y += dy
        self.end_x += dx
        self.end_y += dy

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
        self.parts = {}  # Dictionary of part_name -> SymbolPart
        self.pin_groups = []  # For backward compatibility (single part)
        self.shapes = []      # For backward compatibility (single part)
        self.bbox = (0, 0, 0, 0)

    def _get_or_create_part(self, part_name: str):
        """Get or create a part within this symbol."""
        if part_name not in self.parts:
            self.parts[part_name] = SymbolPart(part_name)
        return self.parts[part_name]

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

    def add_pin_group(self, group: SymbolPinGroup, part_name: str = None):
        """Add a pin group to a specific part or to the main symbol."""
        if part_name is None:
            self.pin_groups.append(group)
        else:
            part = self._get_or_create_part(part_name)
            part.add_pin_group(group)

    def add_shape(self, shape: 'SymbolShapeBase', part_name: str = None):
        """Add a shape to a specific part or to the main symbol."""
        if part_name is None:
            self.shapes.append(shape)
        else:
            part = self._get_or_create_part(part_name)
            part.add_shape(shape)

    def set_bbox(self, x: int, width: int, height: int, y: int, part_name: str = None):
        """Set the bounding box for a specific part or the main symbol."""
        if part_name is None:
            self.bbox = (x, width, height, y)
        else:
            part = self._get_or_create_part(part_name)
            part.set_bbox(x, width, height, y)

    def move(self, dx: float, dy: float, part_name: str = None):
        """Move all elements by the given offset.
        
        Args:
            dx: X-axis offset
            dy: Y-axis offset
            part_name: If specified, move only that part; otherwise move all parts
        """
        if part_name is None:
            # Move all parts
            if len(self.parts) > 0:
                for part in self.parts.values():
                    part.move(dx, dy)
            else:
                # Backward compatibility: move main symbol
                for pin_group in self.pin_groups:
                    pin_group.move(dx, dy)
                for shape in self.shapes:
                    shape.move(dx, dy)
                self.bbox = (self.bbox[0] + dx, self.bbox[1] + dy, self.bbox[2] + dx, self.bbox[3] + dy)
        else:
            # Move specific part
            part = self._get_or_create_part(part_name)
            part.move(dx, dy)

    def align_to_grid(self, grid_size: float = 1.0, part_name: str = None):
        """Align symbol elements to a grid.
        
        Args:
            grid_size: The grid size to align to
            part_name: If specified, align only that part; otherwise align all parts
        """
        def round_to_grid(value: float, grid: float) -> float:
            """Round a value to the nearest grid point."""
            return round(value / grid) * grid
        
        if part_name is None:
            # Align all parts
            if len(self.parts) > 0:
                for part in self.parts.values():
                    # Get current min coordinates
                    if part.pin_groups and part.shapes:
                        all_coords = []
                        for pg in part.pin_groups:
                            all_coords.append(pg.pin.pos.start_x)
                            all_coords.append(pg.pin.pos.start_y)
                        for shape in part.shapes:
                            if hasattr(shape, 'x1'):  # Line
                                all_coords.extend([shape.x1, shape.y1])
                            elif hasattr(shape, 'x'):  # Circle
                                all_coords.extend([shape.x, shape.y])
                            elif hasattr(shape, 'start_x'):  # Arc
                                all_coords.extend([shape.start_x, shape.start_y])
                        
                        if all_coords:
                            min_x = min(all_coords[i] for i in range(0, len(all_coords), 2) if i < len(all_coords))
                            min_y = min(all_coords[i] for i in range(1, len(all_coords), 2) if i < len(all_coords))
                            
                            aligned_x = round_to_grid(min_x, grid_size)
                            aligned_y = round_to_grid(min_y, grid_size)
                            dx = aligned_x - min_x
                            dy = aligned_y - min_y
                            
                            part.move(dx, dy)
            else:
                # Backward compatibility: align main symbol
                if self.pin_groups or self.shapes:
                    all_coords = []
                    for pg in self.pin_groups:
                        all_coords.append(pg.pin.pos.start_x)
                        all_coords.append(pg.pin.pos.start_y)
                    for shape in self.shapes:
                        if hasattr(shape, 'x1'):  # Line
                            all_coords.extend([shape.x1, shape.y1])
                        elif hasattr(shape, 'x'):  # Circle
                            all_coords.extend([shape.x, shape.y])
                        elif hasattr(shape, 'start_x'):  # Arc
                            all_coords.extend([shape.start_x, shape.start_y])
                    
                    if all_coords:
                        min_x = min(all_coords[i] for i in range(0, len(all_coords), 2) if i < len(all_coords))
                        min_y = min(all_coords[i] for i in range(1, len(all_coords), 2) if i < len(all_coords))
                        
                        aligned_x = round_to_grid(min_x, grid_size)
                        aligned_y = round_to_grid(min_y, grid_size)
                        dx = aligned_x - min_x
                        dy = aligned_y - min_y
                        
                        self.move(dx, dy)
        else:
            # Align specific part
            part = self.parts.get(part_name)
            if part:
                if part.pin_groups and part.shapes:
                    all_coords = []
                    for pg in part.pin_groups:
                        all_coords.append(pg.pin.pos.start_x)
                        all_coords.append(pg.pin.pos.start_y)
                    for shape in part.shapes:
                        if hasattr(shape, 'x1'):  # Line
                            all_coords.extend([shape.x1, shape.y1])
                        elif hasattr(shape, 'x'):  # Circle
                            all_coords.extend([shape.x, shape.y])
                        elif hasattr(shape, 'start_x'):  # Arc
                            all_coords.extend([shape.start_x, shape.start_y])
                    
                    if all_coords:
                        min_x = min(all_coords[i] for i in range(0, len(all_coords), 2) if i < len(all_coords))
                        min_y = min(all_coords[i] for i in range(1, len(all_coords), 2) if i < len(all_coords))
                        
                        aligned_x = round_to_grid(min_x, grid_size)
                        aligned_y = round_to_grid(min_y, grid_size)
                        dx = aligned_x - min_x
                        dy = aligned_y - min_y
                        
                        part.move(dx, dy)

    def __str__(self):
        # self._calc_bbox()

        sym_string = "V 50\n"
        sym_string += f"K {random.randint(1000000000, 9999999999)} {self.name}\n"
        sym_string += "Y 1\n"
        
        # If there are multiple parts, output each part separately
        if len(self.parts) > 0:
            for part_name in sorted(self.parts.keys()):
                part = self.parts[part_name]
                sym_string += f"K {random.randint(1000000000, 9999999999)} {part_name}\n"
                sym_string += str(part)
                sym_string += f"U 140 40 8 0 5 3 REFDES={self.refdes.upper()}\n"
                sym_string += "U 140 30 8 0 5 0 TYPE=Type?\n"
                sym_string += f"U 140 30 8 0 5 0 VALUE={self.value}\n"
        else:
            # Backward compatibility: single part
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



