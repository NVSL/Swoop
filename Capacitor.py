from PartType import *
from PartParameter import *
from ParameterQuery import *
from Digikey import *

class CeramicCapacitor(PartType):
    def __init__(self, **args):
        PartType.__init__(self,"CeramicCapacitor", args,
                          {"VALUE" : PartParameter("VALUE", "Capacitance", "float", parseCapacitance, Exact(pF(100))),
                           "TOL" : PartParameter("TOL", "Tolerance", "float", parseTolerance, None),
                           "VOLTS" : PartParameter("VOLTS", "Voltage - Rated", "float",  parseVolts, GT(10)),
                           "CASE" : PartParameter("CASE", "Supplier Device Package", "str", parsePackage, None),
                           "MFR" : PartParameter("MFR", "Manufacturer", "str", lambda x : x, None),
                           "MPN" : PartParameter("MPN", "Manufacturer Part Number", "str", lambda x : x, None),
                           "DIST1" : PartParameter("DIST1", "Digi-Key Part Number", "str", lambda x  :  x, None),
                           "DIST1PN" : PartParameter("DIST1PN", "Digi-Key Part Number", "str", lambda x  :  x, None),
                           "PRICE" : PartParameter("PRICE", "Unit Price (USD)", "float", parsePrice, None),
                           "STOCK" : PartParameter("STOCK", "Stock", "str", lambda x : x, None),
                           "db" : PartParameter("db", "db", "str", lambda x : x, None),
                           "minQty" : PartParameter("minQty", "Minimum Quantity", "int", parseQty, Exact(1))
                           })

class TantalumCapacitor(PartType):
    def __init__(self, **args):
        PartType.__init__(self,"TantalumCapacitor", args,
                          {"VALUE" : PartParameter("VALUE", "Capacitance", "float", parseCapacitance, Exact(pF(100))),
                           "TOL" : PartParameter("TOL", "Tolerance", "float", parseTolerance, None),
                           "VOLTS" : PartParameter("VOLTS", "Voltage - Rated", "float",  parseVolts, GT(10)),
                           "ESR" : PartParameter("ESR", "ESR (Equivalent Series Resistance)", "float",  parseESR, None),
                           "CASE" : PartParameter("CASE", "Supplier Device Package", "str", parsePackage, None),
                           "MFR" : PartParameter("MFR", "Manufacturer", "str", lambda x : x, None),
                           "MPN" : PartParameter("MPN", "Manufacturer Part Number", "str", lambda x : x, None),
                           "DIST1" : PartParameter("DIST1", "Digi-Key Part Number", "str", lambda x  :  x, None),
                           "DIST1PN" : PartParameter("DIST1PN", "Digi-Key Part Number", "str", lambda x  :  x, None),
                           "PRICE" : PartParameter("PRICE", "Unit Price (USD)", "float", parsePrice, None),
                           "STOCK" : PartParameter("STOCK", "Stock", "str", lambda x : x, None),
                           "db" : PartParameter("db", "db", "str", lambda x : x, None),
                           "minQty" : PartParameter("minQty", "Minimum Quantity", "int", parseQty, Exact(1))
                           })
