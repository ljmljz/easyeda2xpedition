from xpedition.pads.base import BasePad

class SquarePad(BasePad):
    def __init__(self, name: str, width: int, offset: tuple = (0, 0)):
        """Initialize a square pad with a name, width, height, and optional offset."""
        super().__init__(name, offset)
        self.shape = "SQUARE"
        self.width = width

    def __str__(self):
        pad_string = super().__str__()
        pad_string += f"...WIDTH {self.width}\n"
        
        return pad_string