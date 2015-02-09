from PartType import *
from PartParameter import *
from ParameterQuery import *
import Digikey

class LED(PartType):
    def __init__(self, **args):
        PartType.__init__(self,"LED", args,
                          {"VALUE" : PartParameter("VALUE", "Color", "str", lambda x: x, Exact("Red")),
                           "WAVELENGTH" : PartParameter("WAVELENGTH", "Wavelength - Dominant", "float",  Digikey.parseNanometer, None),
                           "CANDELA" : PartParameter("CANDELA", "Millicandela Rating", "float",  Digikey.parseMillicandela, None),
                           "VFWD": PartParameter("VFWD", "Voltage - Forward (Vf) (Typ)", "float", Digikey.parseVolts, None),
                           "IFWD": PartParameter("IFWD", "Current - Test", "float", Digikey.parseAmps, None),
                           "BRIGHTNESS": PartParameter("BRIGHTNESS", "Brightness", "str", lambda x: x, None),
                           "CASE" : PartParameter("CASE", "Package / Case", "str", Digikey.parsePackage, None),
                           "SIZE" : PartParameter("SIZE", "Package / Case", "str", Digikey.parseSize, None)
                           })

