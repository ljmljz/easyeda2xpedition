"""Regression tests for symbol/footprint accuracy fixes."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch, mock_open

import pytest

from easyeda2xpedition.convert_footprint import FootprintConverter, sample_svg_arc
from easyeda2xpedition.convert_symbol import EeSymbolToXpeditionSymbol
from easyeda2xpedition.easyeda.parameters_easyeda import EeSymbolPinPath
from easyeda2xpedition.xpedition.footprint.pads import PolygonPad
from easyeda2xpedition.xpedition.symbol.symbol import SymbolPart, SymbolShapeArc, SymbolShapeCircle


def make_symbol_converter():
    symbol = SimpleNamespace(
        info=SimpleNamespace(name="TEST", prefix="U", mpn="MODEL", manufacturer="MFG"),
        subs=[],
        bbox=SimpleNamespace(x=100, y=200, width=100, height=100),
        pins=[],
        rectangles=[],
        circles=[],
        ellipses=[],
        polylines=[],
        lines=[],
        arcs=[],
    )
    with patch("easyeda2xpedition.convert_symbol.EasyedaSymbolImporter") as importer_cls:
        importer_cls.return_value.get_symbol.return_value = symbol
        converter = EeSymbolToXpeditionSymbol({})
    converter.xpedition_symbol.name = "TEST"
    converter.xpedition_symbol.refdes = "U"
    converter.xpedition_symbol.value = "MODEL"
    return converter


def make_footprint_converter(pads=None):
    footprint = SimpleNamespace(
        info=SimpleNamespace(name="FP"),
        bbox=SimpleNamespace(x=0, y=0, width=100, height=100),
        pads=pads or [],
        holes=[],
        rectangles=[],
        circles=[],
        arcs=[],
        tracks=[],
        solid_regions=[],
        copper_areas=[],
    )
    with patch("easyeda2xpedition.convert_footprint.easyeda_importer.EasyedaFootprintImporter") as importer_cls:
        importer_cls.return_value.get_footprint.return_value = footprint
        converter = FootprintConverter({})
    return converter


class TestPinPath:
    def test_vertical_path_is_not_rewritten(self):
        path = EeSymbolPinPath(path="M 10 20 v 30", color="#fff")
        assert "v" in path.path

    def test_horizontal_comma_path(self):
        converter = make_symbol_converter()
        pin = SimpleNamespace(
            pin_path=SimpleNamespace(path="M 10,20 h -30"),
            settings=SimpleNamespace(rotation=0),
        )
        (x2, y2, x1, y1), side = converter._calc_pin_position(pin)
        assert (x1, y1, x2, y2) == (10, 20, -20, 20)
        assert side == 3

    def test_vertical_path(self):
        converter = make_symbol_converter()
        pin = SimpleNamespace(
            pin_path=SimpleNamespace(path="M 10 20 v 30"),
            settings=SimpleNamespace(rotation=0),
        )
        (x2, y2, x1, y1), side = converter._calc_pin_position(pin)
        assert (x1, y1, x2, y2) == (10, 20, 10, 50)
        assert side == 0


class TestSymbolCoordinates:
    def test_symbol_coordinates_use_v50_units(self):
        converter = make_symbol_converter()
        bbox = SimpleNamespace(x=100, y=200)
        assert converter._x(110, bbox) == 10
        assert converter._y(150, bbox) == 50

    def test_ellipse_is_not_collapsed_to_circle(self):
        converter = make_symbol_converter()
        bbox = SimpleNamespace(x=100, y=200)
        ellipse = SimpleNamespace(center_x=100, center_y=200, radius_x=5, radius_y=10)

        converter._add_ellipse(ellipse, bbox)

        assert len(converter.xpedition_symbol.shapes) == 8
        assert all(isinstance(shape, SymbolShapeArc) for shape in converter.xpedition_symbol.shapes)
        xs = [p for shape in converter.xpedition_symbol.shapes for p in (shape.start_x, shape.mid_x, shape.end_x)]
        ys = [p for shape in converter.xpedition_symbol.shapes for p in (shape.start_y, shape.mid_y, shape.end_y)]
        assert min(xs) == pytest.approx(-5)
        assert max(xs) == pytest.approx(5)
        assert min(ys) == pytest.approx(-10)
        assert max(ys) == pytest.approx(10)

    def test_equal_radii_use_circle(self):
        converter = make_symbol_converter()
        bbox = SimpleNamespace(x=100, y=200)
        ellipse = SimpleNamespace(center_x=100, center_y=200, radius_x=7, radius_y=7)

        converter._add_ellipse(ellipse, bbox)

        assert len(converter.xpedition_symbol.shapes) == 1
        assert isinstance(converter.xpedition_symbol.shapes[0], SymbolShapeCircle)

    @patch("builtins.open", new_callable=mock_open)
    def test_text_positions_follow_bbox(self, mock_file):
        converter = make_symbol_converter()
        part = SymbolPart("TEST")
        part.set_bbox(0, 200, 100, 0)
        converter.xpedition_symbol.parts = {"TEST": part}

        converter.save_to_file("test_symbol")

        content = mock_file().write.call_args[0][0]
        assert "U 100 20 8 0 5 3 REFDES=U\n" in content
        assert "U 100 8 8 0 5 0 TYPE=Type?\n" in content
        assert "U 100 -120 8 0 5 0 VALUE=MODEL\n" in content

    @patch("builtins.open", new_callable=mock_open)
    def test_save_single_subpart_with_suffixed_name(self, mock_file):
        converter = make_symbol_converter()
        part = SymbolPart("TEST.1")
        part.set_bbox(0, 200, 100, 0)
        converter.xpedition_symbol.parts = {"TEST.1": part}

        converter.save_to_file("test_symbol")

        mock_file.assert_called_once_with("test_symbol", "w")


class TestFootprintShapes:
    def test_ellipse_points_are_centered(self):
        points = FootprintConverter._ellipse_points(10, 20, 4)
        assert len(points) == 4
        assert min(x for x, _ in points) == pytest.approx(-5)
        assert max(x for x, _ in points) == pytest.approx(5)
        assert min(y for _, y in points) == pytest.approx(-10)
        assert max(y for _, y in points) == pytest.approx(10)

    def test_polygon_pad_points_are_relative_to_pad_center(self):
        pad = SimpleNamespace(
            shape="POLYGON", center_x=100, center_y=50, width=20, height=20,
            layer_id=1, net="", number="1", hole_radius=0,
            points="90 40 110 40 110 60 90 60", rotation=0, id="x",
            hole_length=0, hole_point="", is_plated=True, is_locked=False,
        )
        converter = make_footprint_converter([pad])

        converter._convert_easyeda_padstack_to_xpedition()

        polygon = next(
            pad for name, pad in converter._pads.items()
            if name.startswith("POLYGON_") and not name.endswith("L")
        )
        assert isinstance(polygon, PolygonPad)
        assert polygon.points == [(-100.0, 100.0), (100.0, 100.0), (100.0, -100.0), (-100.0, -100.0)]

    def test_ellipse_pad_uses_polygon_not_oblong(self):
        pad = SimpleNamespace(
            shape="ELLIPSE", center_x=0, center_y=0, width=10, height=20,
            layer_id=1, net="", number="1", hole_radius=0, points="", rotation=0,
            id="x", hole_length=0, hole_point="", is_plated=True, is_locked=False,
        )
        converter = make_footprint_converter([pad])

        converter._convert_easyeda_padstack_to_xpedition()

        ellipse_pad = next(
            pad for name, pad in converter._pads.items()
            if name.startswith("ELLIPSE_") and not name.endswith("L")
        )
        assert isinstance(ellipse_pad, PolygonPad)
        assert len(ellipse_pad.points) == 32

    def test_footprint_arc_is_sampled(self):
        converter = make_footprint_converter()
        points = converter._sample_arc(
            "M 160.83 -362.51 A 1.1811 1.1811 0 1 0 160.85 -362.51"
        )
        assert len(points) == 25
        assert points[0][0] == pytest.approx(points[-1][0], abs=1.0)
        assert points[0][1] == pytest.approx(points[-1][1], abs=1.0)

    def test_sample_svg_arc_returns_endpoints(self):
        points = sample_svg_arc(0, 0, 10, 10, 0, 0, 1, 20, 0, 8)
        assert points[0] == pytest.approx((0, 0))
        assert points[-1] == pytest.approx((20, 0), abs=1e-6)

class TestPadstackMaskAndPaste:
    @staticmethod
    def _pad_extents(pad):
        if hasattr(pad, "diameter"):
            return pad.diameter, pad.diameter
        if isinstance(pad, PolygonPad):
            xs = [point[0] for point in pad.points]
            ys = [point[1] for point in pad.points]
            return max(xs) - min(xs), max(ys) - min(ys)
        return pad.width, pad.height

    @pytest.mark.parametrize(
        "shape,width,height,points",
        [
            ("RECT", 10, 20, ""),
            ("ROUND", 10, 10, ""),
            ("OVAL", 10, 20, ""),
            ("ELLIPSE", 10, 20, ""),
            ("POLYGON", 20, 20, "90 40 110 40 110 60 90 60"),
        ],
    )
    def test_smd_soldermask_is_larger_and_paste_is_not_larger(self, shape, width, height, points):
        pad = SimpleNamespace(
            shape=shape, center_x=100, center_y=50, width=width, height=height,
            layer_id=1, net="", number="1", hole_radius=0, points=points,
            rotation=0, id="x", hole_length=0, hole_point="",
            is_plated=True, is_locked=False,
        )
        converter = make_footprint_converter([pad])

        converter._convert_easyeda_padstack_to_xpedition()

        padstack = next(iter(converter._padstacks.values()))
        body = self._pad_extents(padstack.pads.top_pad)
        soldermask = self._pad_extents(padstack.pads.top_soldermask_pad)
        solderpaste = self._pad_extents(padstack.pads.top_solderpaste_pad)

        assert soldermask[0] == pytest.approx(body[0] + 8)
        assert soldermask[1] == pytest.approx(body[1] + 8)
        assert solderpaste[0] <= body[0] + 1e-6
        assert solderpaste[1] <= body[1] + 1e-6

    def test_through_hole_has_no_solderpaste(self):
        pad = SimpleNamespace(
            shape="ROUND", center_x=100, center_y=50, width=20, height=20,
            layer_id=1, net="", number="1", hole_radius=1, points="",
            rotation=0, id="x", hole_length=0, hole_point="",
            is_plated=True, is_locked=False,
        )
        converter = make_footprint_converter([pad])

        converter._convert_easyeda_padstack_to_xpedition()

        padstack = next(iter(converter._padstacks.values()))
        assert padstack.pads.top_solderpaste_pad is None
        assert padstack.pads.top_soldermask_pad is not None
