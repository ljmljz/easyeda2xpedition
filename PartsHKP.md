# Parts.hkp (ASCII_PDB) File Format

## General

This document describes the ASCII part database format used by Xpedition for
`*.pdb.hkp` files. The format is a dot-indented hierarchical text format. Each
level adds one tab and one dot.

The file begins with a fixed header followed by one or more part records. Parts
are separated by blank lines. Lines starting with `!` are comments.

## Header

```text
!.LCID 2052
.Filetype ASCII_PDB
.Version "02.01"
.LIBRARY_DB_TYPE "Enterprise"
.Units mm
.Notation Si
```

- `.Filetype ASCII_PDB` selects the ASCII part database format.
- `.Version "02.01"` is the format version used by the reference files.
- `.Units mm` defines the property unit system.
- `.Notation Si` selects metric notation.

## Part Record

```text
.Number "C25804"
	..Name "0603WAF1002T5E"
		...Default
	..Label "0603WAF1002T5E"
		...Default
	..Desc "10K 1% 0603"
	..RefPrefix "R"
	..TopCell "R0603"
	..BottomCell ""
	..Prop "Type",	"Resistor",	"Text"
```

- `.Number` is the unique part number used by the schematic and packager.
- `..Name` is the part name.
- `..Label` is the part label shown by the library tools.
- `..Desc` is the part description.
- `..RefPrefix` is the reference designator prefix, for example `R`, `C` or `U`.
- `..TopCell` is the top-side cell (footprint) name.
- `..BottomCell` is the bottom-side cell; an empty string means no separate
  bottom cell.
- `..Prop` stores a property as `"name", "value", "type"`. The common type is
  `Text`; numeric values may use `Real` or `Integer`.

## Gate and Pin Swap Data

```text
	..SwapGroup	"gate"
		...SwapID	"P0"
		...SwapID	"P1"
		...SwapIDProperties	"P0"
			....Prop "Pin Type",	"Input",	"Text"
		...SwapIDProperties	"P1"
			....Prop "Pin Type",	"Output",	"Text"
```

- `..SwapGroup` defines a gate and its pin swap identifiers.
- Each `...SwapID` corresponds to one logical pin in the gate.
- `...SwapIDProperties` assigns properties to the preceding swap identifier.
- `Pin Type` accepts logical values such as `Input`, `Output`, `Bidir`,
  `Power` and `Passive`.

## Symbol Reference

```text
	..Symbol	"EasyEDA:0603WAF1002T5E"
		...Default
		...Symbol_SwapGroup	"gate"
			....PinName	"2"
			....PinName	"1"
```

- `..Symbol` references a symbol as `library:symbol_name`.
- `...Default` marks the default symbol reference.
- `...Symbol_SwapGroup` maps a gate to the symbol pin names.
- `....PinName` lists the symbol pin names in the same order as the gate pins.

## Slots and Cell Pin Numbers

```text
	..Slots
		...Slot_SwapGroup	"gate"
			....SlotID	1
			....SwapCode	0
			....PinNumber	"2"
			....PinNumber	"1"
```

- `..Slots` maps gates to physical slots.
- `...Slot_SwapGroup` identifies the gate used by the slot.
- `....SlotID` is the slot number.
- `....SwapCode` is normally `0`.
- `....PinNumber` lists the cell pin numbers in the same order as the symbol pin
  names.

## Multi-Gate Parts

A multi-gate part contains one `..SwapGroup` block per gate and one
`...Symbol_SwapGroup` plus `...Slot_SwapGroup` block per gate. Slot IDs are
numbered sequentially from `1`. Pin swap identifiers restart at `P0` for each
gate.

```text
	..SwapGroup	"gate1"
		...SwapID	"P0"
	..SwapGroup	"gate2"
		...SwapID	"P0"
	...
	..Slots
		...Slot_SwapGroup	"gate1"
			....SlotID	1
		...Slot_SwapGroup	"gate2"
			....SlotID	2
```

## Generated Files

The converter writes a single part to `_Parts.pdb.hkp`:

```python
from easyeda2xpedition.convert_parts import EeSymbolToXpeditionPart

converter = EeSymbolToXpeditionPart(easyeda_data)
converter.save_to_file("./output/_Parts.pdb.hkp")
```

The file is UTF-8 encoded with LF line endings. The output uses the LCSC part
number as `.Number`, the EasyEDA symbol name as `.Name`, the manufacturer part
number as `.Label`, and the EasyEDA package name as `.TopCell`.

## Validation Notes

- ASCII PDB import support varies between Xpedition versions.
- Newer installations may require a licensed converter or an encrypted PDB.
- The generated pin mapping assumes one slot per gate. Parts with multiple
  slots per gate need additional mapping data.
