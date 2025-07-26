from xpedition.holes.base import BaseHole

class RoundHole(BaseHole):
    def __init__(self, name: str, diameter: float, plated: bool = False, drill_type: str ="DRILLED", tol: tuple = (0, 0)):
        super().__init__(name, plated, drill_type, tol)
        self.shape = "ROUND"
        self.diameter = diameter

    def __str__(self):
        hole_string = super().__str__()

        hole_string += f"...DIAMETER {int(self.diameter)}\n"
        
        return hole_string