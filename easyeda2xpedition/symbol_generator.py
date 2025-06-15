class SymbolGenerator:
    def __init__(self):
        pass

    def generate(self, data, filepath):
        """Generate an xDX Designer Symbol file from structured data."""
        with open(filepath, 'w') as file:
            self._write_data(data, file)

    def _write_data(self, data, file):
        """Recursively write data to the file."""
        for key, value in data.items():
            if isinstance(value, dict):  # Nested structure
                file.write(f"{key}\n")
                self._write_data(value, file)
            elif isinstance(value, list):  # List of values
                for item in value:
                    file.write(f"{key} {self._format_value(item)}\n")
            else:  # Single key-value pair
                file.write(f"{key} {self._format_value(value)}\n")

    def _format_value(self, value):
        """Format a value for xDX Designer Symbol output."""
        if isinstance(value, str):
            return f'"{value}"' if ' ' in value or value == '' else value
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

# Example usage:
# generator = SymbolGenerator()
# data = {
#     "V": 50,
#     "K": "403164167500 LTC1760IFW-PBF",
#     "Y": 1,
#     "D": "0 -250 280 20",
#     "Z": 0,
#     "i": 0,
#     "U": [
#         "0 0 10 0 5 0 DEVICE=LTC1760IFW-PBF",
#         "0 0 5 0 5 0 Copyright=Copyright (C) 2025 Ultra Librarian.",
#         "0 0 5 0 5 0 Mfr_Name=Analog Devices Inc"
#     ],
#     "P": [
#         {"1": "0 0 30 0 0 2 0"},
#         {"2": "0 -10 30 -10 0 2 0"}
#     ],
#     "L": [
#         {"31": "0 8 0 2 0 1 0 VPLUS"},
#         {"31": "-10 8 0 2 0 1 0 BAT2"}
#     ]
# }
# generator.generate(data, 'output.sym')
