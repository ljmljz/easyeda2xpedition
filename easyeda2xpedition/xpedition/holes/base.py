
class BaseHole(object):
    """Base class for holes in pads."""
    
    def __init__(self, name: str, plated: bool = False, drill_type: str ="DRILLED", tol: tuple = (0, 0)):
        """Initialize a hole with a name and optional offset."""
        self.name = name
        self.tol = tol
        self.shape = ""
        self.plated = plated  # Default to unplated
        self.drill_type = drill_type  # Default to drilled

    def set_tol(self, pos: int, neg: int):
        """Set the offset for the pad."""
        self.tol = (pos, neg)
        
    def __str__(self):
        """Return a string representation of the hole."""
        hole_string = f".Hole \"{self.name}\"\n"
        hole_string += f"..POSITIVE_TOLERANCE {self.tol[0]}\n"
        hole_string += f"..NEGATIVE_TOLERANCE {self.tol[1]}\n"

        plated = "PLATED" if self.plated else "NON_PLATED"
        hole_string += f"..HOLE_OPTIONS {plated} {self.drill_type} USER_GENERATED_NAME\n"
        hole_string += f"..{self.shape.upper()}\n"

        return hole_string
    
    def to_string(self):
        """Return the string representation of the hole."""
        return self.__str__()