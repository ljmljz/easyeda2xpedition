from xpedition.shapes.base import BaseShape

class PolylineShape(BaseShape):
    """
    Represents a polyline shape with multiple points.
    """
    def __init__(self, points, filled: bool = True, level=3):
        super().__init__(level)
        self.shape = "POLYLINE_SHAPE"
        self.points = points  # List of tuples (x, y)
        self.filled = filled

    def __str__(self):
        shape_string = f"{self.indent(self._level)}{self.shape}\n"
        
        if len(self.points) > 0:
            point = self.points[0]
            shape_string += f"{self.indent(self._level + 1)}XY ({point[0]}, {point[1]})\n"

        if len(self.points) > 1:
            for point in self.points[1:]:
                indent = "\t" * (self._level)
                shape_string += f"{indent}({point[0]}, {point[1]})\n"
        
        filled_str = "FILLED" if self.filled else "NOT_FILLED"
        shape_string += f"{self.indent(self._level + 1)}SHAPE_OPTIONS {filled_str}\n"
        return shape_string