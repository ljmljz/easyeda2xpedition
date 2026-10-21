from datetime import datetime


def quote(value) -> str:
    text = str(value)
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    return f'"{text}"'


class PartPin(object):
    def __init__(self, name: str, number: str, pin_type: str = "Bidir"):
        self.name = name or number
        self.number = number
        self.pin_type = pin_type or "Bidir"


class PartGate(object):
    def __init__(self, name: str, pins=None):
        self.name = name
        self.pins = list(pins or [])


class Part(object):
    def __init__(
        self,
        number: str,
        name: str,
        label: str = "",
        description: str = "",
        ref_prefix: str = "",
        top_cell: str = "",
        bottom_cell: str = "",
        symbol_ref: str = "",
        properties=None,
        gates=None,
        modified: datetime = None,
    ):
        self.number = number
        self.name = name
        self.label = label or name
        self.description = description
        self.ref_prefix = ref_prefix
        self.top_cell = top_cell
        self.bottom_cell = bottom_cell
        self.symbol_ref = symbol_ref
        self.properties = list(properties or [])
        self.gates = list(gates or [])
        self.modified = modified

    def add_gate(self, gate: PartGate):
        self.gates.append(gate)

    def add_property(self, name: str, value: str, value_type: str = "Text"):
        self.properties.append((name, value, value_type))

    def _swap_id(self, index: int) -> str:
        return f"P{index}"

    def to_lines(self):
        lines = [f".Number {quote(self.number)}"]
        lines.append(f"\t..Name {quote(self.name)}")
        lines.append("\t\t...Default")
        lines.append(f"\t..Label {quote(self.label)}")
        lines.append("\t\t...Default")
        if self.description:
            lines.append(f"\t..Desc {quote(self.description)}")
        if self.ref_prefix:
            lines.append(f"\t..RefPrefix {quote(self.ref_prefix)}")
        lines.append(f"\t..TopCell {quote(self.top_cell)}")
        lines.append(f"\t..BottomCell {quote(self.bottom_cell)}")
        if self.modified is not None:
            timestamp = int(self.modified.timestamp())
            stamp = self.modified.strftime("%Y/%m/%d %H:%M")
            lines.append(f"\t..Modified\t{timestamp} ! {stamp}")
        for name, value, value_type in self.properties:
            prop_name = quote(name)
            prop_value = quote(value)
            prop_type = quote(value_type)
            lines.append(f"\t..Prop {prop_name},\t{prop_value},\t{prop_type}")

        for gate in self.gates:
            lines.append(f"\t..SwapGroup\t{quote(gate.name)}")
            for index, _ in enumerate(gate.pins):
                lines.append(f"\t\t...SwapID\t{quote(self._swap_id(index))}")
            for index, pin in enumerate(gate.pins):
                lines.append(
                    f"\t\t...SwapIDProperties\t{quote(self._swap_id(index))}"
                )
                lines.append(
                    f"\t\t\t....Prop {quote('Pin Type')},\t"
                    f"{quote(pin.pin_type)},\t{quote('Text')}"
                )

        if self.symbol_ref:
            lines.append(f"\t..Symbol\t{quote(self.symbol_ref)}")
            lines.append("\t\t...Default")
            for gate in self.gates:
                lines.append(f"\t\t...Symbol_SwapGroup\t{quote(gate.name)}")
                for pin in gate.pins:
                    lines.append(f"\t\t\t....PinName\t{quote(pin.name)}")

        if self.gates:
            lines.append("\t..Slots")
            for slot_id, gate in enumerate(self.gates, start=1):
                lines.append(f"\t\t...Slot_SwapGroup\t{quote(gate.name)}")
                lines.append(f"\t\t\t....SlotID\t{slot_id}")
                lines.append("\t\t\t....SwapCode\t0")
                for pin in gate.pins:
                    lines.append(f"\t\t\t....PinNumber\t{quote(pin.number)}")

        return lines

    def __str__(self):
        return "\n".join(self.to_lines()) + "\n"


class PartsLibrary(object):
    def __init__(self, parts=None):
        self.parts = list(parts or [])

    def add_part(self, part: Part):
        self.parts.append(part)

    def __str__(self):
        lines = [
            "!.LCID 2052",
            ".Filetype ASCII_PDB",
            '.Version "02.01"',
            '.LIBRARY_DB_TYPE "Enterprise"',
            ".Units mm",
            ".Notation Si",
            "",
        ]
        for part in self.parts:
            lines.extend(part.to_lines())
            lines.append("")
        return "\n".join(lines) + "\n"

    def save_to_file(self, file_path: str):
        with open(file_path, "w", encoding="utf-8", newline="\n") as output:
            output.write(str(self))
