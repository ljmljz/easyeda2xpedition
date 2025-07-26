from xpedition.pads.base import BasePad

class RadiusCornerRectanglePad(BasePad):
    def __init__(self, name: str, width: int, height: int, radius: int, offset: tuple = (0, 0)):
        """Initialize a radius corner rectangle pad with a name, width, height, radius, and optional offset."""
        super().__init__(name, offset)
        self.shape = "RADIUS_CORNER_RECTANGLE"
        self.width = width
        self.height = height
        self.radius = radius

    def __str__(self):
        pad_string = super().__str__()

        pad_string += f"...WIDTH {self.width}\n"
        pad_string += f"...HEIGHT {self.height}\n"
        pad_string += f"...RADIUS {self.radius}\n"
        
        return pad_string