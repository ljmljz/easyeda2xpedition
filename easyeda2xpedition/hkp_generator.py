class HKPGenerator:
    def __init__(self):
        pass

    def generate(self, data, filepath):
        """Generate an HKP file from structured data."""
        with open(filepath, 'w') as file:
            self._write_data(data, file)

    def _write_data(self, data, file, level=0):
        """Recursively write data to the file."""
        indent = '.' * level
        for key, value in data.items():
            if isinstance(value, dict):  # Nested structure
                # file.write(f"{indent}{key.upper()}\n")
                self._write_data(value, file, level + 1)
            elif isinstance(value, list):  # List of values
                for item in value:
                    if item is None:
                        file.write(f"{indent}{key.upper()}\n")
                    else:
                        file.write(f"{indent}{key.upper()} {self._format_value(item)}\n")
            else:  # Single key-value pair
                if value is None:
                    file.write(f"{indent}{key.upper()}\n")
                else:
                    file.write(f"{indent}{key} {self._format_value(value)}\n")

    def _format_value(self, value):
        """Format a value for HKP output."""
        if isinstance(value, str):
            return f'"{value}"' if ' ' in value or value == '' else value
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            raise ValueError(f"Unsupported value type: {type(value)}")

# Example usage:
# generator = HKPGenerator()
# data = {
#     "FileType": "ASCII_PDB",
#     "Version": "1",
#     "Units": "th",
#     "Number": {
#         "LTC1760IFW-PBF": {
#             "Name": "LTC1760IFW-PBF",
#             "RefPrefix": "U",
#             "Prop": [
#                 {"Type": "IC", "Text": "Text"},
#                 {"Mfr_Name": "Analog Devices Inc", "Text": "Text"}
#             ]
#         }
#     }
# }
# generator.generate(data, 'output.hkp')
