from xpedition.pads.base import BasePad

class ChamferedRectanglePad(BasePad):
    def __init__(self, name: str, width: int, height: int, chamfer: int, offset: tuple = (0, 0)):
        """Initialize a chamfered rectangle pad with a name, width, height, chamfer size, and optional offset."""
        super().__init__(name, offset)
        self.shape = "CHAMFERED_RECTANGLE"
        self.width = width
        self.height = height
        self.chamfer = chamfer

    def __str__(self):
        pad_string = super().__str__()

        pad_string += f"...WIDTH {self.width}\n"
        pad_string += f"...HEIGHT {self.height}\n"
        pad_string += f"...CHAMFER {self.chamfer}\n"
        
        return pad_string