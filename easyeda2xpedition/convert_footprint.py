from easyeda import easyeda_importer
from easyeda import easyeda_api

from xpedition.pads import *
from xpedition.padstacks import *
from xpedition.holes import *
from xpedition.shapes import *
from xpedition.cell import PIN as XpeditionPin

def ee_unit_to_th(value: float) -> float:
    return value * 10

class FootprintConverter(object):
    def __init__(self, easyeda_cp_cad_data: dict, output_folder: str = None):
        self._easyeda_cp_cad_data = easyeda_cp_cad_data
        self._target_folder = output_folder

        self._easyeda_footprint = easyeda_importer.EasyedaFootprintImporter(
            easyeda_cp_cad_data=self._easyeda_cp_cad_data
        ).get_footprint()

        self._pads = {}
        self._padstacks = {}
        self._part = None
        self._cell = {
            "PIN": [],
            "TOP": [],
            "BOTTOM": [],
            "SILKSCREEN_OUTLINE": [],
            "SOLDER_MASK": [],
            "SOLDER_PASTE": [],
            "ASSEMBLY_OUTLINE": [],
            "PLACEMENT_OUTLINE": [],
            "TEXT": []
        }

    def _get_easyeda_layer_name(self,layer_id):
        # 从footprint.info.layers查找layer_id对应的layer_name
        if hasattr(self._easyeda_footprint.info, "layers"):
            for layer in self._easyeda_footprint.info.layers:
                if hasattr(layer, "layer_id") and int(layer.layer_id) == int(layer_id):
                    return getattr(layer, "layer_name", str(layer_id))
                if isinstance(layer, dict) and int(layer.get("layer_id", -1)) == int(layer_id):
                    return layer.get("layer_name", str(layer_id))
        return str(layer_id)
    
    def _map_easyeda_layer_to_xpedition(layer_name: str) -> str:
        layer_map = {
            "TopLayer": "TOP",
            "BottomLayer": "BOTTOM",
            "TopSilkLayer": "SILKSCREEN_OUTLINE",
            "BottomSilkLayer": "SILKSCREEN_OUTLINE",
            "TopPasterLayer": "SOLDER_PASTE",
            "BottomPasterLayer": "SOLDER_PASTE",
            "TopSolderLayer": "SOLDER_MASK",
            "BottomSolderLayer": "SOLDER_MASK",
            "Multi-Layer": "MULTI_LAYER",
            "TopAssembly": "ASSEMBLY_OUTLINE",
            "BottomAssembly": "ASSEMBLY_OUTLINE",
            "ComponentShapeLayer": "ASSEMBLY_OUTLINE",
        }
        return layer_map.get(layer_name, f"UNKNOWN_LAYER_{layer_name}")

    def convert(self):
        self._convert_easyeda_padstack_to_xpedition()
        self._save_padstacks_to_file(f"{self._target_folder}/_Pads.hkp")

        print(f"Converted {len(self._pads)} pads and {len(self._padstacks)} padstacks from EasyEDA to Xpedition format.")

    def _convert_easyeda_padstack_to_xpedition(self):
        """Convert EasyEDA padstacks to Xpedition padstacks."""
        for pad in self._easyeda_footprint.pads:
            width = ee_unit_to_th(pad.width)
            large_width = width + 8 # 8 mils larger for the solder mask/paste
            height = ee_unit_to_th(pad.height)
            large_height = height + 8
            pad_name = f"{pad.shape}_{width}x{height}"
            pad_type = "PIN_THROUGH" if pad.hole_radius > 0 or pad.hole_point else "PIN_SMD"
            normalized_points = []
            

            xpedition_pad = None
            if pad.shape.upper() == "RECT":
                xpedition_pad = RectanglePad(name=pad_name, width=width, height=height)
                large_xpedition_pad = RectanglePad(name=f"{pad_name}L", width=large_width, height=large_height)
            elif pad.shape.upper() == "ROUND":
                xpedition_pad = RoundPad(name=pad_name, diameter=width)
                large_xpedition_pad = RoundPad(name=f"{pad_name}L", diameter=large_width)
            elif pad.shape.upper() == "OVAL":
                xpedition_pad = OblongPad(name=pad_name, width=width, height=height)
                large_xpedition_pad = OblongPad(name=f"{pad_name}L", width=large_width, height=large_height)
            else:
                raise ValueError(f"Unsupported pad shape: {pad.shape}")
            
            if pad_name not in self._pads:
                self._pads[pad_name] = xpedition_pad
                self._pads[f"{pad_name}L"] = large_xpedition_pad

            hole_points = getattr(pad, "hole_point", "")
            if pad.hole_radius > 0 or hole_points:
                normalized_hole_points = []
                xpedition_hole = None

                if hole_points:
                    hx = getattr(pad, "center_x", 0)
                    hy = getattr(pad, "center_y", 0)
                    pts = [float(v) for v in hole_points.replace(",", " ").split()]
                    for i in range(0, len(pts), 2):
                        px = pts[i] - hx
                        py = pts[i + 1] - hy
                        normalized_hole_points.append((ee_unit_to_th(px), ee_unit_to_th(py)))

                    hole_width = max(normalized_hole_points, key=lambda p: p[0])[0] - min(normalized_hole_points, key=lambda p: p[0])[0]
                    hole_height = max(normalized_hole_points, key=lambda p: p[1])[1] - min(normalized_hole_points, key=lambda p: p[1])[1]
                    hole_length = round(max(hole_width, hole_height), 4)
                    hole_radius = round(ee_unit_to_th(pad.hole_radius), 4)

                    xpedition_hole = SlotHole(
                        name=f"HOLE_{hole_radius * 2}x{hole_length}",
                        width=hole_radius * 2,
                        height=hole_length,
                        plated=pad.hole_plated if hasattr(pad, "hole_plated") else True
                    )
                else:
                    xpedition_hole = RoundHole(
                        name=f"HOLE_{round(ee_unit_to_th(pad.hole_radius * 2), 4)}",
                        diameter=ee_unit_to_th(pad.hole_radius * 2),
                        plated=pad.hole_plated if hasattr(pad, "hole_plated") else True
                    )

                padstack_name = f"{pad_name}_TH"
                xpedition_padstack = PinThroughPadStack(name=padstack_name)
                xpedition_padstack.set_pads(
                    top_pad=xpedition_pad,
                    bottom_pad=xpedition_pad,
                    internal_pad=xpedition_pad,
                    top_solderpaste_pad=large_xpedition_pad,
                    bottom_solderpaste_pad=large_xpedition_pad,
                    top_soldermask_pad=large_xpedition_pad,
                    bottom_soldermask_pad=large_xpedition_pad,
                    hole=xpedition_hole
                )

                if xpedition_hole.name not in self._pads:
                    self._pads[xpedition_hole.name] = xpedition_hole
            else:
                padstack_name = f"{pad_name}_SMD"
                xpedition_padstack = PinSMDPadStack(name=padstack_name)
                xpedition_padstack.set_pads(
                    top_pad=xpedition_pad,
                    bottom_pad=xpedition_pad,
                    top_solderpaste_pad=large_xpedition_pad,
                    bottom_solderpaste_pad=large_xpedition_pad,
                    top_soldermask_pad=large_xpedition_pad,
                    bottom_soldermask_pad=large_xpedition_pad
                )

            if padstack_name not in self._padstacks:
                self._padstacks[padstack_name] = xpedition_padstack

            pin = XpeditionPin(pad.number, ee_unit_to_th(pad.center_x), ee_unit_to_th(pad.center_y), xpedition_padstack, pad.rotation)
            self._cell["PIN"].append(pin)

        # Convert EasyEDA holes to Xpedition, the holes are treated as pads with a specific padstack
        for hole in self._easyeda_footprint.holes:
            hole_name = f"HOLE_{round(ee_unit_to_th(hole.radius * 2), 4)}"
            if hole_name not in self._pads:
                xpedition_hole = RoundHole(
                    name=hole_name,
                    diameter=ee_unit_to_th(hole.radius * 2),
                    plated=False
                )
                self._pads[hole_name] = xpedition_hole
            else:
                xpedition_hole = self._pads[hole_name]

            # Create a new round pad for drilled holes
            pad_name = f"ROUND_{round(ee_unit_to_th(hole.radius * 2), 4)}"
            xpedition_pad = RoundPad(name=pad_name, diameter=ee_unit_to_th(hole.radius * 2))
            if pad_name not in self._pads:
                self._pads[pad_name] = xpedition_pad
        
            padstack_name = f"{hole_name}_TH"
            if padstack_name not in self._padstacks:
                xpedition_padstack = PinThroughPadStack(name=padstack_name)
                xpedition_padstack.set_pads(
                    top_pad=xpedition_pad,
                    bottom_pad=xpedition_pad,
                    internal_pad=xpedition_pad,
                    hole=xpedition_hole
                )
                self._padstacks[padstack_name] = xpedition_padstack
            else:
                xpedition_padstack = self._padstacks[padstack_name]

            pin_number = len(self._cell["PIN"]) + 1
            pin = XpeditionPin(pin_number, ee_unit_to_th(hole.center_x), ee_unit_to_th(hole.center_y), xpedition_padstack, 0)

    def _save_padstacks_to_file(self, filename: str):
        with open(filename, 'w') as f:
            f.write(".FILETYPE PADSTACK_LIBRARY\n"
                    ".VERSION \"VB99.0\"\n"
                    ".SCHEMA_VERSION 13\n"
                    ".CREATOR \"EasyEDA to Xpedition Converter\"\n"
                    "\n"
                    ".UNITS TH\n"
                    "\n")

            for pad in self._pads.values():
                f.write(str(pad) + "\n")

            for padstack in self._padstacks.values():
                f.write(str(padstack) + "\n")

    def _convert_easyeda_shape_to_xpedition(self):
        for rect in getattr(self._easyeda_footprint, "rectangles", []):
            layer_name = self._get_easyeda_layer_name(getattr(rect, "layer_id", 0))
            xpedition_layer_name = self._map_easyeda_layer_to_xpedition(layer_name)

            if "UNKNOWN_LAYER" in xpedition_layer_name:
                continue

            # ToDo
            

if __name__ == "__main__":
    tgt_folder = "../output"  # Specify your target folder here
    easyead_cad_data = easyeda_api.EasyedaApi().get_cad_data_of_component(
        lcsc_id="C165948"
    )  # Replace with a valid LCSC ID

    converter = FootprintConverter(easyead_cad_data, output_folder=tgt_folder)
    converter.convert()

    print(f"Converted footprint saved to {tgt_folder}/_Pads.hkp")