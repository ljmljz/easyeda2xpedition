class BasePadStack(object):
    """Base class for pad stacks in Xpedition."""
    
    def __init__(self, name: str):
        """Initialize a pad stack with a name and optional offset."""
        self.name = name
        self.padstack_type = ""
        self.technology = "Default"
        self.pads = PadStackPads()

    def set_pads(self, top_pad=None, bottom_pad=None, internal_pad=None,
                 top_solderpaste_pad=None, bottom_solderpaste_pad=None, 
                 top_soldermask_pad=None, bottom_soldermask_pad=None, hole=None, offset=(0, 0)):
        """Set the pads for the pad stack."""
        self.pads.top_pad = top_pad
        self.pads.bottom_pad = bottom_pad
        self.pads.internal_pad = internal_pad
        self.pads.top_solderpaste_pad = top_solderpaste_pad
        self.pads.bottom_solderpaste_pad = bottom_solderpaste_pad
        self.pads.top_soldermask_pad = top_soldermask_pad
        self.pads.bottom_soldermask_pad = bottom_soldermask_pad
        self.pads.hole = hole
        self.pads.hole_offset = offset

    def __str__(self):
        """Return a string representation of the pad stack."""
        padstack_string = f".PADSTACK \"{self.name}\"\n"
        padstack_string += f"..PADSTACK_TYPE {self.padstack_type.upper()}\n"
        padstack_string += f"..TECHNOLOGY \"({self.technology})\"\n"
        padstack_string += "...TECHNOLOGY_OPTIONS NONE\n"

        if self.pads.top_pad is not None:
            padstack_string += f"...TOP_PAD \"{self.pads.top_pad.name}\"\n"
        if self.pads.top_solderpaste_pad is not None:
            padstack_string += f"...TOP_SOLDERPASTE_PAD \"{self.pads.top_solderpaste_pad.name}\"\n"
        if self.pads.top_soldermask_pad is not None:
            padstack_string += f"...TOP_SOLDERMASK_PAD \"{self.pads.top_soldermask_pad.name}\"\n"
        if self.pads.bottom_pad is not None:
            padstack_string += f"...BOTTOM_PAD \"{self.pads.bottom_pad.name}\"\n"
        if self.pads.bottom_solderpaste_pad is not None:
            padstack_string += f"...BOTTOM_SOLDERPASTE_PAD \"{self.pads.bottom_solderpaste_pad.name}\"\n"
        if self.pads.bottom_soldermask_pad is not None:
            padstack_string += f"...BOTTOM_SOLDERMASK_PAD \"{self.pads.bottom_soldermask_pad.name}\"\n"

        return padstack_string
    
    def to_string(self):
        """Return the string representation of the pad stack."""
        return self.__str__()


class PadStackPads(object):
    def __init__(self):
        self.top_pad = None
        self.bottom_pad = None
        self.internal_pad = None
        self.top_solderpaste_pad = None
        self.bottom_solderpaste_pad = None
        self.top_soldermask_pad = None
        self.bottom_soldermask_pad = None
        self.hole = None
        self.hole_offset = (0, 0)  # Default offset for the hole