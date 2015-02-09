import Digikey
from PartParameter import *
from ParameterQuery import *
from PartType import *

class ZenerDiode(PartType):
    
    def __init__(self, **args):
        PartType.__init__(self, "ZenerDiode", args,
                          {"VALUE" : PartParameter("VALUE", "Voltage - Zener (Nom) (Vz)", "float", Digikey.parseVolts, None),
                           "TOL" : PartParameter("TOL", "Tolerance", "float", Digikey.parseTolerance, LT(0.1)),
                           "PWR" : PartParameter("PWR", "Power - Max", "int",  Digikey.parseWatts, GT(0.125)),
##                           "ILEAK" : PartParameter("ILEAK", "Current - Reverse Leakage @ Vr", "int",  Digikey.parseWatts, GT(0.125)),
#                           "IZMAX" : PartParameter("IZMAX", "Power (Watts)", "int",  Digikey.parseWatts, GT(0.125)),
##                           "VFWD" : PartParameter("VFWD", "Voltage - Forward (Vf) (Max) @ If", "int",  Digikey.parseWatts, GT(0.125)),
                           "CASE" : PartParameter("CASE", "Supplier Device Package", "str", Digikey.parsePackage, None),
                           "SIZE" : PartParameter("SIZE", "Package / Case", "str", Digikey.parseSize, None)
                           })



class SchottkyDiode(PartType):
    
    def __init__(self, **args):
        PartType.__init__(self, "SchottkyDiode", args,
                          {"VALUE" : PartParameter("VALUE", "Voltage - Zener (Nom) (Vz)", "float", Digikey.parseVolts, None),
                           #"TOL" : PartParameter("TOL", "Tolerance", "float", Digikey.parseTolerance, LT(0.1)),
                           #"PWR" : PartParameter("PWR", "Power - Max", "int",  Digikey.parseWatts, GT(0.125)),
#                           "ILEAK" : PartParameter("ILEAK", "Current - Reverse Leakage @ Vr", "str", Digikey.parsePackage, None),
                           "IRECT" : PartParameter("IRECT", "Current - Average Rectified (Io)", "str", Digikey.parseAmps, None),
                           "RECOV" : PartParameter("RECOV", "Reverse Recovery Time (trr)", float, Digikey.parseNanoseconds, None),
#                           "RVDC" : PartParameter("RVDC", "Supplier Device Package", "str", Digikey.parsePackage, None),
#                           "SPEED" : PartParameter("SPEED", "Supplier Device Package", "str", Digikey.parsePackage, None),
                           "VFWD" : PartParameter("VFWD", "Voltage - Forward (Vf) (Max) @ If", "str", Digikey.parseVolts, None),
                           "VREV" : PartParameter("VREV", "Voltage - DC Reverse (Vr) (Max)", "str", Digikey.parseVolts, None),
                           "CASE" : PartParameter("CASE", "Supplier Device Package", "str", Digikey.parsePackage, None),
                           "SIZE" : PartParameter("SIZE", "Package / Case", "str", Digikey.parseSize, None)
                           })


