from PartType import *
from PartParameter import *
from ParameterQuery import *
import Digikey

class CeramicCapacitor(PartType):
    def __init__(self, **args):
        PartType.__init__(self,"CeramicCapacitor", args,
                          {"VALUE" : PartParameter("VALUE", "Capacitance", "float", Digikey.parseCapacitance, None),
                           "TOL" : PartParameter("TOL", "Tolerance", "float", Digikey.parseTolerance, None),
                           "VOLTS" : PartParameter("VOLTS", "Voltage - Rated", "float",  Digikey.parseVolts, GT(10)),
                           "CASE" : PartParameter("CASE", "Supplier Device Package", "str", Digikey.parsePackage, None),
                           "SIZE" : PartParameter("SIZE", "Package / Case", "str", Digikey.parseSize, None),
                           })

class TantalumCapacitor(PartType):
    def __init__(self, **args):
        PartType.__init__(self,"TantalumCapacitor", args,
                          {"VALUE" : PartParameter("VALUE", "Capacitance", "float", Digikey.parseCapacitance, None),
                           "TOL" : PartParameter("TOL", "Tolerance", "float", Digikey.parseTolerance, None),
                           "VOLTS" : PartParameter("VOLTS", "Voltage - Rated", "float",  Digikey.parseVolts, GT(10)),
                           "ESR" : PartParameter("ESR", "ESR (Equivalent Series Resistance)", "float",  Digikey.parseESR, None),
                           "CASE" : PartParameter("CASE", "Supplier Device Package", "str", Digikey.parsePackage, None),
                           "SIZE" : PartParameter("SIZE", "Package / Case", "str", Digikey.parseSize, None),
                           })
