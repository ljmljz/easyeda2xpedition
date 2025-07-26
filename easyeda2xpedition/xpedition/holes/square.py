from xpedition.holes.base import BaseHole

class SquareHole(BaseHole):
    def __init__(self, name: str, width: int, plated: bool = False, drill_type: str ="DRILLED", tol: tuple = (0, 0)):
        super().__init__(name, plated, drill_type, tol)
        self.shape = "SQUARE"
        self.width = width

    def __str__(self):
        hole_string = super().__str__()

        hole_string += f"...WIDTH {self.width}\n"
        
        return hole_string