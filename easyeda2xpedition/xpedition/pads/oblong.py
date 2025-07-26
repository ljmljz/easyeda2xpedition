from xpedition.pads.base import BasePad

class OblongPad(BasePad):
    def __init__(self, name: str, width: int, height: int, offset: tuple = (0, 0)):
        super().__init__(name, offset)
        self.shape = "OBLONG"
        self.width = width
        self.height = height

    def __str__(self):
        pad_string = super().__str__()

        pad_string += f"...WIDTH {self.width}\n"
        pad_string += f"...HEIGHT {self.height}\n"
        
        return pad_string