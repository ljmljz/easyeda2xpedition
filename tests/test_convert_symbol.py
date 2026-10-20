"""
Unit tests for EasyEDA to Xpedition symbol conversion.

This module contains tests for the EeSymbolToXpeditionSymbol class, covering:
- Symbol initialization and conversion
- Pin position and side calculation
- Pin type mapping
- Rotation calculations
- Shape conversions
- File output operations
"""

import pytest
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock, patch, mock_open
from easyeda2xpedition.convert_symbol import EeSymbolToXpeditionSymbol


class TestSymbolUnitConversion:
    """Tests for unit conversion in symbol conversion."""

    def test_ee_unit_to_th_for_symbols(self):
        """Test that EasyEDA symbol units map 1:1 to the Xpedition V 50 symbol unit."""
        from easyeda2xpedition.convert_symbol import ee_unit_to_th

        assert ee_unit_to_th(100.0) == 100.0
        assert ee_unit_to_th(50.5) == 50.5
        assert ee_unit_to_th(0.0) == 0.0
        assert ee_unit_to_th(-25.0) == -25.0


class TestSymbolGridAlignment:
    """Tests for aligning symbol pins and outlines to the 0.1 inch grid."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_pins_and_outline_align_to_point_one_inch_grid(self, mock_importer_class):
        mock_importer_class.return_value.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )
        converter = EeSymbolToXpeditionSymbol({})
        bbox = SimpleNamespace(x=473.9, y=249.7)
        pin = SimpleNamespace(pin_path=SimpleNamespace(path="M 495 260 h 10"))

        converter._align_to_grid(bbox, [pin])

        assert converter._x(495, bbox) == 20
        assert converter._y(260, bbox) == -10
        assert converter._x(505, bbox) == 30
        assert converter._x(555, bbox) == 80
        assert converter._y(250, bbox) == 0
        assert converter._y(380, bbox) == -130

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_convert_subpart_aligns_before_conversion(self, mock_importer_class):
        mock_importer_class.return_value.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )
        converter = EeSymbolToXpeditionSymbol({})
        bbox = SimpleNamespace(x=327.6, y=134.7)
        pin = SimpleNamespace(pin_path=SimpleNamespace(path="M 330 145 h 10"))
        subpart = MagicMock(bbox=bbox, pins=[pin])

        with patch.object(converter, 'convert_pin_groups_for_subpart'), \
                patch.object(converter, 'convert_shapes_for_subpart'):
            converter.convert_subpart(subpart, "TEST.1")

        assert converter._x(330, bbox) == 0
        assert converter._y(145, bbox) == -10
        assert converter._x(340, bbox) == 10
        assert converter._y(135, bbox) == 0


class TestSymbolPinLength:
    """Tests for the generated 0.2 inch pin length."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def make_converter(self, mock_importer_class):
        mock_importer_class.return_value.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )
        return EeSymbolToXpeditionSymbol({})

    def _pin(self, path, rotation):
        return SimpleNamespace(
            pin_path=SimpleNamespace(path=path),
            settings=SimpleNamespace(rotation=rotation),
        )

    def test_left_pin_has_point_two_inch_length(self):
        converter = self.make_converter()
        bbox = SimpleNamespace(x=473.9, y=249.7)
        pin = self._pin("M 495 260 h 10", 180)
        converter._align_to_grid(bbox, [pin])

        body_x, body_y, end_x, end_y, side = converter._pin_endpoints(pin, bbox)

        assert (body_x, body_y) == (30, -10)
        assert (end_x, end_y) == (10, -10)
        assert side == 2

    def test_right_pin_has_point_two_inch_length(self):
        converter = self.make_converter()
        bbox = SimpleNamespace(x=473.9, y=249.7)
        pin = self._pin("M 565 340 h -10", 180)
        converter._align_to_grid(bbox, [pin])

        body_x, body_y, end_x, end_y, side = converter._pin_endpoints(pin, bbox)

        assert (body_x, body_y) == (80, -90)
        assert (end_x, end_y) == (100, -90)
        assert side == 3

    def test_top_pin_extends_upwards(self):
        converter = self.make_converter()
        bbox = SimpleNamespace(x=90, y=40)
        pin = self._pin("M 100 50 v 10", 0)
        converter._align_to_grid(bbox, [pin])

        body_x, body_y, end_x, end_y, side = converter._pin_endpoints(pin, bbox)

        assert side == 0
        assert (body_x, body_y) == (10, -20)
        assert (end_x, end_y) == (10, 0)

    def test_bottom_pin_extends_downwards(self):
        converter = self.make_converter()
        bbox = SimpleNamespace(x=90, y=40)
        pin = self._pin("M 100 60 v -10", 0)
        converter._align_to_grid(bbox, [pin])

        body_x, body_y, end_x, end_y, side = converter._pin_endpoints(pin, bbox)

        assert side == 1
        assert (body_x, body_y) == (10, -10)
        assert (end_x, end_y) == (10, -30)


class TestSymbolConverterInitialization:
    """Tests for symbol converter initialization."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_symbol_converter_initialization(self, mock_importer_class):
        """Test initialization of symbol converter."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        
        mock_symbol = MagicMock()
        mock_symbol.info.name = "TEST_SYMBOL"
        mock_symbol.info.prefix = "U"
        mock_symbol.info.mpn = "TEST_MPN"
        mock_symbol.info.manufacturer = "TEST_MFG"
        mock_importer.get_symbol.return_value = mock_symbol

        cad_data = {"cad": {"meta": {"name": "TEST"}}}
        converter = EeSymbolToXpeditionSymbol(cad_data)

        assert converter.easyeda_cad_data == cad_data
        assert converter.easyeda_symbol is not None
        assert converter.xpedition_symbol.name == "TEST_SYMBOL"
        assert converter._pin_name_list == []

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_symbol_info_assignment(self, mock_importer_class):
        """Test that symbol info is correctly assigned during conversion."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        
        mock_symbol = MagicMock()
        mock_symbol.info.name = "IC_CHIP"
        mock_symbol.info.prefix = "U"
        mock_symbol.info.mpn = "STM32F103"
        mock_symbol.info.manufacturer = "STMicroelectronics"
        mock_symbol.subs = []
        mock_symbol.pins = []
        mock_importer.get_symbol.return_value = mock_symbol

        cad_data = {}
        converter = EeSymbolToXpeditionSymbol(cad_data)
        result = converter.convert()

        assert result.refdes == "U"
        assert result.value == "STM32F103"
        assert result.mfg_name == "STMicroelectronics"
        assert result.mpn == "STM32F103"
        assert result.dev_name == "IC_CHIP"
        assert result.name == "IC_CHIP"


class TestRotationCalculations:
    """Tests for rotation angle to Xpedition rotation code conversion."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_rotation_0_degrees(self, mock_importer_class):
        """Test conversion of 0 degrees rotation."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        result = converter._calc_rotation_from_angle(0)
        assert result == 0

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_rotation_90_degrees(self, mock_importer_class):
        """Test conversion of 90 degrees rotation."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        result = converter._calc_rotation_from_angle(90)
        assert result == 1

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_rotation_180_degrees(self, mock_importer_class):
        """Test conversion of 180 degrees rotation."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        result = converter._calc_rotation_from_angle(180)
        assert result == 2

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_rotation_270_degrees(self, mock_importer_class):
        """Test conversion of 270 degrees rotation."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        result = converter._calc_rotation_from_angle(270)
        assert result == 3

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_rotation_invalid_angle(self, mock_importer_class):
        """Test that invalid rotation angles raise ValueError."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        with pytest.raises(ValueError, match="angle must be 0, 90, 180 or 270"):
            converter._calc_rotation_from_angle(45)


class TestPinSideCalculations:
    """Tests for pin side determination based on position."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_anchor_from_side_top(self, mock_importer_class):
        """Test anchor positions for top side pins."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        anchors = converter._get_anchor_from_side(0)
        assert anchors == (2, 3)

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_anchor_from_side_bottom(self, mock_importer_class):
        """Test anchor positions for bottom side pins."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        anchors = converter._get_anchor_from_side(1)
        assert anchors == (8, 9)

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_anchor_from_side_left(self, mock_importer_class):
        """Test anchor positions for left side pins."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        anchors = converter._get_anchor_from_side(2)
        assert anchors == (2, 3)

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_anchor_from_side_right(self, mock_importer_class):
        """Test anchor positions for right side pins."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        anchors = converter._get_anchor_from_side(3)
        assert anchors == (8, 9)


class TestPinTypeMapping:
    """Tests for EasyEDA pin type to Xpedition pin type mapping."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_pin_type_input(self, mock_importer_class):
        """Test conversion of Input pin type."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        mock_pin = MagicMock()
        mock_pin.settings.type = "Input"
        result = converter._get_xpedition_pin_type(mock_pin)
        
        assert result == "Input"

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_pin_type_output(self, mock_importer_class):
        """Test conversion of Output pin type."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        mock_pin = MagicMock()
        mock_pin.settings.type = "Output"
        result = converter._get_xpedition_pin_type(mock_pin)
        
        # Note: There's a typo in the original code: "Ouput"
        assert result == "Ouput"

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_pin_type_io(self, mock_importer_class):
        """Test conversion of I/O pin type."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        mock_pin = MagicMock()
        mock_pin.settings.type = "I/O"
        result = converter._get_xpedition_pin_type(mock_pin)
        
        assert result == "BI"

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_pin_type_power(self, mock_importer_class):
        """Test conversion of Power pin type (undefined)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        mock_pin = MagicMock()
        mock_pin.settings.type = "Power"
        result = converter._get_xpedition_pin_type(mock_pin)
        
        # Power type is not in the mapping, returns None
        assert result is None

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_pin_type_undefined(self, mock_importer_class):
        """Test conversion of undefined pin type."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        mock_pin = MagicMock()
        mock_pin.settings.type = "Undefined"
        result = converter._get_xpedition_pin_type(mock_pin)
        
        assert result is None


class TestPinNameDetermination:
    """Tests for pin name deduplication logic."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_determine_pin_name_unique(self, mock_importer_class):
        """Test pin name determination for unique names."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        mock_pin = MagicMock()
        mock_pin.name.text = "GND"
        result = converter._determine_pin_name(mock_pin)
        
        assert result == "GND"
        assert "GND" in converter._pin_name_list

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_determine_pin_name_duplicate(self, mock_importer_class):
        """Test pin name determination for duplicate names."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        converter._pin_name_list = ["VCC"]
        
        mock_pin = MagicMock()
        mock_pin.name.text = "VCC"
        result = converter._determine_pin_name(mock_pin)
        
        assert result == "VCC_1"
        assert "VCC_1" in converter._pin_name_list

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_determine_pin_name_multiple_duplicates(self, mock_importer_class):
        """Test pin name determination with multiple duplicates."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        converter._pin_name_list = ["VCC", "VCC_1", "VCC_2"]
        
        mock_pin = MagicMock()
        mock_pin.name.text = "VCC"
        result = converter._determine_pin_name(mock_pin)
        
        assert result == "VCC_3"
        assert "VCC_3" in converter._pin_name_list


class TestBezierPointCalculation:
    """Tests for cubic Bezier point calculation."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_cubic_bezier_start_point(self, mock_importer_class):
        """Test Bezier point calculation at t=0 (start point)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        p0 = (0, 0)
        p1 = (10, 10)
        p2 = (20, 10)
        p3 = (30, 0)
        
        result = converter._cubic_bezier_point(p0, p1, p2, p3, 0.0)
        
        assert result == p0

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_cubic_bezier_end_point(self, mock_importer_class):
        """Test Bezier point calculation at t=1 (end point)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        p0 = (0, 0)
        p1 = (10, 10)
        p2 = (20, 10)
        p3 = (30, 0)
        
        result = converter._cubic_bezier_point(p0, p1, p2, p3, 1.0)
        
        assert result == p3

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_cubic_bezier_midpoint(self, mock_importer_class):
        """Test Bezier point calculation at t=0.5 (midpoint)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        p0 = (0, 0)
        p1 = (10, 10)
        p2 = (20, 10)
        p3 = (30, 0)
        
        result = converter._cubic_bezier_point(p0, p1, p2, p3, 0.5)
        
        # Should be approximately in the middle
        assert isinstance(result[0], float)
        assert isinstance(result[1], float)
        assert result[0] > 0
        assert result[0] < 30


class TestPinRotationMapping:
    """Tests for pin label rotation based on pin side."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_label_rotation_top_side(self, mock_importer_class):
        """Test label rotation for top side pins (270 degrees)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        result = converter._calc_lable_rotation_from_side(0)
        
        assert result == 3  # 270 degrees

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_label_rotation_bottom_side(self, mock_importer_class):
        """Test label rotation for bottom side pins (90 degrees)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        result = converter._calc_lable_rotation_from_side(1)
        
        assert result == 1  # 90 degrees

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_label_rotation_left_side(self, mock_importer_class):
        """Test label rotation for left side pins (0 degrees)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        result = converter._calc_lable_rotation_from_side(2)
        
        assert result == 0  # 0 degrees

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_label_rotation_right_side(self, mock_importer_class):
        """Test label rotation for right side pins (0 degrees)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        result = converter._calc_lable_rotation_from_side(3)
        
        assert result == 0  # 0 degrees


class TestPinSideRotation:
    """Tests for pin side rotation transformations."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_rotate_pin_side_no_rotation(self, mock_importer_class):
        """Test pin rotation with no side rotation (side 0)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        original = (1, 2, 3, 4)
        result = converter._rotate_pin_side(original, 0)
        
        assert result == original

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_rotate_pin_side_bottom(self, mock_importer_class):
        """Test pin side rotation for bottom (side 1)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        original = (1, 2, 3, 4)
        result = converter._rotate_pin_side(original, 1)
        
        assert result == (2, 1, 4, 3)

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_rotate_pin_side_left(self, mock_importer_class):
        """Test pin side rotation for left (side 2)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        original = (1, 2, 3, 4)
        result = converter._rotate_pin_side(original, 2)
        
        assert result == (3, 4, 1, 2)

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_rotate_pin_side_right(self, mock_importer_class):
        """Test pin side rotation for right (side 3)."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        original = (1, 2, 3, 4)
        result = converter._rotate_pin_side(original, 3)
        
        assert result == (4, 3, 2, 1)

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_rotate_pin_side_invalid(self, mock_importer_class):
        """Test that invalid side raises ValueError."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        with pytest.raises(ValueError, match="side must be 0, 1, 2 or 3"):
            converter._rotate_pin_side((1, 2, 3, 4), 5)


class TestMultiPartSymbols:
    """Tests for multi-part symbol handling."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_symbol_with_no_subparts(self, mock_importer_class):
        """Test conversion of symbol without subparts."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        
        mock_symbol = MagicMock()
        mock_symbol.info.name = "SIMPLE_SYMBOL"
        mock_symbol.info.prefix = "U"
        mock_symbol.info.mpn = "TEST_MPN"
        mock_symbol.info.manufacturer = "TEST_MFG"
        mock_symbol.subs = None
        mock_symbol.pins = []
        mock_importer.get_symbol.return_value = mock_symbol

        converter = EeSymbolToXpeditionSymbol({})
        result = converter.convert()

        assert result is not None

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    def test_symbol_with_multiple_subparts(self, mock_importer_class):
        """Test conversion of symbol with multiple subparts."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        
        mock_symbol = MagicMock()
        mock_symbol.info.name = "MULTI_PART_SYMBOL"
        mock_symbol.info.prefix = "U"
        mock_symbol.info.mpn = "TEST_MPN"
        mock_symbol.info.manufacturer = "TEST_MFG"
        mock_symbol.subs = [MagicMock(), MagicMock()]  # Two subparts
        mock_importer.get_symbol.return_value = mock_symbol

        converter = EeSymbolToXpeditionSymbol({})
        
        with patch.object(converter, 'convert_subpart'):
            result = converter.convert()
            
            assert result is not None


class TestFileOutput:
    """Tests for symbol file output."""

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_single_part_symbol(self, mock_file, mock_importer_class):
        """Test saving single-part symbol to file."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        converter.xpedition_symbol.name = "TEST"
        converter.xpedition_symbol.parts = {"TEST": MagicMock()}

        # Should not raise an error
        converter.save_to_file("test_symbol")

        mock_file.assert_called_once_with("test_symbol", "w")

    @patch('easyeda2xpedition.convert_symbol.EasyedaSymbolImporter')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_multi_part_symbol(self, mock_file, mock_importer_class):
        """Test saving multi-part symbol to separate files."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_symbol.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            subs=[],
            pins=[]
        )

        converter = EeSymbolToXpeditionSymbol({})
        
        # Add mock parts
        part1 = MagicMock()
        part1.name = "PART_1"
        part1.__str__ = MagicMock(return_value="PART_1_DATA")
        
        part2 = MagicMock()
        part2.name = "PART_2"
        part2.__str__ = MagicMock(return_value="PART_2_DATA")
        
        converter.xpedition_symbol.parts = {
            "symbol.1": part1,
            "symbol.2": part2
        }
        
        converter.save_to_file("test_symbol")
        
        # Should be called twice for two parts
        assert mock_file.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
