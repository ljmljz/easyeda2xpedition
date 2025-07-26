from xpedition.pads.base import BasePad

class SquareDonutPad(BasePad):
    def __init__(self, name: str, width: int, height: int, offset: tuple = (0, 0)):
        """Initialize a square donut pad with a name, width, height, and optional offset."""
        super().__init__(name, offset)
        self.shape = "SQUARE_DONUT"
        self.width = width
        self.height = height

    def __str__(self):
        pad_string = super().__str__()

        pad_string += f"...WIDTH {self.width}\n"
        pad_string += f"...HEIGHT {self.height}\n"
        
        return pad_string