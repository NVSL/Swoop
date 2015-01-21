from Digikey import *
from PartParameter import *
from PartType import *

class Resistor(PartType):
    def __init__(self, **args):
        self.__dict__["partType"] = "Resistor"
        self.__dict__["resistance"] = PartParameter("resistance", "Resistance (Ohms)", "float", parseResistance, Exact(330));
        self.__dict__["tolerance"] = PartParameter("tolerance", "Tolerance", "float", parseTolerance, LT(0.1));
        self.__dict__["watts"] = PartParameter("watts", "Power (Watts)", "int",  parseWatts, GT(0.125));
        self.__dict__["package"] = PartParameter("package", "Supplier Device Package", "str", parsePackage, None);
        self.__dict__["partnumber"] = PartParameter("partnumber", "Digi-Key Part Number", "str", lambda x : x, None);
        self.__dict__["price"] = PartParameter("price", "Unit Price (USD)", "float", parsePrice, None);
        self.__dict__["stock"] = PartParameter("stock", "Stock", "str", lambda x : x, None);
        self.__dict__["db"] = PartParameter("db", "db", "str", lambda x : x, None);
        self.__dict__["minQty"] =  PartParameter("minQty", "Minimum Quantity", "int", parseQty, Exact(1));
        self.__dict__["parameters"] = [self.resistance, self.price, self.tolerance, self.watts, self.package, self.partnumber, self.db]
        
        if "_db_rec" in args:
            for p in self.parameters:
                if p.key in args["_db_rec"]:
                    p.value = p.parse(args["_db_rec"][p.key])
        else:
            for p in args:
                setattr(self,p,args[p])

