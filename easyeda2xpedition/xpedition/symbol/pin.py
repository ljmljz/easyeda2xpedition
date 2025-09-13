from dataclasses import dataclass

class SymbolPinPosition(object):
    def __init__(self, start_x: float, start_y: float, end_x: float, end_y: float):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y


class SymbolPin(object):
    def __init__(self, number: str, pos: SymbolPinPosition, rotation: int = 0, side: int = 0, inverted: bool = 0):
        self.number = number
        self.pos = pos
        self.rotation = rotation # 0: 0deg, 1: 90deg, 2: 180deg, 3: 270deg
        self.side = side # 0: top, 1: bottom, 2: left, 3: right
        self.inverted = inverted # 0: normal, 1: inverted

    def __str__(self):
        pin_string = "P "
        pin_string += f"{self.number} "
        pin_string += f"{self.pos.end_x} {self.pos.end_y} {self.pos.start_x} {self.pos.start_y} "
        pin_string += f"{self.rotation} "
        pin_string += f"{self.side} "
        pin_string += f"{self.inverted}\n"

        return pin_string

class SymbolLabel(object):
    def __init__(self, label: str, x: float, y: float, rotation: int = 0, anchor: int = 2, visible: int = 1):
        self.label = label
        self.x = x
        self.y = y
        self.text_size = 8
        self.rotation = rotation
        self.anchor = anchor # 1: lower, 2: middle left, 3: upper, 8: middle right
        self.scope = 0 # 1: global, 0: local
        self.visible = visible # 0: invisible, 1: visible, 2: name only, 3: value only
        self.logic_sense = 0 # 0: normal, 1: inverted

    def __str__(self):
        label_string = "L "
        label_string += f"{self.x} {self.y} "
        label_string += f"{self.text_size} "
        label_string += f"{self.rotation} "
        label_string += f"{self.anchor} "
        label_string += f"{self.scope} "
        label_string += f"{self.visible} "
        label_string += f"{self.logic_sense} "
        label_string += f"{self.label}\n"

        return label_string
    
class SymbolAnnotation(object):
    def __init__(self, annotation: str, x: float, y: float, rotation: int = 0, anchor: int = 3, visible: int = 3):
        self.annotation = annotation
        self.x = x
        self.y = y
        self.text_size = 8
        self.rotation = rotation
        self.anchor = anchor
        self.visible = visible # 0: invisible, 1: visible, 2: name only, 3: value only

    def __str__(self):
        annotation_string = "A "
        annotation_string += f"{self.x} {self.y} "
        annotation_string += f"{self.text_size} "
        annotation_string += f"{self.rotation} "
        annotation_string += f"{self.anchor} "
        annotation_string += f"{self.visible} "
        annotation_string += f"{self.annotation}\n"

        return annotation_string

@dataclass
class SymbolPinGroup:
    pin: SymbolPin
    label: SymbolLabel
    annotations: list[SymbolAnnotation]

    def __str__(self):
        group_string = str(self.pin)
        group_string += str(self.label)

        for annotation in self.annotations:
            group_string += str(annotation)

        return group_string
    
    def add_annotation(self, annotation: SymbolAnnotation):
        if self.annotations is None:
            self.annotations = []

        self.annotations.append(annotation)