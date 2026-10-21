from types import SimpleNamespace

from easyeda2xpedition.viewer.easyeda_viewer import EasyedaViewer
from easyeda2xpedition.viewer.xpedition_viewer import XpeditionViewer
from easyeda2xpedition.xpedition.parts import (
    Part,
    PartGate,
    PartPin,
    PartsLibrary,
)


def make_viewer():
    return object.__new__(XpeditionViewer)


def test_detect_file_types():
    viewer = make_viewer()

    assert viewer._detect_file_type(['.FILETYPE CELL_LIBRARY', '.PACKAGE_CELL "X"']) == "cell"
    assert viewer._detect_file_type(['.FILETYPE PADSTACK_LIBRARY']) == "padstack"
    assert viewer._detect_file_type(["V 50", "K 1 TEST"]) == "symbol"
    assert viewer._detect_file_type(['.Filetype ASCII_PDB', '.Number "C1"']) == "part"


def test_parse_part_library():
    viewer = make_viewer()
    content = "\n".join(
        [
            "!.LCID 2052",
            ".Filetype ASCII_PDB",
            '.Number "C25804"',
            '\t..Name "0603WAF1002T5E"',
            '\t..Label "0603WAF1002T5E"',
            '\t..Desc "10K 1% 0603"',
            '\t..RefPrefix "R"',
            '\t..TopCell "R0603"',
            '\t..BottomCell "R0603"',
            '\t..Prop "Type",\t"Resistor",\t"Text"',
            '\t..Prop "Manufacturer",\t"UNI-ROYAL",\t"Text"',
            '\t..SwapGroup\t"gate1"',
            '\t\t...SwapID\t"P0"',
            '\t..Symbol\t"EasyEDA:0603WAF1002T5E"',
            '\t\t...Symbol_SwapGroup\t"gate1"',
            '\t\t\t....PinName\t"1"',
            '\t\t\t....PinName\t"2"',
            '\t..Slots',
            '\t\t...Slot_SwapGroup\t"gate1"',
            '\t\t\t....PinNumber\t"1"',
            '\t\t\t....PinNumber\t"2"',
            "",
            '.Number "C2"',
            '\t..Name "SECOND"',
        ]
    )

    parts = viewer._parse_part_library(content)

    assert len(parts) == 2
    assert parts[0]["number"] == "C25804"
    assert parts[0]["name"] == "0603WAF1002T5E"
    assert parts[0]["label"] == "0603WAF1002T5E"
    assert parts[0]["description"] == "10K 1% 0603"
    assert parts[0]["ref_prefix"] == "R"
    assert parts[0]["top_cell"] == "R0603"
    assert parts[0]["symbol_ref"] == "EasyEDA:0603WAF1002T5E"
    assert parts[0]["properties"] == [
        ("Type", "Resistor", "Text"),
        ("Manufacturer", "UNI-ROYAL", "Text"),
    ]
    assert parts[0]["gates"] == [{"name": "gate1", "pins": ["1", "2"]}]
    assert parts[1]["number"] == "C2"
    assert parts[1]["name"] == "SECOND"


def test_parse_generated_part_library():
    viewer = make_viewer()
    part = Part(
        number="C1",
        name="TEST",
        label="TEST",
        description="A test part",
        ref_prefix="R",
        top_cell="R0603",
        symbol_ref="EasyEDA:TEST",
        properties=[("Type", "Resistor", "Text")],
        gates=[
            PartGate("gate1", [PartPin("1", "1"), PartPin("2", "2")]),
            PartGate("gate2", [PartPin("3", "3")]),
        ],
    )

    parsed = viewer._parse_part_library(str(PartsLibrary([part])))

    assert len(parsed) == 1
    assert parsed[0]["number"] == "C1"
    assert parsed[0]["name"] == "TEST"
    assert parsed[0]["description"] == "A test part"
    assert parsed[0]["top_cell"] == "R0603"
    assert parsed[0]["symbol_ref"] == "EasyEDA:TEST"
    assert parsed[0]["properties"] == [("Type", "Resistor", "Text")]
    assert parsed[0]["gates"] == [
        {"name": "gate1", "pins": ["1", "2"]},
        {"name": "gate2", "pins": ["3"]},
    ]


def test_parse_part_library_unescapes_quotes():
    viewer = make_viewer()
    parts = viewer._parse_part_library(
        '.Number "C1"\n\t..Prop "Note",\t"say \\"hi\\"",\t"Text"'
    )

    assert parts[0]["properties"] == [("Note", 'say "hi"', "Text")]


def test_find_part_symbol_and_cell_files(tmp_path):
    viewer = make_viewer()
    symbol_path = tmp_path / "TEST_xpedition.1"
    symbol_path.write_text("V 50\nK 1 TEST\n", encoding="utf-8")
    cell_path = tmp_path / "_Cell.hkp"
    cell_path.write_text(
        '.FILETYPE CELL_LIBRARY\n.PACKAGE_CELL "R0603"\n', encoding="utf-8"
    )
    part = {
        "symbol_ref": "EasyEDA:TEST",
        "top_cell": "R0603",
        "bottom_cell": "R0603",
    }

    assert viewer._find_symbol_file(part, str(tmp_path)) == str(symbol_path)
    assert viewer._find_cell_file(part, str(tmp_path)) == str(cell_path)


def test_format_easyeda_part_properties():
    viewer = object.__new__(EasyedaViewer)
    symbol = SimpleNamespace(
        info=SimpleNamespace(
            lcsc_id="C25804",
            name="0603WAF1002T5E",
            mpn="0603WAF1002T5E",
            manufacturer="UNI-ROYAL",
            prefix="R",
            package="R0603",
            jlc_id="Basic Part",
            datasheet="https://example.com/C25804",
        ),
        subs=[SimpleNamespace(pins=[1, 2])],
    )
    footprint = SimpleNamespace(
        info=SimpleNamespace(
            name="R0603", fp_type="smd", model_3d_name="R0603"
        ),
        pads=[1, 2],
        tracks=[],
        holes=[],
        circles=[],
        rectangles=[],
    )

    text = viewer._format_easyeda_part_properties(symbol, footprint)

    assert "LCSC ID: C25804" in text
    assert "Manufacturer: UNI-ROYAL" in text
    assert "Symbol pins: 2" in text
    assert "Footprint pads: 2" in text


def test_parse_cell_pin_and_shape():
    viewer = make_viewer()
    sections = viewer._cell_sections(
        [
            '.PACKAGE_CELL "TEST"',
            ' ..PIN "1"',
            "  ...XY (10, 20)",
            '  ...PADSTACK "RECT_1x2_SMD"',
            "  ...ROTATION 90",
            " ..SILKSCREEN_OUTLINE",
            "  ...POLYLINE_PATH",
            "   ....WIDTH 10",
            "   ....XY (-10, 20)",
            "\t\t\t(-10, 30)",
            "   ....SHAPE_OPTIONS NOT_FILLED",
        ]
    )

    assert [section["header"] for section in sections] == ["..PIN", "..SILKSCREEN_OUTLINE"]

    pin = viewer._parse_cell_pin(sections[0])
    assert pin == {
        "number": "1",
        "x": 10.0,
        "y": 20.0,
        "padstack": "RECT_1x2_SMD",
        "rotation": 90.0,
    }

    shape = viewer._parse_cell_shape(sections[1])
    assert shape["layer"] == "SILKSCREEN_OUTLINE"
    assert shape["points"] == [(-10.0, 20.0), (-10.0, 30.0)]
    assert shape["width"] == 10.0
    assert shape["filled"] is False


def test_parse_pad_library():
    viewer = make_viewer()
    viewer._parse_pad_library_lines(
        [
            ".FILETYPE PADSTACK_LIBRARY",
            '.PAD "RECT_1x2"',
            "..RECTANGLE",
            "...WIDTH 1",
            "...HEIGHT 2",
            '.PAD "RECT_1x2L"',
            "..RECTANGLE",
            "...WIDTH 1.8",
            "...HEIGHT 2.8",
            '.HOLE "HOLE_0.5"',
            "..ROUND",
            "...DIAMETER 0.5",
            '.PADSTACK "RECT_1x2_SMD"',
            '...TOP_PAD "RECT_1x2"',
            '...TOP_SOLDERPASTE_PAD "RECT_1x2"',
            '...TOP_SOLDERMASK_PAD "RECT_1x2L"',
            '...HOLE_NAME "HOLE_0.5"',
        ]
    )

    assert viewer.pads["RECT_1x2"]["kind"] == "rect"
    assert viewer.pads["RECT_1x2"]["width"] == 1.0
    assert viewer.pads["RECT_1x2"]["height"] == 2.0
    assert viewer.holes["HOLE_0.5"]["kind"] == "round"
    assert viewer.holes["HOLE_0.5"]["diameter"] == 0.5
    assert viewer.padstacks["RECT_1x2_SMD"]["pad"] == "RECT_1x2"
    assert viewer.padstacks["RECT_1x2_SMD"]["soldermask"] == "RECT_1x2L"
    assert viewer.padstacks["RECT_1x2_SMD"]["solderpaste"] == "RECT_1x2"
    assert viewer.padstacks["RECT_1x2_SMD"]["hole"] == "HOLE_0.5"


def test_easyeda_symbol_pin_endpoints():
    def make_pin(path, x=0.0, y=0.0):
        return SimpleNamespace(
            settings=SimpleNamespace(pos_x=x, pos_y=y),
            pin_path=SimpleNamespace(path=path),
        )

    assert EasyedaViewer._symbol_pin_endpoints(
        make_pin("M 495 260 h 10", 495, 260)
    ) == ((495.0, 260.0), (505.0, 260.0))
    assert EasyedaViewer._symbol_pin_endpoints(
        make_pin("M 40 -0 h-10", 40, 0)
    ) == ((40.0, -0.0), (30.0, -0.0))
    assert EasyedaViewer._symbol_pin_endpoints(
        make_pin("M 10 20 v -10", 10, 20)
    ) == ((10.0, 20.0), (10.0, 10.0))
    assert EasyedaViewer._symbol_pin_endpoints(
        make_pin("invalid", 7, 8)
    ) == ((7, 8), (7, 8))

def test_easyeda_symbol_subparts():
    sub_one = SimpleNamespace(name="Unit A", pins=[1, 2])
    sub_two = SimpleNamespace(name="Unit B", pins=[3])
    symbol = SimpleNamespace(subs=[sub_one, sub_two])

    assert EasyedaViewer._get_symbol_subs(symbol) == [sub_one, sub_two]
    assert EasyedaViewer._symbol_sub_label(sub_one, 0) == "Unit A (2 pins)"
    assert EasyedaViewer._symbol_sub_label(sub_two, 1) == "Unit B (1 pins)"
    assert EasyedaViewer._get_symbol_subs(None) == []

    single = SimpleNamespace(name="Single")
    assert EasyedaViewer._get_symbol_subs(single) == [single]


def test_xpedition_symbol_part_paths(tmp_path):
    first = tmp_path / "TEST_xpedition.1"
    second = tmp_path / "TEST_xpedition.2"
    third = tmp_path / "TEST_xpedition.3"
    for path in (first, second, third):
        path.write_text("V 50\nK 1 TEST\n", encoding="utf-8")

    assert XpeditionViewer._symbol_part_paths(str(second)) == [
        str(first),
        str(second),
        str(third),
    ]


def test_xpedition_split_symbol_sections():
    sections = XpeditionViewer._split_symbol_sections(
        [
            "V 50",
            "K 1 MAIN",
            "Y 1",
            "K 2 AMP.1",
            "D 0 10 20 0",
            "P 1 -1 -1 1 -1 0 2 0",
            "K 3 AMP.2",
            "l 2 0 0 1 1",
        ]
    )

    assert [name for name, _ in sections] == ["AMP.1", "AMP.2"]
    assert sections[0][1][0] == "K 2 AMP.1"
    assert sections[1][1][0] == "K 3 AMP.2"

def test_easyeda_pin_name_placement_helpers():
    assert EasyedaViewer._easyeda_text_anchor("start") == "w"
    assert EasyedaViewer._easyeda_text_anchor("end") == "e"
    assert EasyedaViewer._easyeda_text_anchor("middle") == "center"
    assert EasyedaViewer._easyeda_text_anchor("") == "center"

    assert EasyedaViewer._pin_name_position((0, 0), (10, 0)) == (18.0, 0.0)
    assert EasyedaViewer._pin_name_position((40, 0), (30, 0)) == (22.0, 0.0)
    assert EasyedaViewer._pin_name_position((5, 5), (5, 5)) == (5, 5)
