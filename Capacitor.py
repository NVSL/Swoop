from PartType import *
from PartParameter import *
from Digikey import *

class CeramicCapacitor(PartType):
    def __init__(self, **args):
        self.__dict__["partType"] = "CeramicCapacitor"
        self.__dict__["capacitance"] = PartParameter("capacitance", "Capacitance", "float", parseCapacitance, Exact(pF(1))); 
        self.__dict__["tolerance"] = PartParameter("tolerance", "Tolerance", "float", parseTolerance, None)
        self.__dict__["volts"] = PartParameter("volts", "Voltage - Rated", "float",  parseVolts, GT(5))
        self.__dict__["package"] = PartParameter("package", "Package / Case", "str", parsePackage, None)
        self.__dict__["partnumber"] = PartParameter("partnumber", "Digi-Key Part Number", "str", lambda x : x, None)
        self.__dict__["price"] = PartParameter("price", "Unit Price (USD)", "float", parsePrice, None)
        self.__dict__["stock"] = PartParameter("stock", "Stock", "str", lambda x : x, None)
        self.__dict__["db"] = PartParameter("db", "db", "str", lambda x : x, None)
        self.__dict__["minQty"] =  PartParameter("minQty", "Minimum Quantity", "int", parseQty, Exact(1))
        self.__dict__["parameters"] = [self.capacitance, self.price, self.tolerance, self.volts, self.package, self.partnumber, self.db]
        
        if "_db_rec" in args:
            for p in self.parameters:
                if p.key in args["_db_rec"]:
                    p.value = p.parse(args["_db_rec"][p.key])
        else:
            for p in args:
                setattr(self,p,args[p])

