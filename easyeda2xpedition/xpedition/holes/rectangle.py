from xpedition.holes.base import BaseHole

class RectangleHole(BaseHole):
    def __init__(self, name: str, width: int, height: int, plated: bool = False, drill_type: str = "DRILLED", tol: tuple = (0, 0)):
        super().__init__(name, plated, drill_type, tol)
        self.shape = "RECTANGLE"
        self.width = width
        self.height = height

    def __str__(self):
        hole_string = super().__str__()

        hole_string += f"...WIDTH {self.width}\n"
        hole_string += f"...HEIGHT {self.height}\n"
        
        return hole_string