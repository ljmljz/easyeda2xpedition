from easyeda.parameters_easyeda import ee_footprint

pads = {}
padstacks = {}

class EasyEDAPad(object):
    def __init__(self, pad_data: dict):
        self._raw_data = pad_data
        self.name = pad_data.get("name", "")
        self.type = pad_data.get("type", "")
        self.shape = pad_data.get("shape", "")
        self.data = pad_data.get("data", None)

class EasyEDAPadStack(object):
    def __init__(self):
        self.name = ""
        self.top_pad = None
        self.bottom_pad = None
        self.internal_pad = None
        self.top_solderpaste_pad = None
        self.bottom_solderpaste_pad = None
        self.top_soldermask_pad = None
        self.bottom_soldermask_pad = None
        self.hole_name = None

def get_pads_from_footprint(footprint: ee_footprint) -> dict:
    for pad in footprint.pads:
        pad_name = f"{pad.shape}_{pad.width}x{pad.height}"
        pad_type = "TH" if pad.hole_radius > 0 else "SMD"
        normalized_points = []
        normalized_hole_points = []

        for idx, val in enumerate(pad.points.split(" ")):
            point = float(val.strip())

            x, y = 0, 0
            if idx % 2 == 0:  # x-coordinate
                x = point - pad.center_x
            else:  # y-coordinate
                y = point - pad.center_y

            normalized_points.append((x, y))

        for idx, val in enumerate(pad.hole_points.split(" ")):
            point = float(val.strip())

            x, y = 0, 0
            if idx % 2 == 0:  # x-coordinate
                x = point - pad.center_x
            else:  # y-coordinate
                y = point - pad.center_y

            normalized_hole_points.append((x, y))

        pad_data = {
            "name": pad_name,
            "type": pad_type,
            "shape": pad.shape,
            "data": {
                "points": normalized_points,
                "hole_points": normalized_hole_points,
                "width": pad.width,
                "height": pad.height,
                "hole_radius": pad.hole_radius,
                "hole_length": pad.hole_length,
            }
        }

        if pad_name not in pads:
            pads[pad_name] = EasyEDAPad(pad_data)

        return pads


def get_padstacks_from_footprint(footprint: ee_footprint) -> dict:
    for idx, pad in enumerate(footprint.pads):
        pad_name = f"{pad.shape}_{pad.width}x{pad.height}"
        if pad_name in pads:
            easyeda_pad = pads[pad_name]
            easyeda_padstack = EasyEDAPadStack()
            easyeda_padstack.top_pad = easyeda_pad