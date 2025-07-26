from xpedition.pads.base import BasePad

class RoundFingerPad(BasePad):
    def __init__(self, name: str, width: int, height: int, offset: tuple = (0, 0)):
        """Initialize a round finger pad with a name, width, height, and optional offset."""
        super().__init__(name, offset)
        self.shape = "ROUND_FINGER"
        self.width = width
        self.height = height

    def __str__(self):
        pad_string = super().__str__()

        pad_string += f"...WIDTH {self.width}\n"
        pad_string += f"...HEIGHT {self.height}\n"
        
        return pad_string