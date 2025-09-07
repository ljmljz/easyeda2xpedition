# Pads.hkp File Format

## General

This document describes the Pads.hkp file format used by Mentor Graphics Xpedition for PCB design. The format is primarily used for storing PAD and PADSTACK data in an ASCII format.

The file is split into sections, each starting with a dot (.) followed by a section name. The section names are case-insensitive.

The attributes within each section are also case-insensitive. And it's indent with multile dots.

## Header Section

The header section contains the file version and creator information.
> .FILETYPE PADSTACK_LIBRARY  
> .VERSION "VB99.0"  
> .SCHEMA_VERSION 13  
> .CREATOR "EasyEDA2Xpedition"

## UNIT Section

The unit section specifies the unit of measurement used in the design.
> .UNIT TH

`TH` specifies the unit of the design. `TH` stands for "thousandth of an inch". it equals to `mil`.

## PAD Section

here is the pad section example:
> .PAD "SQUARE 5x5"  
> ..SQUARE  
> ...WIDTH 5  
> ...PAD_OPTIONS  USER_GENERATED_NAME  
> ..OFFSET (0, 0)

- `.PAD "SQUARE 5x5"` defines a PAD named "SQUARE 5x5"
- `..SQUARE` indicates that this is a square shape pad. the valid shape can be `SQUARE`, `ROUND`, `RECTANGLE`, `OBLONG`, `OCTAGON`, etc.
- `...WIDTH 5` specifies the width of the pad.
- `...PAD_OPTIONS USER_GENERATED_NAME` indicates that this pad is user-generated.
- `..OFFSET (0, 0)` specifies the offset of the pad from its reference point.

## HOLE Section

The hole section specifies the hole size and shape of the pad or mounting hole.
here is the hole section example:
> .HOLE "ROUND 26"  
..ROUND  
...DIAMETER 26  
..POSITIVE_TOLERANCE 0  
..NEGATIVE_TOLERANCE 0  
..HOLE_OPTIONS NON_PLATED DRILLED USER_GENERATED_NAME

- `.HOLE "ROUND 26"` defines a hole named "ROUND 26".
- `..ROUND` indicates that this is a round hole. the valid shape can be `ROUND`, `RECTANGLE`, `SLOT`.
- `...DIAMETER 26` specifies the diameter of the hole.
- `..POSITIVE_TOLERANCE 0` specifies the positive tolerance of the hole size.
- `..NEGATIVE_TOLERANCE 0` specifies the negative tolerance of the hole size.
- `..HOLE_OPTIONS NON_PLATED DRILLED USER_GENERATED_NAME` specifies the hole options. `NON_PLATED` indicates that the hole is not plated, it can be `PLATED` indicates that the hole is plated. `DRILLED` indicates that the hole is drilled, and `USER_GENERATED_NAME` indicates that this hole is user-generated.

## PADSTACK Section

The padstack section specifies the padstack name, padstack type, and padstack attributes.

here is the padstack section example:
> .PADSTACK "SX5Y5D0T0"  
..PADSTACK_TYPE PIN_SMD  
..TECHNOLOGY "(Default)"  
...TECHNOLOGY_OPTIONS NONE  
...TOP_PAD "SQUARE 5x5"  
...BOTTOM_PAD "SQUARE 5x5"  
...TOP_SOLDERMASK_PAD "SQUARE 5x5"  
...TOP_SOLDERPASTE_PAD "SQUARE 5x5"  
...BOTTOM_SOLDERMASK_PAD "SQUARE 5x5"  
...BOTTOM_SOLDERPASTE_PAD "SQUARE 5x5"

- `.PADSTACK "SX5Y5D0T0"` defines a padstack named "SX5Y5D0T0".
- `..PADSTACK_TYPE PIN_SMD` specifies that this padstack is a surface mount device (SMD) pin. it can be `PIN_THROUGH` too.
- `..TECHNOLOGY "(Default)"` specifies the technology used for this padstack.
- `...TECHNOLOGY_OPTIONS NONE` specifies the technology options.
- `...TOP_PAD "SQUARE 5x5"` specifies the top pad of this padstack.
- `...BOTTOM_PAD "SQUARE 5x5"` specifies the bottom pad of this padstack.
- `...TOP_SOLDERMASK_PAD "SQUARE 5x5"` specifies the top solder mask pad of this padstack.
- `...TOP_SOLDERPASTE_PAD "SQUARE 5x5"` specifies the top solder paste pad of this padstack.
- `...BOTTOM_SOLDERMASK_PAD "SQUARE 5x5"` specifies the bottom solder mask pad of this padstack.
- `...BOTTOM_SOLDERPASTE_PAD "SQUARE 5x5"` specifies the bottom solder paste pad of this padstack.

To be noted. the solder mask pad should be larger than the top and bottom pad. But here uses the same pad. we can add a solder mask shape in cell definition.
