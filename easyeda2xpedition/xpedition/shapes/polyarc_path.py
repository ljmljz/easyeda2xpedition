from xpedition.shapes.base import BaseShape

class PolyarcPath(BaseShape):
    """
    Represents a polyarc path with multiple points and arcs.
    """
    def __init__(self, points, width, level=3):
        super().__init__(level)
        self.shape = "POLYARC_PATH"
        self.points = points  # List of tuples (x, y)
        self.width = width

    def __str__(self):
        shape_string = f"{self.indent(self._level)}{self.shape}\n"
        shape_string += f"{self.indent(self._level + 1)}WIDTH {self.width}\n"
        
        if len(self.points) > 0:
            point = self.points[0]
            shape_string += f"{self.indent(self._level + 1)}XY ({point[0]}, {point[1]})\n"

        if len(self.points) > 1:
            for point in self.points[1:]:
                indent = "\t" * (self._level)
                shape_string += f"{indent}({point[0]}, {point[1]})\n"
        
        return shape_string