from Digikey import *
from PartParameter import *
from ParameterQuery import *
from PartType import *

class Resistor(PartType):
    
    def __init__(self, **args):
        PartType.__init__(self, "Resistor", args,
                          {"VALUE" : PartParameter("VALUE", "Resistance (Ohms)", "float", parseResistance, Exact(330)),
                           "TOL" : PartParameter("TOL", "Tolerance", "float", parseTolerance, LT(0.1)),
                           "PWR" : PartParameter("PWR", "Power (Watts)", "int",  parseWatts, GT(0.125)),
                           "CASE" : PartParameter("CASE", "Supplier Device Package", "str", parsePackage, None),
                           "DIST1PN" : PartParameter("DIST1PN", "Digi-Key Part Number", "str", lambda x  :  x, None),
                           "PRICE" : PartParameter("PRICE", "Unit Price (USD)", "float", parsePrice, None),
                           "STOCK" : PartParameter("STOCK", "Stock", "str", lambda x : x, None),
                           "db" : PartParameter("db", "db", "str", lambda x : x, None),
                           "minQty" : PartParameter("minQty", "Minimum Quantity", "int", parseQty, Exact(1))
                           })
