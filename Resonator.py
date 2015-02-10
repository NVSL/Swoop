import Digikey
from PartParameter import *
from ParameterQuery import *
from PartType import *

class Resonator(PartType):
    
    def __init__(self, **args):
        PartType.__init__(self, "Resonator", args,
                          {"VALUE" : PartParameter("VALUE", "Frequency", "float", Digikey.parseFrequency, None),
                           "TOL" : PartParameter("TOL", "Frequency Tolerance", "float", Digikey.parseTolerance, LT(0.1)),
                           "STBL" : PartParameter("STABILITY", "Frequency Stability", "float", Digikey.parseTolerance, LT(0.1)),
                           "PWR" : PartParameter("PWR", "Power (Watts)", "int",  Digikey.parseWatts, GT(0.1)),
                           "CAP": PartParameter("VALUE", "Capacitance", "float", Digikey.parseCapacitance, None),
                           "CASE" : PartParameter("CASE", "Package / Case", "str", Digikey.parsePackage, None),
                           "SIZE" : PartParameter("SIZE", "Package / Case", "str", Digikey.parseSize, None),
                           })
