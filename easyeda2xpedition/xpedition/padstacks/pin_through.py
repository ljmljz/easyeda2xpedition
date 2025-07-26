from xpedition.padstacks.base import BasePadStack

class PinThroughPadStack(BasePadStack):
    def __init__(self, name: str):
        """Initialize a pin through pad stack with a name."""
        super().__init__(name)
        self.padstack_type = "PIN_THROUGH"

    def __str__(self):
        pad_string = super().__str__()
        if self.pads.internal_pad is not None:
            pad_string += f"...INTERNAL_PAD \"{self.pads.internal_pad.name}\"\n"
        pad_string += f"...HOLE_NAME \"{self.pads.hole.name}\"\n"
        pad_string += f"....OFFSET {self.pads.hole_offset}\n"
        
        return pad_string