from easyeda import easyeda_importer
from easyeda import easyeda_api
from xpedition.padstack import XpeditonPadStack
from xpedition.cell import XpeditonCell
import os

def ee_unit_to_th(value: float) -> float:
    return value * 10

class FootprintConverter(object):
    def __init__(self, easyeda_cp_cad_data: dict, output_folder: str = None):
        self._easyeda_cp_cad_data = easyeda_cp_cad_data
        self._target_folder = output_folder

        self._easyeda_footprint = easyeda_importer.EasyedaFootprintImporter(
            easyeda_cp_cad_data=self._easyeda_cp_cad_data
        ).get_footprint()

        self._xpedition_padstack_handler = XpeditonPadStack(self._easyeda_footprint)
        self._xpedition_cell_handler = XpeditonCell(self._easyeda_footprint)

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
        
    def convert(self):
        self._xpedition_padstack_handler.save_padstacks(os.path.join(self._target_folder, "_Pads.hkp"))

if __name__ == "__main__":
    tgt_folder = "output"  # Specify your target folder here
    easyead_cad_data = easyeda_api.EasyedaApi().get_cad_data_of_component(
        lcsc_id="C165948"
    )  # Replace with a valid LCSC ID

    converter = FootprintConverter(easyead_cad_data, output_folder=tgt_folder)
    converter.convert()

    print(f"Converted footprint saved to {tgt_folder}/_Pads.hkp")