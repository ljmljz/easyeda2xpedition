"""
Unit tests for EasyEDA to Xpedition footprint conversion.

This module contains tests for the FootprintConverter class, covering:
- Unit conversions (EasyEDA to Xpedition)
- Pad shape conversions
- Padstack generation
- Layer mapping
- Coordinate transformations
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from easyeda2xpedition.convert_footprint import (
    FootprintConverter,
    ee_unit_to_th,
    apply_vertical_mirror
)


class TestUnitConversion:
    """Tests for unit conversion utilities."""

    def test_ee_unit_to_th_basic_conversion(self):
        """Test basic EasyEDA unit to thousandths conversion."""
        # 1 EasyEDA unit = 10 thousandths
        assert ee_unit_to_th(1.0) == 10.0
        assert ee_unit_to_th(2.5) == 25.0
        assert ee_unit_to_th(10.0) == 100.0

    def test_ee_unit_to_th_zero_value(self):
        """Test conversion of zero value."""
        assert ee_unit_to_th(0.0) == 0.0

    def test_ee_unit_to_th_negative_values(self):
        """Test conversion of negative values."""
        assert ee_unit_to_th(-1.0) == -10.0
        assert ee_unit_to_th(-5.5) == -55.0

    def test_ee_unit_to_th_rounding(self):
        """Test that conversion rounds to 2 decimal places."""
        result = ee_unit_to_th(3.14159)
        assert result == round(31.4159, 2)
        assert isinstance(result, float)


class TestVerticalMirror:
    """Tests for vertical mirror transformation."""

    def test_apply_vertical_mirror_origin(self):
        """Test mirroring at origin."""
        result = apply_vertical_mirror(0.0, 100.0)
        assert result == 0.0

    def test_apply_vertical_mirror_positive_value(self):
        """Test mirroring of positive Y coordinate."""
        result = apply_vertical_mirror(50.0, 100.0)
        assert result == -50.0

    def test_apply_vertical_mirror_negative_value(self):
        """Test mirroring of negative Y coordinate."""
        result = apply_vertical_mirror(-50.0, 100.0)
        assert result == 50.0

    def test_apply_vertical_mirror_bbox_height_parameter(self):
        """Test that bbox_height parameter is handled correctly."""
        # The function applies mirroring regardless of bbox_height
        result1 = apply_vertical_mirror(25.0, 100.0)
        result2 = apply_vertical_mirror(25.0, 200.0)
        # The bbox_height doesn't affect the direct mirror operation
        assert result1 == -25.0
        assert result2 == -25.0


class TestFootprintConverterInitialization:
    """Tests for FootprintConverter initialization."""

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    def test_converter_initialization(self, mock_importer_class):
        """Test FootprintConverter initialization with mock data."""
        # Setup mock
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        
        mock_footprint = MagicMock()
        mock_footprint.info.name = "TEST_FOOTPRINT"
        mock_footprint.bbox.x = 0.0
        mock_footprint.bbox.y = 0.0
        mock_footprint.bbox.width = 100.0
        mock_footprint.bbox.height = 100.0
        mock_importer.get_footprint.return_value = mock_footprint

        # Create converter
        cad_data = {"cad": {"meta": {"name": "TEST"}}}
        converter = FootprintConverter(cad_data, output_folder="./test_output")

        # Verify initialization
        assert converter._easyeda_cp_cad_data == cad_data
        assert converter._target_folder == "./test_output"
        assert converter._cell.name == "TEST_FOOTPRINT"
        assert converter._bbox is not None

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    def test_converter_no_output_folder(self, mock_importer_class):
        """Test FootprintConverter with no output folder specified."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_footprint.return_value = MagicMock()

        cad_data = {"cad": {"meta": {"name": "TEST"}}}
        converter = FootprintConverter(cad_data)  # No output_folder specified

        assert converter._target_folder is None


class TestLayerMapping:
    """Tests for EasyEDA to Xpedition layer mapping."""

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    def test_layer_mapping(self, mock_importer_class):
        """Test that EasyEDA layers are correctly mapped to Xpedition layers."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_footprint.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            bbox=MagicMock(x=0, y=0, width=100, height=100)
        )

        cad_data = {}
        converter = FootprintConverter(cad_data)

        # Test layer mappings
        test_cases = [
            ("TopLayer", "TOP"),
            ("BottomLayer", "BOTTOM"),
            ("TopSilkLayer", "SILKSCREEN_OUTLINE"),
            ("BottomSilkLayer", "SILKSCREEN_OUTLINE"),
            ("TopPasteMaskLayer", "SOLDER_PASTE"),
            ("BottomPasteMaskLayer", "SOLDER_PASTE"),
            ("TopSolderMaskLayer", "SOLDER_MASK"),
            ("BottomSolderMaskLayer", "SOLDER_MASK"),
            ("Multi-Layer", "MULTI_LAYER"),
            ("TopAssembly", "ASSEMBLY_OUTLINE"),
            ("BottomAssembly", "ASSEMBLY_OUTLINE"),
            ("ComponentShapeLayer", "ASSEMBLY_OUTLINE"),
        ]

        for easyeda_layer, expected_xpedition in test_cases:
            result = converter._map_easyeda_layer_to_xpedition(easyeda_layer)
            assert result == expected_xpedition, \
                f"Layer '{easyeda_layer}' should map to '{expected_xpedition}', got '{result}'"

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    def test_unknown_layer_mapping(self, mock_importer_class):
        """Test that unknown layers are mapped with a prefix."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_footprint.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            bbox=MagicMock(x=0, y=0, width=100, height=100)
        )

        cad_data = {}
        converter = FootprintConverter(cad_data)

        result = converter._map_easyeda_layer_to_xpedition("UnknownLayer")
        assert result.startswith("UNKNOWN_LAYER_")
        assert "UnknownLayer" in result


class TestRectanglePadConversion:
    """Tests for rectangle pad conversion."""

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    def test_rectangle_pad_properties(self, mock_importer_class):
        """Test that rectangle pads are correctly converted with proper dimensions."""
        from easyeda2xpedition.xpedition.footprint.pads import RectanglePad

        # Rectangle pad dimensions
        width_ee = 50.0
        height_ee = 30.0
        width_th = ee_unit_to_th(width_ee)
        height_th = ee_unit_to_th(height_ee)

        pad = RectanglePad(name="rect_test", width=width_th, height=height_th)
        
        # Verify pad properties
        assert pad.name == "rect_test"
        assert pad.width == width_th
        assert pad.height == height_th


class TestRoundPadConversion:
    """Tests for round pad conversion."""

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    def test_round_pad_diameter(self, mock_importer_class):
        """Test that round pads are correctly converted with proper diameter."""
        from easyeda2xpedition.xpedition.footprint.pads import RoundPad

        diameter_ee = 40.0
        diameter_th = ee_unit_to_th(diameter_ee)

        pad = RoundPad(name="round_test", diameter=diameter_th)
        
        assert pad.name == "round_test"
        assert pad.diameter == diameter_th


class TestOblongPadConversion:
    """Tests for oblong/oval pad conversion."""

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    def test_oblong_pad_properties(self, mock_importer_class):
        """Test that oblong pads are correctly converted."""
        from easyeda2xpedition.xpedition.footprint.pads import OblongPad

        width_th = ee_unit_to_th(60.0)
        height_th = ee_unit_to_th(30.0)

        pad = OblongPad(name="oblong_test", width=width_th, height=height_th)
        
        assert pad.name == "oblong_test"
        assert pad.width == width_th
        assert pad.height == height_th


class TestPadStackGeneration:
    """Tests for padstack generation."""

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    def test_smd_padstack_creation(self, mock_importer_class):
        """Test that SMD padstacks are correctly created."""
        from easyeda2xpedition.xpedition.footprint.padstacks import PinSMDPadStack
        from easyeda2xpedition.xpedition.footprint.pads import RectanglePad

        padstack = PinSMDPadStack(name="test_smd")
        pad = RectanglePad(name="pad_test", width=50.0, height=50.0)

        padstack.set_pads(
            top_pad=pad,
            bottom_pad=pad,
            top_solderpaste_pad=pad,
            bottom_solderpaste_pad=pad,
            top_soldermask_pad=pad,
            bottom_soldermask_pad=pad
        )

        assert padstack.name == "test_smd"

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    def test_through_hole_padstack_creation(self, mock_importer_class):
        """Test that through-hole padstacks are correctly created."""
        from easyeda2xpedition.xpedition.footprint.padstacks import PinThroughPadStack
        from easyeda2xpedition.xpedition.footprint.pads import RectanglePad, RoundPad
        from easyeda2xpedition.xpedition.footprint.holes import RoundHole

        padstack = PinThroughPadStack(name="test_th")
        pad = RectanglePad(name="pad_test", width=50.0, height=50.0)
        hole = RoundHole(name="hole_test", diameter=20.0, plated=True)

        padstack.set_pads(
            top_pad=pad,
            bottom_pad=pad,
            internal_pad=pad,
            top_soldermask_pad=pad,
            bottom_soldermask_pad=pad,
            hole=hole
        )

        assert padstack.name == "test_th"


class TestMountTypeDetection:
    """Tests for automatic mount type detection."""

    def test_mount_type_detection_logic(self):
        """Test the logic for detecting mount type from padstacks."""
        # Test SMD only
        smd_padstacks = {
            "pad1_SMD": MagicMock(),
            "pad2_SMD": MagicMock(),
        }
        is_all_smd = all("SMD" in key for key in smd_padstacks.keys())
        assert is_all_smd is True

        # Test through-hole only
        th_padstacks = {
            "pad1_TH": MagicMock(),
            "pad2_TH": MagicMock(),
        }
        is_all_th = all("TH" in key for key in th_padstacks.keys())
        assert is_all_th is True

        # Test mixed
        mixed_padstacks = {
            "pad1_SMD": MagicMock(),
            "pad2_TH": MagicMock(),
        }
        is_all_smd = all("SMD" in key for key in mixed_padstacks.keys())
        is_all_th = all("TH" in key for key in mixed_padstacks.keys())
        assert is_all_smd is False
        assert is_all_th is False


class TestCoordinateTransformation:
    """Tests for coordinate transformation and normalization."""

    def test_coordinate_normalization(self):
        """Test that coordinates are properly normalized using bounding box."""
        bbox_x = 10.0
        bbox_y = 20.0
        
        pad_x = 50.0
        pad_y = 60.0

        # Normalize to bbox origin
        normalized_x = pad_x - bbox_x
        normalized_y = pad_y - bbox_y

        assert normalized_x == 40.0
        assert normalized_y == 40.0

    def test_coordinate_transformation_with_mirror(self):
        """Test coordinate transformation with vertical mirroring."""
        bbox_height = 100.0
        normalized_y = 50.0

        # Apply mirror
        mirrored_y = apply_vertical_mirror(normalized_y, bbox_height)

        assert mirrored_y == -50.0


class TestPolygonPadConversion:
    """Tests for polygon pad conversion."""

    def test_polygon_point_parsing(self):
        """Test parsing of polygon points from string format."""
        point_string = "0 0 100 0 100 100 0 100"
        pts = [float(v) for v in point_string.replace(",", " ").split()]
        
        points = []
        for i in range(0, len(pts), 2):
            px = ee_unit_to_th(pts[i])
            py = ee_unit_to_th(pts[i + 1])
            points.append((px, py))

        assert len(points) == 4
        assert points[0] == (0.0, 0.0)
        assert points[1] == (1000.0, 0.0)
        assert points[2] == (1000.0, 1000.0)
        assert points[3] == (0.0, 1000.0)


class TestFileOutput:
    """Tests for file output operations."""

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    @patch('builtins.open', create=True)
    def test_save_padstacks_file_header(self, mock_open, mock_importer_class):
        """Test that padstacks file is created with correct header."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_footprint.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            bbox=MagicMock(x=0, y=0, width=100, height=100),
            pads=[],
            holes=[],
            rectangles=[],
            circles=[],
            arcs=[],
            tracks=[],
            solid_regions=[],
            copper_areas=[]
        )

        converter = FootprintConverter({})
        
        # Mock the file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        converter.save_padstacks_to_file("test_pads.hkp")

        # Verify file was opened
        mock_open.assert_called_once_with("test_pads.hkp", 'w')

    @patch('easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter')
    @patch('builtins.open', create=True)
    def test_save_cell_file_header(self, mock_open, mock_importer_class):
        """Test that cell file is created with correct header."""
        mock_importer = MagicMock()
        mock_importer_class.return_value = mock_importer
        mock_importer.get_footprint.return_value = MagicMock(
            info=MagicMock(name="TEST"),
            bbox=MagicMock(x=0, y=0, width=100, height=100),
            pads=[],
            holes=[],
            rectangles=[],
            circles=[],
            arcs=[],
            tracks=[],
            solid_regions=[],
            copper_areas=[]
        )

        converter = FootprintConverter({})
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        converter.save_cell_to_file("test_cell.hkp")

        # Verify file was opened
        mock_open.assert_called_once_with("test_cell.hkp", 'w')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
