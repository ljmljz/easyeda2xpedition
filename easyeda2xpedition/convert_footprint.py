from easyeda2kicad.easyeda import easyeda_importer
from easyeda2kicad.easyeda import easyeda_api
from easyeda2kicad.easyeda.parameters_easyeda import EeFootprintPad
import os

def mm_to_th(mm):
    return mm / 0.0254

def th_to_mm(th):
    return th * 0.0254


class FootprintConverter(object):
    def __init__(self, easyeda_cp_cad_data: dict, output_folder: str = None):
        self._easyeda_cp_cad_data = easyeda_cp_cad_data
        self._target_folder = output_folder

        self._easyeda_footprint = easyeda_importer.EasyedaFootprintImporter(
            easyeda_cp_cad_data=self._easyeda_cp_cad_data
        ).get_footprint()

        self._xpedition_footprints = []
        self._xpedition_padstacks = []
        self._xpedition_pads = []
        self._xpedition_3d_model = None

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

    def _convert_cell(self):
        """Convert EasyEDA footprint to Xpedition cell."""
        with open(os.path.join(self._target_folder, "_Cells.hkp"), "w") as f:
            f.write(".FILETYPE CELL_LIBRARY\n")
            f.write(".VERSION \"1.01.01\"\n")
            f.write(".CREATOR \"EasyEDA to Xpedition Converter\"\n")
            f.write("\n")

            f.write(".UNITS TH\n")
            f.write("\n")

            f.write(f".PACKAGE_CELL {self._easyeda_footprint.info.name.upper()}\n")
            f.write("..NUMBER_LAYERS 4\n")
            f.write("..PACKAGE_GROUP IC_Other\n")

            # Place the padstack here
            index = 0
            for pad in self._easyeda_footprint.pads:
                indent = '..'
                f.write(f"{indent}PIN {pad.number}\n")

                indent = '...'
                f.write(f"{indent}XY ({int(mm_to_th(pad.x))}, {int(mm_to_th(pad.y))})\n")
                f.write(f"{indent}PADSTACK {self._format_value(self._xpedition_padstacks[index])}\n")
                f.write(f"{indent}ROTATION {int(pad.rotation)}\n")
                f.write(f"{indent}PIN_OPTIONS NONE\n")

                index += 1

            for solid_region in self._easyeda_footprint.solid_regions:
                indent = '..'
                

    def _convert_padstack(self):
        """Convert EasyEDA footprint to Xpedition padstack."""
        with open(os.path.join(self._target_folder, "_Pads.hkp"), "w") as f:
            f.write(".FILETYPE PADSTACK_LIBRARY\n")
            f.write(".VERSION \"VB99.0\"\n")
            f.write(".SCHEMA_VERSION 13\n")
            f.write(".CREATOR \"EasyEDA to Xpedition Converter\"\n")
            f.write("\n")

            f.write(".UNITS TH\n")
            f.write("\n")

            for pad in self._easyeda_footprint.pads:
                width = int(mm_to_th(pad.width))
                height = int(mm_to_th(pad.height))

                shape = self._shape_map.get(pad.shape.upper(), pad.shape.upper())
                name = f"{shape} {width}x{height}"

                if name not in self._xpedition_pads:
                    self._convert_pad(pad, f)

                # no matter what, we need to add the pad name to the pads list
                self._xpedition_pads.append(name)

            index = 0
            for pad in self._easyeda_footprint.pads:
                padstack_type = "PIN_THROUGH" if pad.hole_radius > 0 else "PIN_SMD"
                padstack_shape = self._shape_map.get(pad.shape.upper(), pad.shape.upper())
                padstack_name = "R" if padstack_shape == "RECTANGLE" else "E"
                padstack_name += f"X{int(mm_to_th(pad.width))}Y{int(mm_to_th(pad.height))}"
                
                if padstack_type == "PIN_THROUGH":
                    padstack_name += f"D{int(mm_to_th(pad.hole_radius * 2))}P0"
                else:
                    padstack_name += "D0T0"

                if padstack_name not in self._xpedition_padstacks:
                    f.write(f".PADSTACK {padstack_name}\n")
                    f.write(f"..PADSTACK_TYPE {padstack_type}\n")
                    
                    f.write("..TECHNOLOGY \"(Default)\"\n")
                    f.write("...TECHNOLOGY_OPTIONS NONE\n")

                    f.write(f"...TOP_PAD {self._xpedition_pads[index]}\n")
                    f.write(f"...TOP_SOLDERPASTE_PAD {self._xpedition_pads[index]}\n")
                    f.write(f"...TOP_SOLDERMASK_PAD {self._xpedition_pads[index]}\n")
                    f.write(f"...TOP_PAD {self._xpedition_pads[index]}\n")
                    f.write(f"...BOTTOM_PAD {self._xpedition_pads[index]}\n")
                    f.write(f"...BOTTOM_SOLDERPASTE_PAD {self._xpedition_pads[index]}\n") 
                    f.write(f"...BOTTOM_SOLDERMASK_PAD {self._xpedition_pads[index]}\n")

                    if padstack_type == "PIN_THROUGH":
                        f.write(f"...INTERNAL_PAD {self._xpedition_pads[index]}\n")
                        f.write(f"...HOLE_NAME {int(mm_to_th(pad.hole_radius * 2))}\n")

                    f.write("....OFFSET (0, 0)\n")
                    f.write("\n")

                index += 1

                # no matter what, we need to add the padstack name to the padstacks list
                self._xpedition_padstacks.append(padstack_name)

    def _convert_pad(self, easyeda_pad: EeFootprintPad, fp: object):
        """Convert EasyEDA pad to Xpedition pad."""
        width = int(mm_to_th(easyeda_pad.width))
        height = int(mm_to_th(easyeda_pad.height))

        shape = self._shape_map.get(easyeda_pad.shape.upper(), easyeda_pad.shape.upper())
        name = f"{shape} {width}x{height}"

        indent = '.'
        fp.write(f"{indent}PAD {name}\n")

        indent = '..'
        fp.write(f"{indent}{shape.upper()}\n")

        indent = '...'
        fp.write(f"{indent}WIDTH {width}\n")
        fp.write(f"{indent}HEIGHT {height}\n")

        indent = '..'
        fp.write(f"{indent}PAD_OPTIONS  USER_GENERATED_NAME\n")
        fp.write(f"{indent}OFFSET (0, 0)\n")
        fp.write("\n")

if __name__ == "__main__":
    tgt_folder = "output"  # Specify your target folder here
    easyead_cad_data = easyeda_api.EasyedaApi().get_cad_data_of_component(
        lcsc_id="C165948"
    )  # Replace with a valid LCSC ID
    converter = FootprintConverter(easyead_cad_data, output_folder=tgt_folder)
    converter._convert_padstack()

    print(f"Converted footprint saved to {tgt_folder}/_Pads.hkp")