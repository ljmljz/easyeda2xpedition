import re

class HKPParser:
    def __init__(self):
        self.data = {}

    def parse(self, filepath):
        with open(filepath, 'r') as file:
            lines = file.readlines()
        self.data = self._parse_lines(lines)
        return self.data

    def _parse_lines(self, lines, start=0, end=None, level=0):
        if end is None:
            end = len(lines)
        result = {}
        i = start
        while i < end:
            line = lines[i].strip()
            if not line or line.startswith('#'):  # Skip empty lines and comments
                i += 1
                continue
            indent_level = self._get_indent_level(line)
            if indent_level > level:  # Nested structure
                key = line.strip('.').split(' ')[0]
                nested_end = self._find_next_level(lines, i + 1, end, level)
                result[key] = self._parse_lines(lines, i + 1, nested_end, indent_level)
                i = nested_end
            elif indent_level == level:  # Key-value pair or standalone key
                if ' ' in line:
                    key, value = map(str.strip, line.split(' ', 1))
                    result[key.strip('.')] = self._parse_value(value)
                else:
                    result[line.strip('.')] = {}
                i += 1
            else:  # End of current level
                break
        return result

    def _find_next_level(self, lines, start, end, level):
        for i in range(start, end):
            if self._get_indent_level(lines[i].strip()) <= level:
                return i
        return end

    def _get_indent_level(self, line):
        return len(line) - len(line.lstrip('.'))

    def _parse_value(self, value):
        # Handle different value types (e.g., strings, arrays, numbers)
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]  # String
        elif ',' in value:
            return [self._parse_value(v.strip()) for v in value.split(',')]  # Array
        try:
            return int(value)  # Integer
        except ValueError:
            try:
                return float(value)  # Float
            except ValueError:
                return value  # Fallback to string

# Example usage:
# parser = HKPParser()
# parts_data = parser.parse('XpeditionDesigner/_Parts.hkp')
# pads_data = parser.parse('XpeditionDesigner/_Pads.hkp')
# cells_data = parser.parse('XpeditionDesigner/_Cells.hkp')
# print(parts_data)
# print(pads_data)
# print(cells_data)
