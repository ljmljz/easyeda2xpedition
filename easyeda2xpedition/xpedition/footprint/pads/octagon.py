from xpedition.pads.base import BasePad

class OctagonPad(BasePad):
    def __init__(self, name: str, width: int, offset: tuple = (0, 0)):
        """Initialize an octagon pad with a name, width, height, and optional offset."""
        super().__init__(name, offset)
        self.shape = "OCTAGON"
        self.width = width

    def __str__(self):
        pad_string = super().__str__()

        pad_string += f"...WIDTH {self.width}\n"
        
        return pad_string