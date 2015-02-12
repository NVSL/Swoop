import Digikey
from PartParameter import *
from ParameterQuery import *
from PartType import *
import Units

class Resistor(PartType):
    
    def __init__(self, **args):
        PartType.__init__(self, "Resistor", args,
                          {"VALUE" : PartParameter("VALUE", "Resistance (Ohms)", "float", Digikey.parseResistance, None,render=Units.renderOhms),
                           "TOL" : PartParameter("TOL", "Tolerance", "float", Digikey.parseTolerance, LT(0.1),render=Units.renderTolerance),
                           "PWR" : PartParameter("PWR", "Power (Watts)", "int",  Digikey.parseWatts, GT(0.1),Units.renderWatts),
                           "CASE" : PartParameter("CASE", "Supplier Device Package", "str", Digikey.parsePackage, None),
                           "SIZE" : PartParameter("SIZE", "Package / Case", "str", Digikey.parseSize, None),
                           })
