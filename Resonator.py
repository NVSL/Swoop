import Digikey
from PartParameter import *
from ParameterQuery import *
from PartType import *
import Units

class Resonator(PartType):
    
    def __init__(self, **args):
        PartType.__init__(self, "Resonator", args,
                          {"VALUE" : PartParameter("VALUE", "Frequency", "float", Digikey.parseFrequency, None,render=Units.renderHz),
                           "TOL" : PartParameter("TOL", "Frequency Tolerance", "float", Digikey.parseTolerance, LT(0.1)),
                           "STBL" : PartParameter("STABILITY", "Frequency Stability", "float", Digikey.parseTolerance, LT(0.1)),
                           "PWR" : PartParameter("PWR", "Power (Watts)", "int",  Digikey.parseWatts, GT(0.1)),
                           "CAP": PartParameter("VALUE", "Capacitance", "float", Digikey.parseCapacitance, None, render=Units.renderFarads),
                           "CASE" : PartParameter("CASE", "Package / Case", "str", Digikey.parsePackage, None),
                           "SIZE" : PartParameter("SIZE", "Package / Case", "str", Digikey.parseSize, None),
                           })
