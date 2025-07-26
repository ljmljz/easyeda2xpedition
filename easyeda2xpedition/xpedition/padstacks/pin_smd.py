from xpedition.padstacks.base import BasePadStack

class PinSMDPadStack(BasePadStack):
    def __init__(self, name: str):
        """Initialize a pin SMD pad stack with a name, pad shape, width, height, and optional offset."""
        super().__init__(name)
        self.padstack_type = "PIN_SMD"

    def __str__(self):
        pad_string = super().__str__()
        
        return pad_string