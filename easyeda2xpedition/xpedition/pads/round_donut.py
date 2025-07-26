from xpedition.pads.base import BasePad

class RoundDonutPad(BasePad):
    def __init__(self, name: str, outer_diameter: float, inner_diameter: float, offset: tuple = (0, 0)):
        """Initialize a round donut pad with a name, outer diameter, inner diameter, and optional offset."""
        super().__init__(name, offset)
        self.shape = "ROUND_DONUT"
        self.outer_diameter = outer_diameter
        self.inner_diameter = inner_diameter

    def __str__(self):
        pad_string = super().__str__()

        pad_string += f"...OUTER_DIAMETER {int(self.outer_diameter)}\n"
        pad_string += f"...INNER_DIAMETER {int(self.inner_diameter)}\n"
        
        return pad_string