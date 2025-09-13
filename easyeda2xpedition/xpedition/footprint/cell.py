from xpedition.padstacks.base import BasePadStack
from xpedition.shapes.base import BaseShape


class PIN(object):
    def __init__(self, number: int, x: float, y: float, padstack: BasePadStack, rotation: int =0):
        self.number = number
        self.x = x
        self.y = y
        self.padstack = padstack
        self.rotation = rotation

    def __str__(self):
        pin_string = f" ..PIN \"{self.number}\"\n"
        pin_string += f"  ...XY ({round(self.x, 4)}, {round(self.y, 4)})\n"
        pin_string += f"  ...PADSTACK \"{self.padstack.name}\"\n"
        pin_string += f"  ...ROTATION {int(self.rotation)}\n"
        pin_string += "  ...PIN_OPTIONS NONE\n"

        return pin_string


class AssemblyOutline(object):
    def __init__(self, shape: BaseShape):
        self.shape = shape
        self.shape.indent(3)

    def __str__(self):
        outline_string = " ..ASSEMBLY_OUTLINE\n"
        outline_string += str(self.shape)

        return outline_string


class SilkscreenOutline(object):
    def __init__(self, shape: BaseShape, side: str = "MNT_SIDE"):
        self.shape = shape
        self.side = side
        self.shape.indent(3)

    def __str__(self):
        silk_string = " ..SILKSCREEN_OUTLINE\n"
        silk_string += f"  ...SIDE {self.side}\n"
        silk_string += str(self.shape)

        return silk_string


class SolderMask(object):
    def __init__(self, shape: BaseShape, side: str = "MNT_SIDE"):
        self.shape = shape
        self.side = side
        self.shape.indent(3)

    def __str__(self):
        mask_string = " ..SOLDER_MASK\n"
        mask_string += f"  ...SIDE {self.side}\n"
        mask_string += str(self.shape)

        return mask_string


class SolderPaste(object):
    def __init__(self, shape: BaseShape, side: str = "MNT_SIDE"):
        self.shape = shape
        self.side = side
        self.shape.indent(3)

    def __str__(self):
        paste_string = " ..SOLDER_PASTE\n"
        paste_string += f"  ...SIDE {self.side}\n"
        paste_string += str(self.shape)

        return paste_string
    
class PlacementOutline(object):
    def __init__(self, shape: BaseShape, height: float = 0):
        self.shape = shape
        self.height = height
        self.shape.indent(3)

    def __str__(self):
        outline_string = " ..PLACEMENT_OUTLINE\n"
        outline_string += f"  ...HEIGHT {round(self.height, 4)}\n"
        outline_string += "  ...UNDERSIDE_SPACE 0\n"
        outline_string += "  ...SIDE MNT_SIDE\n"
        outline_string += "  ...DISPLAY_WIDTH 0\n"
        outline_string += str(self.shape)

        return outline_string

class Cell(object):
    def __init__(self, name):
        self.name = name
        self.number_layers = 2
        self.package_group = "General"
        self.mount_type = "SURFACE"     # Default mount type, value can be "SURFACE", "THROUGH" and "MIXED"

        self._pads = []
        self._padstacks = []
        self.pins = []
        self.assembly_outlines = []
        self.silkscreen_outlines = []
        self.solder_masks = []
        self.solder_pastes = []
        self.placement_outlines = []
        self.texts = []

        self._add_texts()

    def _add_texts(self):
        text = self._add_text_refdes()
        self.texts.append(text)

        text = self._add_text_type()
        self.texts.append(text)

        text = self._add_text_dev()
        self.texts.append(text)

        text = self._add_text_tol()
        self.texts.append(text)

        text = self._add_text_refdes2()
        self.texts.append(text)

    def _add_text_refdes(self):
        text = " ..TEXT \"RefDes\"\n"
        text += "  ...TEXT_TYPE REF_DES\n"
        text += "   ...DISPLAY_ATTR\n"
        text += "   ....XY (0, 0)\n"
        text += "   ....TEXT_LYR SILKSCREEN_MNT_SIDE\n"
        text += "   ....HORZ_JUST CENTER\n"
        text += "   ....VERT_JUST CENTER\n"
        text += "   ....HEIGHT 50\n"
        text += "   ....WIDTH 312\n"
        text += "   ....STROKE_WIDTH 3\n"
        text += "   ....ROTATION 0\n"
        text += "   ....FONT \"vf_std\"\n"
        text += "   ....TEXT \"TEXT_ASPECT_RATIO\" \"0.900\"\n"
        text += "   .....TEXT_TYPE PROPERTY_PAIR\n"
        text += "   ....TEXT_OPTIONS NONE\n"

        return text
    
    def _add_text_type(self):
        text = " ..TEXT \"Type\" \"DEV\"\n"
        text += "  ...TEXT_TYPE PROPERTY_PAIR\n"

        return text
    
    def _add_text_dev(self):
        text = " ..TEXT \"DEV\" \"DEV\"\n"
        text += "  ...TEXT_TYPE PROPERTY_PAIR\n"
        
        return text
    
    def _add_text_tol(self):
        text = " ..TEXT \"TOL\" \"TOL\"\n"
        text += "  ...TEXT_TYPE PROPERTY_PAIR\n"

        return text
    
    def _add_text_refdes2(self):
        text = " ..TEXT \"RefDes2\"\n"
        text += "  ...TEXT_TYPE REF_DES\n"
        text += "   ...DISPLAY_ATTR\n"
        text += "   ....XY (0, 0)\n"
        text += "   ....TEXT_LYR ASSEMBLY\n"
        text += "   ....HORZ_JUST CENTER\n"
        text += "   ....VERT_JUST CENTER\n"
        text += "   ....HEIGHT 50\n"
        text += "   ....WIDTH 364\n"
        text += "   ....STROKE_WIDTH 3\n"
        text += "   ....ROTATION 0\n"
        text += "   ....FONT \"vf_std\"\n"
        text += "   ....TEXT \"TEXT_ASPECT_RATIO\" \"0.900\"\n"
        text += "   .....TEXT_TYPE PROPERTY_PAIR\n"
        text += "   ....TEXT_OPTIONS NONE\n"

        return text
    
    def add_pin(self, pin: PIN):
        """Add a pin to the cell."""
        self.pins.append(pin)

    def add_assembly_outline(self, outline: AssemblyOutline):
        """Add an assembly outline to the cell."""
        self.assembly_outlines.append(outline)

    def add_silkscreen_outline(self, outline: SilkscreenOutline):
        """Add a silkscreen outline to the cell."""
        self.silkscreen_outlines.append(outline)

    def add_solder_mask(self, mask: SolderMask):
        """Add a solder mask to the cell."""
        self.solder_masks.append(mask)

    def add_solder_paste(self, paste: SolderPaste):
        """Add a solder paste to the cell."""
        self.solder_pastes.append(paste)

    def add_placement_outline(self, outline: PlacementOutline):
        """Add a placement outline to the cell."""
        self.placement_outlines.append(outline)

    def get_pin_count(self):
        """Get the count of pins in the cell."""
        return len(self.pins)
