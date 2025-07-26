from xpedition.pads.base import BasePad

class RoundPad(BasePad):
    def __init__(self, name: str, diameter: float, offset: tuple = (0, 0)):
        super().__init__(name, offset)
        self.shape = "ROUND"
        self.diameter = diameter

    def __str__(self):
        pad_string = super().__str__()

        pad_string += f"...DIAMETER {int(self.diameter)}\n"
        
        return pad_string