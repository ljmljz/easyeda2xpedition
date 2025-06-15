from easyeda.parameters_easyeda import ee_footprint

def ee_unit_to_th(value: float) -> float:
    return value * 10


class XpeditonCell(object):
    def __init__(self, easyeda_footprint: ee_footprint):
        self._easyeda_footprint = easyeda_footprint
        self._xpedition_header = ""
        self._xpedition_cells = {}

        self._shape_map = {
            "CIRCLE": "ROUND",
            "RECT": "RECTANGLE",
            "OVAL": "OBLONG",
            "ELLIPSE": "OBLONG",
            "POLYGON": "POLYGON",
        }

    def _build_header(self):
        """Build the header for the Xpedition cell file."""
        self._xpedition_header = (
            ".FILETYPE CELL_LIBRARY\n"
            ".VERSION \"1.01.01\"\n"
            ".CREATOR \"EasyEDA to Xpedition Converter\"\n"
            "\n"
            ".UNITS TH\n"
            "\n"
        )

    def _convert_cell(self):
        cell_name = self._easyeda_footprint.info.name.upper()
        cell_string = f"{self._xpedition_header}.PACKAGE_CELL {cell_name}\n"
        cell_string += "..NUMBER_LAYERS 4\n"
        cell_string += "..PACKAGE_GROUP IC_Other\n"

        # Add PIN to the cell
        for pad in self._easyeda_footprint.pads:
            shape = self._shape_map.get(pad.shape.upper(), pad.shape.upper())

            padstack_type = "PIN_THROUGH" if pad.hole_radius > 0 else "PIN_SMD"
            padstack_name = "R" if shape == "RECTANGLE" else "E"
            padstack_name += f"X{int(ee_unit_to_th(pad.width))}Y{int(ee_unit_to_th(pad.height))}"

            if padstack_type == "PIN_THROUGH":
                padstack_name += f"D{int(ee_unit_to_th(pad.hole_radius * 2))}P0"
            else:
                padstack_name += "D0T0"

            cell_string += f"..PIN {pad.number}\n"
            
            indent = '...'
            cell_string += f"{indent}XY ({int(ee_unit_to_th(pad.center_x))}, {int(ee_unit_to_th(pad.center_y))})\n"
            cell_string += f"{indent}PADSTACK {padstack_name}\n"
            cell_string += f"{indent}ROTATION {int(pad.rotation)}\n"
            cell_string += f"{indent}PIN_OPTIONS NONE\n"

        # Holes should be added as PIN with a specific padstack
        for hole in self._easyeda_footprint.holes:
            pass

        # Add SOLDER_MASK to the cell
        # Todo

        # Add TEXT to the cell
        # Todo

        # Add SILKSCREEN_OUTLINE to the cell
        # Todo

        # Add ASSEMBLY_OUTLINE to the cell
        # Todo

        # Add MOUNT_TYPE to the cell: SURFACE/THROUGH/MIXED
        cell_string += "..MOUNT_TYPE MIXED"

        self._xpedition_cells[cell_name] = {
            'data_str': cell_string,
            'ee_source': {'type': 'FOOTPRINT', 'data': self._easyeda_footprint},
        }


    def get_cells(self) -> str:
        """Get the Xpedition cell string."""
        self._build_header()
        self._convert_cell()

        cells_string = self._xpedition_header
        for cell_name, cell_data in self._xpedition_cells.items():
            cells_string += cell_data['data_str'] + "\n"

        return cells_string

    def save_cells(self, file_path: str):
        """Save the Xpedition cell string to a file."""
        with open(file_path, "w") as f:
            f.write(self.get_cells())
