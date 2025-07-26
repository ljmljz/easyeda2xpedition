from xpedition.padstacks.base import BasePadStack

class PIN(object):
    def __init__(self, number: int, x: float, y: float, padstack: BasePadStack, rotation: int =0):
        self.number = number
        self.x = x
        self.y = y
        self.padstack = padstack
        self.rotation = rotation

    def __str__(self):
        pin_string = f"..PIN {self.number}\n"
        pin_string += f"...XY ({round(self.x, 4)}, {round(self.y, 4)})\n"
        pin_string += f"...PADSTACK {self.padstack.name}\n"
        pin_string += f"...ROTATION {self.rotation}\n"
        pin_string += "...PIN_OPTIONS NONE\n"

        return pin_string
    
class AssemblyOutline(object):
    def __init__(self, points: list, width: float = 6):
        self.points = points
        self.width = width

    def __str__(self):
        outline_string = "..ASSEMBLY_OUTLINE\n"
        outline_string += "...PLOYLINE_PATH\n"
        outline_string += f"....WIDTH {round(self.width, 4)}\n"
        for point in self.points:
            outline_string += f"...({round(point[0], 4)}, {round(point[1], 4)})\n"
        outline_string += "...\n"

        return outline_string

class Cell(object):
    def __init__(self, name):
        self.name = name
        self.number_layers = 4
        self.package_group = "IC_Other"

        self._padstacks = []
        self._pins = []
        self.holes = []
        self.shape = None
        self.rotation = 0