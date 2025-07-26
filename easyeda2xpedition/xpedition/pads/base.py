

class BasePad(object):
    def __init__(self, name: str, offset: tuple = (0, 0)):
        """Initialize a base pad with a name and optional offset."""
        self.name = name
        self.shape = ""
        self.pad_options = "USER_GENERATED_NAME"
        self.offset = offset

    def set_offset(self, x: int, y: int):
        """Set the offset for the pad."""
        self.offset = (x, y)

    def __str__(self):
        pad_string = f".PAD \"{self.name}\"\n"
        pad_string += f"..PAD_OPTIONS {self.pad_options}\n"
        pad_string += f"..OFFSET ({self.offset[0]}, {self.offset[1]})\n"
        pad_string += f"..{self.shape.upper()}\n"
        
        return pad_string
    
    def to_string(self):
        """Return the string representation of the pad."""
        return self.__str__()