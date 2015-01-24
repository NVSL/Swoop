from PartType import *
from PartParameter import *
from ParameterQuery import *
from Digikey import *

class CeramicCapacitor(PartType):

    def __init__(self, **args):
        setattr(self,"parameters", {
                "VALUE" : PartParameter("capacitance", "Capacitance", "float", parseCapacitance, Exact(pF(1))),
                "TOL" : PartParameter("tolerance", "Tolerance", "float", parseTolerance, None),
                "VOLTS" : PartParameter("volts", "Voltage - Rated", "float",  parseVolts, GT(5)),
                "CASE" : PartParameter("package", "Package / Case", "str", parsePackage, None),
                "DIST1PN" : PartParameter("partnumber", "Digi-Key Part Number", "str", lambda x : x, None),
                "PRICE" : PartParameter("price", "Unit Price (USD)", "float", parsePrice, None),
                "STOCK" : PartParameter("stock", "Stock", "str", lambda x : x, None),
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
