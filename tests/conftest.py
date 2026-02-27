"""
Shared test configuration and fixtures for EasyEDA2Xpedition tests.
"""

import pytest
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class MockBBox:
    """Mock bounding box object."""
    x: float = 0.0
    y: float = 0.0
    width: float = 100.0
    height: float = 100.0


@dataclass
class MockPin:
    """Mock pad/pin object for testing."""
    number: str = "1"
    shape: str = "RECT"
    width: float = 50.0
    height: float = 50.0
    center_x: float = 50.0
    center_y: float = 50.0
    rotation: int = 0
    hole_radius: float = 0.0
    is_plated: bool = True


@dataclass
class MockCircle:
    """Mock circle object for testing."""
    layer_id: int = 1
    cx: float = 50.0
    cy: float = 50.0
    radius: float = 25.0
    stroke_width: float = 1.0


@dataclass
class MockLayer:
    """Mock layer object."""
    layer_id: int = 1
    layer_name: str = "TopLayer"


@dataclass
class MockFootprintInfo:
    """Mock footprint info object."""
    name: str = "TEST_FOOTPRINT"
    layers: list = None

    def __post_init__(self):
        if self.layers is None:
            self.layers = [MockLayer()]


@dataclass
class MockSymbolInfo:
    """Mock symbol info object."""
    name: str = "TEST_SYMBOL"
    prefix: str = "U"
    mpn: str = "TEST_MPN"
    manufacturer: str = "TEST_MFG"


@pytest.fixture
def mock_footprint_cad_data() -> Dict[str, Any]:
    """
    Provide mock EasyEDA footprint CAD data for testing.
    Returns a dictionary simulating EasyEDA API response.
    """
    return {
        "cad": {
            "meta": {
                "name": "C165948"
            },
            "canvas": {
                "height": 200,
                "width": 200
            }
        }
    }


@pytest.fixture
def mock_symbol_cad_data() -> Dict[str, Any]:
    """
    Provide mock EasyEDA symbol CAD data for testing.
    Returns a dictionary simulating EasyEDA API response.
    """
    return {
        "cad": {
            "meta": {
                "name": "TEST_SYMBOL",
                "prefix": "U",
                "mfg": "TEST_MFG",
                "mpn": "TEST_MPN"
            }
        }
    }


@pytest.fixture
def mock_pad():
    """Provide a mock pad object."""
    return MockPin(
        number="1",
        shape="RECT",
        width=50.0,
        height=50.0,
        center_x=50.0,
        center_y=50.0
    )


@pytest.fixture
def mock_round_pad():
    """Provide a mock round pad object."""
    return MockPin(
        number="2",
        shape="ROUND",
        width=40.0,
        height=40.0,
        center_x=100.0,
        center_y=50.0
    )


@pytest.fixture
def mock_oval_pad():
    """Provide a mock oval/oblong pad object."""
    return MockPin(
        number="3",
        shape="OVAL",
        width=60.0,
        height=30.0,
        center_x=150.0,
        center_y=50.0
    )


@pytest.fixture
def mock_through_hole_pad():
    """Provide a mock through-hole pad object."""
    return MockPin(
        number="4",
        shape="ROUND",
        width=60.0,
        height=60.0,
        center_x=50.0,
        center_y=100.0,
        hole_radius=15.0,
        is_plated=True
    )


@pytest.fixture
def sample_layer_id_to_name_map() -> Dict[int, str]:
    """Provide a sample mapping of layer IDs to layer names."""
    return {
        1: "TopLayer",
        2: "BottomLayer",
        11: "TopSilkLayer",
        12: "BottomSilkLayer",
        21: "TopSolderMaskLayer",
        22: "BottomSolderMaskLayer",
        31: "TopPasteMaskLayer",
        32: "BottomPasteMaskLayer",
        51: "TopAssembly",
        52: "BottomAssembly",
    }


@pytest.fixture
def expected_layer_map() -> Dict[str, str]:
    """Provide expected EasyEDA to Xpedition layer mapping."""
    return {
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


@pytest.fixture
def bbox() -> MockBBox:
    """Provide a mock bounding box."""
    return MockBBox(x=0.0, y=0.0, width=200.0, height=200.0)
