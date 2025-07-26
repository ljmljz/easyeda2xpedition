from easyeda.parameters_easyeda import ee_footprint

def ee_unit_to_th(value: float) -> float:
    return value * 10

class XpeditonPadStack(object):
    def __init__(self, easyeda_footprint: ee_footprint):
        self._easyeda_footprint = easyeda_footprint
        self._xpeidtion_header = ""
        self._xpedition_pads = {}
        self._xpedition_padstacks = {}

        self._shape_map = {
            "CIRCLE": "ROUND",
            "RECT": "RECTANGLE",
            "OVAL": "OBLONG",
            "ELLIPSE": "OBLONG",
            "POLYGON": "POLYGON",
        }

    def _format_value(self, value):
        """Format a value for HKP output."""
        if isinstance(value, str):
            return f'"{value}"' if ' ' in value or value == '' else value
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

    def _build_header(self):
        """Build the header for the Xpedition padstack file."""
        self._xpeidtion_header = (
            ".FILETYPE PADSTACK_LIBRARY\n"
            ".VERSION \"VB99.0\"\n"
            ".SCHEMA_VERSION 13\n"
            ".CREATOR \"EasyEDA to Xpedition Converter\"\n"
            "\n"
            ".UNITS TH\n"
            "\n"
        )

    def _convert_padstack(self):
        """Convert EasyEDA footprint to Xpedition padstack."""
        for pad in self._easyeda_footprint.pads:
            width = int(ee_unit_to_th(pad.width))
            height = int(ee_unit_to_th(pad.height))

            shape = self._shape_map.get(pad.shape.upper(), pad.shape.upper())
            pad_name = f"{shape} {width}x{height}"

            padstack_type = "PIN_THROUGH" if pad.hole_radius > 0 else "PIN_SMD"
            padstack_name = "R" if shape == "RECTANGLE" else "E"
            padstack_name += f"X{int(ee_unit_to_th(pad.width))}Y{int(ee_unit_to_th(pad.height))}"
            
            if padstack_type == "PIN_THROUGH":
                padstack_name += f"D{int(ee_unit_to_th(pad.hole_radius * 2))}P0"
            else:
                padstack_name += "D0T0"

            if pad_name not in self._xpedition_pads:
                pad_string = self._convert_pad(pad_name, shape, width, height)

                self._xpedition_pads[pad_name] = {
                    'data_str': pad_string,
                    'ee_source': {'type': 'PAD', 'data': pad},
                }

            if padstack_name not in self._xpedition_padstacks:
                padstack_string = ""
                padstack_string += f".PADSTACK {padstack_name}\n"
                padstack_string += f"..PADSTACK_TYPE {padstack_type}\n"
                
                padstack_string += "..TECHNOLOGY \"(Default)\"\n"
                padstack_string += "...TECHNOLOGY_OPTIONS NONE\n"

                padstack_string += f"...TOP_PAD {pad_name}\n"
                padstack_string += f"...TOP_SOLDERPASTE_PAD {pad_name}\n"
                padstack_string += f"...TOP_SOLDERMASK_PAD {pad_name}\n"
                padstack_string += f"...BOTTOM_PAD {pad_name}\n"
                padstack_string += f"...BOTTOM_SOLDERPASTE_PAD {pad_name}\n"
                padstack_string += f"...BOTTOM_SOLDERMASK_PAD {pad_name}\n"

                if padstack_type == "PIN_THROUGH":
                    padstack_string += f"...INTERNAL_PAD {pad_name}\n"
                    padstack_string += f"...HOLE_NAME {int(ee_unit_to_th(pad.hole_radius * 2))}\n"

                padstack_string += "....OFFSET (0, 0)\n"
                padstack_string += "\n"

                self._xpedition_padstacks[padstack_name] = {
                    'data_str': padstack_string,
                    'ee_source': {'type': 'PAD', 'data': pad},
                }

        # Convert holes to padstacks. Holes sould be padstacks in Xpedition
        self._convert_hole()

    def _convert_pad(self, pad_name: str, shape: str, width: int, height: int) -> str:
        """Convert EasyEDA pad to Xpedition pad."""
        pad_string = ""
        pad_string += f".PAD {self._format_value(pad_name)}\n"

        pad_string += f"..{shape.upper()}\n"

        pad_string += f"...WIDTH {width}\n"
        pad_string += f"...HEIGHT {height}\n"

        pad_string += "..PAD_OPTIONS USER_GENERATED_NAME\n"
        pad_string += "..OFFSET (0, 0)\n"
        pad_string += "\n"

        return pad_string
  
    def _convert_hole(self):
        # Convert holes to padstacks
        for hole in self._easyeda_footprint.holes:
            hole_diameter = int(ee_unit_to_th(hole.radius * 2))
            pad_name = f"ROUND {hole_diameter}"
            pad_string = ""

            if pad_name not in self._xpedition_pads:
                indent = '.'
                pad_string += f"{indent}HOLE {pad_name}\n"

                indent = '..'
                pad_string += f"{indent}ROUND\n"

                indent = '...'
                pad_string += f"{indent}DIAMETER {int(ee_unit_to_th(hole.radius * 2))}\n"

                indent = '..'
                pad_string += f"{indent}POSITIVE_TOLERANCE 0\n"
                pad_string += f"{indent}NEGATIVE_TOLERANCE 0\n"

                # EasyEDA's holes are always non-plated. plated holes will be in pads.
                pad_string += f"{indent}HOLE_OPTIONS NON_PLATED DRILLED USER_GENERATED_NAME\n"
                pad_string += "\n"

                self._xpedition_pads[pad_name] = {
                    'data_str': pad_string,
                    'ee_source': {'type': 'HOLE', 'data': hole},
                }


            padstack_name = f"EX{hole_diameter}Y{hole_diameter}D{hole_diameter}P0"
            padstack_string = ""
            if padstack_name not in self._xpedition_padstacks:
                padstack_string += f".PADSTACK {padstack_name}\n"
                padstack_string += "..PADSTACK_TYPE PIN_THROUGH\n"
                padstack_string += "..TECHNOLOGY \"(Default)\"\n"
                padstack_string += "...TECHNOLOGY_OPTIONS NONE\n"
                padstack_string += f"...TOP_PAD {pad_name}\n"
                padstack_string += f"...TOP_SOLDERPASTE_PAD {pad_name}\n"
                padstack_string += f"...TOP_SOLDERMASK_PAD {pad_name}\n"
                padstack_string += f"...BOTTOM_PAD {pad_name}\n"
                padstack_string += f"...BOTTOM_SOLDERPASTE_PAD {pad_name}\n"
                padstack_string += f"...BOTTOM_SOLDERMASK_PAD {pad_name}\n"
                padstack_string += f"...INTERNAL_PAD {pad_name}\n"
                padstack_string += f"...HOLE_NAME {int(ee_unit_to_th(hole.radius * 2))}\n"
                padstack_string += "....OFFSET (0, 0)\n"
                padstack_string += "\n"

                self._xpedition_padstacks[padstack_name] = {
                    'data_str': padstack_string,
                    'ee_source': {'type': 'HOLE', 'data': hole},
                }

    def get_padstacks(self) -> str:
        self._build_header()
        self._convert_padstack()

        """Get the Xpedition padstacks as a string."""
        padstacks_str = self._xpeidtion_header

        for pad_name in self._xpedition_pads:
            padstacks_str += self._xpedition_pads[pad_name]['data_str']

        for padstack_name in self._xpedition_padstacks:
            padstacks_str += self._xpedition_padstacks[padstack_name]['data_str']
        return padstacks_str
    
    def save_padstacks(self, file_path: str):
        """Save the Xpedition padstacks to a file."""
        with open(file_path, 'w') as f:
            f.write(self.get_padstacks())
