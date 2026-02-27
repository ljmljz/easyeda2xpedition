from easyeda2xpedition.xpedition.footprint.pads.base import BasePad

class PolygonPad(BasePad):
    def __init__(self, name: str, points: list, offset: tuple = (0, 0)):
        """Initialize a polygon pad with a name, list of points, and optional offset."""
        super().__init__(name, offset)
        self.shape = "CUSTOM"
        self.points = points  # List of tuples (x, y)

    def __str__(self):
        pad_string = super().__str__()

        pad_string += "...POLYLINE_SHAPE\n"
        pad_string += "....XY " + " ".join(f"({point[0]}, {point[1]})" for point in self.points) + "\n"
        pad_string += "....SHAPE_OPTIONS FILLED\n"
        
        return pad_string