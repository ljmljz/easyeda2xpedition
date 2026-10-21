import re

from easyeda2xpedition.convert_parts import EeSymbolToXpeditionPart
from easyeda2xpedition.xpedition.parts import (
    Part,
    PartGate,
    PartPin,
    PartsLibrary,
)


def _pin(number, name, x, pin_type=0):
    return "^^".join(
        [
            f"P~show~{pin_type}~{number}~{x}~0~0~gge{number}~0",
            f"{x}~0",
            f"M {x} 0 h10~#000000",
            f"1~{x + 10}~5~0~{name}~start~~~#000000",
            f"1~{x + 10}~-5~0~{number}~end~~~#000000",
            f"0~{x}~0",
            "0~M 0 0",
        ]
    )


def _symbol_data(shape=None, subparts=None):
    data = {
        "description": "10K 1% 0603",
        "lcsc": {"number": "C25804", "url": "https://example.com/C25804"},
        "dataStr": {
            "head": {
                "x": "0",
                "y": "0",
                "c_para": {
                    "pre": "R?",
                    "name": "0603WAF1002T5E",
                    "package": "R0603",
                    "Manufacturer": "UNI-ROYAL",
                    "Manufacturer Part": "0603WAF1002T5E",
                    "JLCPCB Part Class": "Basic Part",
                },
            },
            "BBox": {"x": "-4", "y": "-4", "width": "48", "height": "8"},
        },
    }
    if shape is not None:
        data["dataStr"]["shape"] = shape
    if subparts is not None:
        data["subparts"] = subparts
    return data


class TestPartsModel:
    def test_library_header_and_sections(self):
        part = Part(
            number="C1",
            name="TEST",
            label="TEST",
            description="A test part",
            ref_prefix="R",
            top_cell="R0603",
            symbol_ref="EasyEDA:TEST",
            properties=[("Type", "Resistor", "Text")],
            gates=[PartGate("gate", [PartPin("1", "1"), PartPin("2", "2")])],
        )

        text = str(PartsLibrary([part]))
        lines = text.splitlines()

        assert lines[:7] == [
            "!.LCID 2052",
            ".Filetype ASCII_PDB",
            '.Version "02.01"',
            '.LIBRARY_DB_TYPE "Enterprise"',
            ".Units mm",
            ".Notation Si",
            "",
        ]
        assert '.Number "C1"' in lines
        assert '\t..Name "TEST"' in lines
        assert "\t\t...Default" in lines
        assert '\t..Desc "A test part"' in lines
        assert '\t..TopCell "R0603"' in lines
        assert '\t..Prop "Type",\t"Resistor",\t"Text"' in lines
        assert '\t..SwapGroup\t"gate"' in lines
        assert '\t\t...SwapID\t"P0"' in lines
        assert '\t..Symbol\t"EasyEDA:TEST"' in lines
        assert '\t\t\t....PinName\t"1"' in lines
        assert "\t..Slots" in lines
        assert "\t\t\t....SlotID\t1" in lines
        assert '\t\t\t....PinNumber\t"1"' in lines
        assert text.endswith("\n")

    def test_quote_escapes_special_characters(self):
        part = Part(
            number='C"1',
            name="TEST",
            description="line1\nline2",
            gates=[],
        )
        text = str(PartsLibrary([part]))
        assert '.Number "C\\"1"' in text
        assert '\t..Desc "line1 line2"' in text


class TestPartConverter:
    def test_metadata_and_pin_mapping(self):
        converter = EeSymbolToXpeditionPart(
            _symbol_data(shape=[_pin("2", "2", 40), _pin("1", "1", 0)])
        )
        part = converter.part

        assert part.number == "C25804"
        assert part.name == "0603WAF1002T5E"
        assert part.label == "0603WAF1002T5E"
        assert part.description == "10K 1% 0603"
        assert part.ref_prefix == "R"
        assert part.top_cell == "R0603"
        assert part.symbol_ref == "EasyEDA:0603WAF1002T5E"
        assert ("Type", "Resistor", "Text") in part.properties
        assert ("Manufacturer", "UNI-ROYAL", "Text") in part.properties
        assert ("Supplier Part Number", "C25804", "Text") in part.properties

        assert len(part.gates) == 1
        assert part.gates[0].name == "gate"
        assert [pin.name for pin in part.gates[0].pins] == ["2", "1"]
        assert [pin.number for pin in part.gates[0].pins] == ["2", "1"]

    def test_duplicate_pin_names_are_disambiguated(self):
        converter = EeSymbolToXpeditionPart(
            _symbol_data(shape=[_pin("1", "A", 0), _pin("2", "A", 40)])
        )

        assert [pin.name for pin in converter.part.gates[0].pins] == [
            "A",
            "A_1",
        ]

    def test_pin_type_mapping(self):
        converter = EeSymbolToXpeditionPart(
            _symbol_data(
                shape=[
                    _pin("1", "IN", 0, pin_type=1),
                    _pin("2", "OUT", 40, pin_type=2),
                    _pin("3", "IO", 80, pin_type=3),
                    _pin("4", "VCC", 120, pin_type=4),
                ]
            )
        )

        assert [pin.pin_type for pin in converter.part.gates[0].pins] == [
            "Input",
            "Output",
            "Bidir",
            "Power",
        ]

    def test_multipart_creates_multiple_gates_and_slots(self):
        subparts = [
            {
                "title": "TEST.1",
                "dataStr": {
                    "BBox": {
                        "x": "0",
                        "y": "0",
                        "width": "20",
                        "height": "20",
                    },
                    "shape": [_pin("1", "A", 0)],
                },
            },
            {
                "title": "TEST.2",
                "dataStr": {
                    "BBox": {
                        "x": "0",
                        "y": "0",
                        "width": "20",
                        "height": "20",
                    },
                    "shape": [_pin("2", "B", 0)],
                },
            },
        ]
        converter = EeSymbolToXpeditionPart(_symbol_data(subparts=subparts))
        part = converter.part
        text = converter.to_pdb()

        assert [gate.name for gate in part.gates] == ["gate1", "gate2"]
        assert '\t..SwapGroup\t"gate1"' in text
        assert '\t..SwapGroup\t"gate2"' in text
        assert "\t\t\t....SlotID\t1" in text
        assert "\t\t\t....SlotID\t2" in text
        assert '\t\t\t....PinNumber\t"1"' in text
        assert '\t\t\t....PinNumber\t"2"' in text

    def test_ref_prefix_and_part_number_overrides(self):
        data = _symbol_data(shape=[_pin("1", "1", 0)])
        data["dataStr"]["head"]["c_para"]["pre"] = "U?.2"

        converter = EeSymbolToXpeditionPart(data, part_number="CUSTOM-1")

        assert converter.part.number == "CUSTOM-1"
        assert converter.part.ref_prefix == "U"
        assert ("Type", "IC", "Text") in converter.part.properties

    def test_save_to_file_uses_lf_and_utf8(self, tmp_path):
        converter = EeSymbolToXpeditionPart(
            _symbol_data(shape=[_pin("1", "1", 0)])
        )
        output = tmp_path / "test.pdb.hkp"

        converter.save_to_file(str(output))
        raw = output.read_bytes()
        text = raw.decode("utf-8")

        assert b"\r\n" not in raw
        assert raw.endswith(b"\n")
        assert ".Filetype ASCII_PDB" in text
        assert '.Number "C25804"' in text
        assert re.search(r"\t\.\.Symbol\t\"EasyEDA:0603WAF1002T5E\"", text)
