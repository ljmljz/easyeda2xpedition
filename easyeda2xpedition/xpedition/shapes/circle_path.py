from xpedition.shapes.base import BaseShape

class CirclePath(BaseShape):
    """
    Represents a circular path with a center and radius.
    """
    def __init__(self, center_x, center_y, radius, width, level=3):
        super().__init__(level)
        self.shape = "CIRCLE_PATH"

        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.width = width

    def __str__(self):
        shape_string = f"{self.indent(self._level)}{self.shape}\n"
        shape_string += f"{self.indent(self._level + 1)}WIDTH {self.width}\n"
        shape_string += f"{self.indent(self._level + 1)}XY ({self.center_x}, {self.center_y})\n"
        shape_string += f"{self.indent(self._level + 1)}RADIUS {self.radius}\n"