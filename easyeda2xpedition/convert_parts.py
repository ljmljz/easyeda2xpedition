import re

from easyeda2xpedition.easyeda.easyeda_importer import EasyedaSymbolImporter
from easyeda2xpedition.easyeda.parameters_easyeda import EasyedaPinType
from easyeda2xpedition.xpedition.parts.part import (
    Part,
    PartGate,
    PartPin,
    PartsLibrary,
)


class EeSymbolToXpeditionPart(object):
    def __init__(
        self,
        easyeda_cad_data: dict,
        symbol_library: str = "EasyEDA",
        part_number: str = None,
    ):
        self.easyeda_cad_data = easyeda_cad_data
        self.symbol_library = symbol_library
        self._part_number = part_number
        self.easyeda_symbol = EasyedaSymbolImporter(
            easyeda_cad_data
        ).get_symbol()
        self.part = self.convert()

    def convert(self) -> Part:
        info = self.easyeda_symbol.info
        name = info.name or ""
        number = self._part_number or info.lcsc_id or name
        label = info.mpn or name
        description = (
            self.easyeda_cad_data.get("description")
            or self.easyeda_cad_data.get("dataStr", {})
            .get("head", {})
            .get("c_para", {})
            .get("Description")
            or ""
        )
        ref_prefix = self._ref_prefix(info.prefix)
        top_cell = info.package or ""
        symbol_ref = f"{self.symbol_library}:{name}" if name else ""

        properties = [("Type", self._part_type(ref_prefix), "Text")]
        if info.manufacturer:
            properties.append(("Manufacturer", info.manufacturer, "Text"))
        if info.mpn:
            properties.append(("Manufacturer Part Number", info.mpn, "Text"))
        if info.lcsc_id:
            properties.append(("Supplier Part Number", info.lcsc_id, "Text"))
        if info.datasheet:
            properties.append(("Datasheet", info.datasheet, "Text"))
        if info.jlc_id:
            properties.append(("JLCPCB Part Class", info.jlc_id, "Text"))

        return Part(
            number=number,
            name=name,
            label=label,
            description=str(description),
            ref_prefix=ref_prefix,
            top_cell=top_cell,
            symbol_ref=symbol_ref,
            properties=properties,
            gates=self._convert_gates(),
        )

    def _convert_gates(self):
        subparts = self.easyeda_symbol.subs
        gates = []
        total = len(subparts)
        if total == 0:
            return gates

        for index, subpart in enumerate(subparts, start=1):
            gate_name = "gate" if total == 1 else f"gate{index}"
            gates.append(PartGate(gate_name, self._convert_pins(subpart.pins)))
        return gates

    def _convert_pins(self, pins):
        converted = []
        used_names = []
        for index, pin in enumerate(pins, start=1):
            number = (pin.number.text or "").strip() or str(index)
            name = (pin.name.text or "").strip() or number
            name = self._unique_name(name, used_names)
            used_names.append(name)
            converted.append(
                PartPin(
                    name=name,
                    number=number,
                    pin_type=self._pin_type(pin),
                )
            )
        return converted

    @staticmethod
    def _unique_name(name: str, used_names) -> str:
        if name not in used_names:
            return name

        index = 1
        while f"{name}_{index}" in used_names:
            index += 1
        return f"{name}_{index}"

    @staticmethod
    def _pin_type(pin) -> str:
        pin_type = getattr(pin.settings, "type", None)
        mapping = {
            EasyedaPinType._input: "Input",
            EasyedaPinType.output: "Output",
            EasyedaPinType.bidirectional: "Bidir",
            EasyedaPinType.power: "Power",
            EasyedaPinType.unspecified: "Bidir",
        }
        return mapping.get(pin_type, "Bidir")

    @staticmethod
    def _ref_prefix(prefix: str) -> str:
        prefix = (prefix or "").strip()
        prefix = re.sub(r"\.\d+$", "", prefix)
        prefix = prefix.rstrip("?")
        return prefix or "U"

    @staticmethod
    def _part_type(ref_prefix: str) -> str:
        mapping = {
            "R": "Resistor",
            "C": "Capacitor",
            "L": "Inductor",
            "D": "Diode",
            "LED": "LED",
            "Q": "Transistor",
            "U": "IC",
            "IC": "IC",
            "J": "Connector",
            "P": "Connector",
            "Y": "Crystal",
            "X": "Crystal",
            "K": "Relay",
            "F": "Fuse",
            "SW": "Switch",
            "TP": "Test Point",
        }
        return mapping.get((ref_prefix or "").upper(), "Other")

    def to_pdb(self) -> str:
        return str(PartsLibrary([self.part]))

    def save_to_file(self, file_path: str):
        PartsLibrary([self.part]).save_to_file(file_path)
