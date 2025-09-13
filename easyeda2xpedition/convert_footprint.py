from easyeda import easyeda_importer
from easyeda import easyeda_api

from xpedition.footprint.pads import *
from xpedition.footprint.padstacks import *
from xpedition.footprint.holes import *
from xpedition.footprint.shapes import *
from xpedition.footprint.cell import PIN as XpeditionPin
from xpedition.footprint.cell import Cell as XpeditionCell
from xpedition.footprint.cell import SilkscreenOutline, AssemblyOutline, SolderMask, SolderPaste, PlacementOutline
import re

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
        self._cell = XpeditionCell(name=self._easyeda_footprint.info.name)
        self._bbox = self._easyeda_footprint.bbox if hasattr(self._easyeda_footprint, "bbox") else None

    def _get_easyeda_layer_name(self,layer_id):
        # 从footprint.info.layers查找layer_id对应的layer_name
        if hasattr(self._easyeda_footprint.info, "layers"):
            for layer in self._easyeda_footprint.info.layers:
                if hasattr(layer, "layer_id") and int(layer.layer_id) == int(layer_id):
                    return getattr(layer, "layer_name", str(layer_id))
                if isinstance(layer, dict) and int(layer.get("layer_id", -1)) == int(layer_id):
                    return layer.get("layer_name", str(layer_id))
        return str(layer_id)
    
    def _map_easyeda_layer_to_xpedition(self, layer_name: str) -> str:
        layer_map = {
            "TopLayer": "TOP",
            "BottomLayer": "BOTTOM",
            "TopSilkLayer": "SILKSCREEN_OUTLINE",
            "BottomSilkLayer": "SILKSCREEN_OUTLINE",
            "TopPasteMaskLayer": "SOLDER_PASTE",
            "BottomPasteMaskLayer": "SOLDER_PASTE",
            "TopSolderMaskLayer": "SOLDER_MASK",
            "BottomSolderMaskLayer": "SOLDER_MASK",
            "Multi-Layer": "MULTI_LAYER",
            "TopAssembly": "ASSEMBLY_OUTLINE",
            "BottomAssembly": "ASSEMBLY_OUTLINE",
            "ComponentShapeLayer": "ASSEMBLY_OUTLINE",
        }
        return layer_map.get(layer_name, f"UNKNOWN_LAYER_{layer_name}")

    def convert(self):
        self._convert_easyeda_padstack_to_xpedition()
        self._convert_easyeda_shape_to_xpedition()

        print(f"Converted {len(self._pads)} pads and {len(self._padstacks)} padstacks from EasyEDA to Xpedition format.")

    def _convert_easyeda_padstack_to_xpedition(self):
        """Convert EasyEDA padstacks to Xpedition padstacks."""
        for pad in self._easyeda_footprint.pads:
            width = ee_unit_to_th(pad.width)
            large_width = width + 8 # 8 mils larger for the solder mask/paste
            height = ee_unit_to_th(pad.height)
            large_height = height + 8
            pad_name = f"{pad.shape}_{width}x{height}"            

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
                    if hole_height > hole_width:
                        # this slot is vertical
                        slot_width = hole_radius * 2
                        slot_height = hole_length + hole_radius * 2
                    else:
                        slot_width = hole_length + hole_radius * 2
                        slot_height = hole_radius * 2

                    xpedition_hole = SlotHole(
                        name=f"HOLE_{hole_radius * 2}x{hole_length}",
                        width=slot_width,
                        height=slot_height,
                        plated=pad.is_plated if hasattr(pad, "is_plated") else True
                    )
                else:
                    xpedition_hole = RoundHole(
                        name=f"HOLE_{round(ee_unit_to_th(pad.hole_radius * 2), 4)}",
                        diameter=ee_unit_to_th(pad.hole_radius * 2),
                        plated=pad.is_plated if hasattr(pad, "is_plated") else True
                    )

                padstack_name = f"{pad_name}_TH"
                xpedition_padstack = PinThroughPadStack(name=padstack_name)
                xpedition_padstack.set_pads(
                    top_pad=xpedition_pad,
                    bottom_pad=xpedition_pad,
                    internal_pad=xpedition_pad,
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
                    top_solderpaste_pad=xpedition_pad,
                    bottom_solderpaste_pad=xpedition_pad,
                    top_soldermask_pad=large_xpedition_pad,
                    bottom_soldermask_pad=large_xpedition_pad
                )

            if padstack_name not in self._padstacks:
                self._padstacks[padstack_name] = xpedition_padstack

            # Create a new pin for the pad SMD and TH
            x = ee_unit_to_th(pad.center_x) - ee_unit_to_th(self._bbox.x)
            y = ee_unit_to_th(pad.center_y) - ee_unit_to_th(self._bbox.y)
            pin = XpeditionPin(pad.number, x, y, xpedition_padstack, pad.rotation)
            self._cell.add_pin(pin)

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

            pin_number = self._cell.get_pin_count() + 1
            x = ee_unit_to_th(hole.center_x) - ee_unit_to_th(self._bbox.x)
            y = ee_unit_to_th(hole.center_y) - ee_unit_to_th(self._bbox.y)
            pin = XpeditionPin(pin_number, x, y, xpedition_padstack, 0)
            self._cell.add_pin(pin)

        # Determine mount type based on padstacks
        if all("SMD" in key for key in self._padstacks.keys()):
                mount_type = "SURFACE"
        elif all("TH" in key for key in self._padstacks.keys()):
            mount_type = "THROUGH"
        else:
            mount_type = "MIXED"
        self._cell.mount_type = mount_type

    def _add_shape_to_cell(self, shape: BaseShape, layer_name: str):
        xpedition_layer_name = self._map_easyeda_layer_to_xpedition(layer_name)
        if "UNKNOWN_LAYER" in xpedition_layer_name:
            print(f"Warning: Layer '{layer_name}' is not mapped to a known Xpedition layer. Skipping shape.")
            return

        if xpedition_layer_name == "SILKSCREEN_OUTLINE":
            silkscreen = SilkscreenOutline(shape, side="MNT_SIDE" if "Top" in layer_name else "OPP_SIDE")
            self._cell.add_silkscreen_outline(silkscreen)
        elif xpedition_layer_name == "ASSEMBLY_OUTLINE":
            assembly = AssemblyOutline(shape)
            self._cell.add_assembly_outline(assembly)
        elif xpedition_layer_name == "SOLDER_PASTE":
            solder_paste = SolderPaste(shape, side="MNT_SIDE" if "Top" in layer_name else "OPP_SIDE")
            self._cell.add_solder_paste(solder_paste)
        elif xpedition_layer_name == "SOLDER_MASK":
            solder_mask = SolderMask(shape, side="MNT_SIDE" if "Top" in layer_name else "OPP_SIDE")
            self._cell.add_solder_mask(solder_mask)

    def _convert_easyeda_shape_to_xpedition(self):
        # handle rect in layers to cell
        for rect in getattr(self._easyeda_footprint, "rectangles", []):
            layer_name = self._get_easyeda_layer_name(getattr(rect, "layer_id", 0))

            cx = ee_unit_to_th(getattr(rect, "x", 0)) - ee_unit_to_th(self._bbox.x)
            cy = ee_unit_to_th(getattr(rect, "y", 0)) - ee_unit_to_th(self._bbox.y)
            width = ee_unit_to_th(getattr(rect, "width", 0))
            height = ee_unit_to_th(getattr(rect, "height", 0))
            points = ((cx - width/2, cy + height/2), (cx + width/2, cy + height/2), (cx + width/2, cy - height/2), (cx - width/2, cy - height/2))
            shape = PolylineShape(points)
           
            self._add_shape_to_cell(shape, layer_name)

        # handle circle in layers to cell
        for circle in getattr(self._easyeda_footprint, "circles", []):
            layer_name = self._get_easyeda_layer_name(getattr(circle, "layer_id", 0))
            
            cx = ee_unit_to_th(getattr(circle, "cx", 0)) - ee_unit_to_th(self._bbox.x)
            cy = ee_unit_to_th(getattr(circle, "cy", 0)) - ee_unit_to_th(self._bbox.y)
            radius = ee_unit_to_th(getattr(circle, "radius", 0))
            width = ee_unit_to_th(getattr(circle, "stroke_width", 0))
            shape = CirclePath(center_x=cx, center_y=cy, radius=radius, width=width)

            self._add_shape_to_cell(shape, layer_name)

        for arc in getattr(self._easyeda_footprint, "arcs", []):
            layer_name = self._get_easyeda_layer_name(getattr(arc, "layer_id", 0))
            
            points = getattr(arc, "points", [])
            width = ee_unit_to_th(getattr(arc, "stroke_width", 0))

            # need to convert SVG ARC to PolyarcPath
            # shape = PolyarcPath(points=points, width=width)

            # self._add_shape_to_cell(shape, layer_name)

        for track in getattr(self._easyeda_footprint, "tracks", []):
            layer_name = self._get_easyeda_layer_name(getattr(track, "layer_id", 0))
            
            point_string = getattr(track, "points", "")
            points = []
            if point_string:
                pts = [float(x) for x in point_string.replace(",", " ").split()]
                for i in range(0, len(pts), 2):
                    points.append((ee_unit_to_th(pts[i]) - ee_unit_to_th(self._bbox.x), ee_unit_to_th(pts[i + 1]) - ee_unit_to_th(self._bbox.y)))

            width = ee_unit_to_th(getattr(track, "stroke_width", 0))
            shape = PolylinePath(points=points, width=width)
            self._add_shape_to_cell(shape, layer_name)

        for region in getattr(self._easyeda_footprint, "solid_regions", []):
            layer_name = self._get_easyeda_layer_name(getattr(region, "layer_id", 0))
            
            point_string = getattr(region, "points", "")
            points = []
            if point_string:
                # Remove SVG path commands like M, L, Z, etc.
                cleaned = re.sub(r'[MLHVCSQTAZmlhvcsqtaz]', ' ', point_string)
                pts = [float(x) for x in cleaned.replace(",", " ").split() if x.strip()]
                for i in range(0, len(pts), 2):
                    points.append((ee_unit_to_th(pts[i]) - ee_unit_to_th(self._bbox.x), ee_unit_to_th(pts[i + 1]) - ee_unit_to_th(self._bbox.y)))

            shape = PolylineShape(points=points)
            self._add_shape_to_cell(shape, layer_name)

        for area in getattr(self._easyeda_footprint, "copper_areas", []):
            layer_name = self._get_easyeda_layer_name(getattr(area, "layer_id", 0))
            
            point_string = getattr(area, "points", "")
            points = []
            if point_string:
                # Remove SVG path commands like M, L, Z, etc.
                cleaned = re.sub(r'[MLHVCSQTAZmlhvcsqtaz]', ' ', point_string)
                pts = [float(x) for x in cleaned.replace(",", " ").split() if x.strip()]
                for i in range(0, len(pts), 2):
                    points.append((ee_unit_to_th(pts[i]) - ee_unit_to_th(self._bbox.x), ee_unit_to_th(pts[i + 1]) - ee_unit_to_th(self._bbox.y)))

            shape = PolylineShape(points=points)
            self._add_shape_to_cell(shape, layer_name)

        # add placement outline
        grow_size = 10  # 10 mils grow size for the placement outline
        points = [
            (-ee_unit_to_th(self._easyeda_footprint.bbox.width / 2) - grow_size, -ee_unit_to_th(self._easyeda_footprint.bbox.height / 2) - grow_size),
            (ee_unit_to_th(self._easyeda_footprint.bbox.width / 2) + grow_size, -ee_unit_to_th(self._easyeda_footprint.bbox.height / 2) - grow_size),
            (ee_unit_to_th(self._easyeda_footprint.bbox.width / 2) + grow_size, ee_unit_to_th(self._easyeda_footprint.bbox.height / 2) + grow_size),
            (-ee_unit_to_th(self._easyeda_footprint.bbox.width / 2) - grow_size, ee_unit_to_th(self._easyeda_footprint.bbox.height / 2) + grow_size)
        ]
        shape = PolylineShape(points=points, filled=False)
        outline = PlacementOutline(shape=shape)
        self._cell.add_placement_outline(outline)

    def save_padstacks_to_file(self, filename: str):
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

    def save_cell_to_file(self, filename: str):
        with open(filename, 'w') as f:
            f.write(".FILETYPE CELL_LIBRARY\n"
                    ".VERSION \"1.01.01\"\n"
                    ".CREATOR \"EasyEDA to Xpedition Converter\"\n"
                    "\n"
                    ".UNITS TH\n"
                    "\n")
            
            package_string = f".PACKAGE_CELL \"{self._cell.name}\"\n"
            package_string += f" ..NUMBER_LAYERS {self._cell.number_layers}\n"
            package_string += f" ..PACKAGE_GROUP {self._cell.package_group}\n"
            package_string += f" ..MOUNT_TYPE {self._cell.mount_type}\n"
            f.write(package_string)

            for pin in self._cell.pins:
                f.write(str(pin) + "\n")

            for outline in self._cell.silkscreen_outlines:
                f.write(str(outline) + "\n")

            for outline in self._cell.assembly_outlines:
                f.write(str(outline) + "\n")

            for mask in self._cell.solder_masks:
                f.write(str(mask) + "\n")

            for paste in self._cell.solder_pastes:
                f.write(str(paste) + "\n")

            for outline in self._cell.placement_outlines:
                f.write(str(outline) + "\n")

            for text in self._cell.texts:
                f.write(text + "\n")

if __name__ == "__main__":
    tgt_folder = "../output"  # Specify your target folder here
    easyead_cad_data = easyeda_api.EasyedaApi().get_cad_data_of_component(
        lcsc_id="C165948"
    )  # Replace with a valid LCSC ID

    converter = FootprintConverter(easyead_cad_data, output_folder=tgt_folder)
    converter.convert()
    converter.save_padstacks_to_file(f"{tgt_folder}/_Pads.hkp")
    converter.save_cell_to_file(f"{tgt_folder}/_Cell.hkp")

    print(f"Converted footprint Done. Pads saved to {tgt_folder}/_Pads.hkp and Cell saved to {tgt_folder}/_Cell.hkp")