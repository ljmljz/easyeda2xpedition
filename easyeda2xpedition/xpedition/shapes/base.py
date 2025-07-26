class BaseShape(object):
    def __init__(self, level=3):
        self._level = level
        self.shape = ""

    def indent(self, level):
        indent_string =  " " * (level - 1)
        indent_string += "." * level
        
        return indent_string
    
    def to_string(self):
        self.__str__()