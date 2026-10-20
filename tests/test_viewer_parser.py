from easyeda2xpedition.viewer.xpedition_viewer import XpeditionViewer


def make_viewer():
    return object.__new__(XpeditionViewer)


def test_detect_file_types():
    viewer = make_viewer()

    assert viewer._detect_file_type(['.FILETYPE CELL_LIBRARY', '.PACKAGE_CELL "X"']) == "cell"
    assert viewer._detect_file_type(['.FILETYPE PADSTACK_LIBRARY']) == "padstack"
    assert viewer._detect_file_type(["V 50", "K 1 TEST"]) == "symbol"


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
