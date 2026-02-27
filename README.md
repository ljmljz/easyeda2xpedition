# EasyEDA2Xpedition

This project is inspired by [EasyEDA2KiCAD.py](https://github.com/uPesy/easyeda2kicad.py)  
It aims to convert EasyEDA Symbol/Footprint to Mentor Graphics Xpedition Symbol/Footprint files.

## Overview

EasyEDA2Xpedition is a Python tool that converts PCB designs and components from EasyEDA format to Mentor Graphics Xpedition format. It supports both footprint and symbol conversions, enabling workflows that transition from EasyEDA to Xpedition-based PCB design.

## Features

- **Footprint Conversion**: Converts EasyEDA footprints to Xpedition Cell and Padstack formats (.hkp)
- **Symbol Conversion**: Converts EasyEDA schematic symbols to Xpedition symbol format
- **Component Data Retrieval**: Integrates with LCSC database via EasyEDA API
- **Support for Multiple Pad Types**: Handles RECT, ROUND, OVAL, ELLIPSE, and POLYGON pads
- **Layer Mapping**: Automatically maps EasyEDA layers to Xpedition layers (silkscreen, solder mask, paste, assembly)
- **Coordinate Transformation**: Applies proper coordinate system transformations between formats

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd easyeda2xpedition
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # On Windows
   # or
   source .venv/bin/activate  # On Linux/macOS
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) For development and testing, install additional dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Development

### Setting Up for Development

For development work, it's recommended to install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

This includes pytest for testing, code formatting tools, and linters.

## Usage

### Footprint Conversion

To convert an EasyEDA footprint to Xpedition format:

```python
from easyeda2xpedition.convert_footprint import FootprintConverter
from easyeda2xpedition.easyeda.easyeda_api import EasyedaApi

# Retrieve component data from LCSC
api = EasyedaApi()
easyeda_data = api.get_cad_data_of_component(lcsc_id="C165948")

# Convert to Xpedition format
converter = FootprintConverter(easyeda_data, output_folder="./output")
converter.convert()

# Save output files
converter.save_padstacks_to_file("./output/_Pads.hkp")
converter.save_cell_to_file("./output/_Cell.hkp")
```

### Symbol Conversion

To convert an EasyEDA symbol to Xpedition format:

```python
from easyeda2xpedition.convert_symbol import EeSymbolToXpeditionSymbol
from easyeda2xpedition.easyeda.easyeda_api import EasyedaApi

# Retrieve component data from LCSC
api = EasyedaApi()
easyeda_data = api.get_cad_data_of_component(lcsc_id="C165948")

# Convert to Xpedition format
converter = EeSymbolToXpeditionSymbol(easyeda_data)
xpedition_symbol = converter.convert()
```

## Project Structure

```
easyeda2xpedition/
├── convert_footprint.py          # Footprint conversion logic
├── convert_symbol.py             # Symbol conversion logic
├── easyeda/
│   ├── easyeda_api.py           # API client for EasyEDA/LCSC
│   ├── easyeda_importer.py      # Data parsing and importing
│   ├── parameters_easyeda.py    # Data models for EasyEDA
│   └── svg_path_parser.py       # SVG path parsing utilities
├── xpedition/
│   ├── footprint/
│   │   ├── pads/                # Pad definitions (Rectangle, Round, Oblong, etc.)
│   │   ├── padstacks/           # Padstack configurations (SMD, Through-hole)
│   │   ├── holes/               # Hole definitions
│   │   ├── shapes/              # Shape definitions for polygons and paths
│   │   └── cell.py              # Cell and pin definitions
│   └── symbol/
│       ├── pin.py               # Symbol pin definitions
│       └── symbol.py            # Symbol structure
└── viewer/                       # Visualization utilities
```

## File Formats

### EasyEDA File Format

This document describes the EasyEDA PCB file format used by EasyEDA for PCB design. The format is primarily used for storing PCB design data in an ASCII format: [EasyEDA PCB File Format](https://docs.easyeda.com/en/DocumentFormat/3-EasyEDA-PCB-File-Format/)

### Xpedition File Format (.hkp)

Only focus on the ascii format file.

#### Pads.hkp File Format

Pads.hkp file format description: [PadsHKP.md](PadsHKP.md)

#### Cells.hkp File Format

Cells.hkp file format description: [CellsHKP.md](CellsHKP.md)

#### Parts.hkp File Format

Parts.hkp file format description: [PartsHKP.md](PartsHKP.md)

## Testing

Run the test suite to verify conversion functionality:

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest -v tests/

# Run specific test file
pytest tests/test_convert_footprint.py
pytest tests/test_convert_symbol.py

# Run with coverage report
pytest --cov=easyeda2xpedition tests/
```

## Development

### Running Tests During Development

The project includes comprehensive tests for footprint and symbol conversion:

- `tests/test_convert_footprint.py` - Footprint conversion tests
- `tests/test_convert_symbol.py` - Symbol conversion tests
- `tests/conftest.py` - Shared test fixtures and utilities

Tests cover:
- Unit conversion (EasyEDA units to Xpedition thousandths)
- Pad shape conversions
- Padstack generation
- Layer mapping
- Coordinate transformations
- Pin conversions
