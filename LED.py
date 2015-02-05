from PartType import *
from PartParameter import *
from ParameterQuery import *
from Digikey import *

class LED(PartType):
    def __init__(self, **args):
        PartType.__init__(self,"LED", args,
                          {"VALUE" : PartParameter("VALUE", "Color", "str", lambda x: x, Exact("Red")),
                           "WAVELENGTH" : PartParameter("WAVELENGTH", "Wavelength - Dominant", "float",  parseNanometer, None),
                           "CANDELA" : PartParameter("CANDELA", "Millicandela Rating", "float",  parseMillicandela, None),
                           "VFWD": PartParameter("VFWD", "Voltage - Forward (Vf) (Typ)", "float", parseVolts, None),
                           "IFWD": PartParameter("IFWD", "Current - Test", "float", parseAmps, None),
                           "BRIGHTNESS": PartParameter("BRIGHTNESS", "Brightness", "str", lambda x: x, None),
                           "CASE" : PartParameter("CASE", "Package / Case", "str", parsePackage, None),
                           "DIST1PN" : PartParameter("DIST1PN", "Digi-Key Part Number", "str", lambda x : x, None),
                           "PRICE" : PartParameter("PRICE", "Unit Price (USD)", "float", parsePrice, None),
                           "STOCK" : PartParameter("STOCK", "Stock", "str", lambda x : x, None),
                           "db" : PartParameter("db", "db", "str", lambda x : x, None),
                           "minQty" :  PartParameter("minQty", "Minimum Quantity", "int", parseQty, Exact(1))
                           })

