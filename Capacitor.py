from PartType import *
from PartParameter import *
from ParameterQuery import *
from Digikey import *

class CeramicCapacitor(PartType):

    def __init__(self, **args):
        setattr(self,"parameters", {
                "VALUE" : PartParameter("VALUE", "Capacitance", "float", parseCapacitance, Exact(pF(100))),
                "TOL" : PartParameter("TOL", "Tolerance", "float", parseTolerance, None),
                "VOLTS" : PartParameter("VOLTS", "Voltage - Rated", "float",  parseVolts, GT(5)),
                "CASE" : PartParameter("CASE", "Package / Case", "str", parsePackage, None),
                "DIST1PN" : PartParameter("DIST1PN", "Digi-Key Part Number", "str", lambda x : x, None),
                "PRICE" : PartParameter("PRICE", "Unit Price (USD)", "float", parsePrice, None),
                "STOCK" : PartParameter("STOCK", "Stock", "str", lambda x : x, None),
                "db" : PartParameter("db", "db", "str", lambda x : x, None),
                "minQty" :  PartParameter("minQty", "Minimum Quantity", "int", parseQty, Exact(1))
                })
        #self.__dict__["parameters"] = [self.capacitance, self.price, self.tolerance, self.volts, self.package, self.partnumber, self.db]
        
        for p in sorted(self.parameters):
            self.__dict__[p] = self.parameters[p]

        self.parameterList = [self.parameters[a] for a in sorted(self.parameters)]

        self.__dict__["partType"] =  "CeramicCapacitor"

        if "_db_rec" in args:
            for p in self.parameters.values():
                if p.key in args["_db_rec"]:
                    p.value = p.parse(args["_db_rec"][p.key])
        else:
            for p in args:
                setattr(self,p,args[p])
