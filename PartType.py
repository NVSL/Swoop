from PartParameter import *
from ParameterQuery import *
import Digikey

class PartType:
    partType = "Abstract"
    preference = []

    def __init__(self, typename,args,fields):
        setattr(self, "parameters",{
                #                           "DIST1" : PartParameter("DIST1", "Digi-Key Part Number", "str", lambda x  :  x, None),
                "DIST1PN" : PartParameter("DIST1PN", "Digi-Key Part Number", "str", lambda x : x, None),
                "PRICE" : PartParameter("PRICE", "Unit Price (USD)", "float", Digikey.parsePrice, None),
                "STOCK" : PartParameter("STOCK", "Stock", "str", lambda x : x.upper(), None),
                "PACKAGE" : PartParameter("PACKAGE", "Package", "str", lambda x : x, None),
                "MFR" : PartParameter("MFR", "Manufacturer", "str", lambda x : x, None),
                "MPN" : PartParameter("MPN", "Manufacturer Part Number", "str", lambda x : x, None),
                "db" : PartParameter("db", "db", "str", lambda x : x, None),
                "minQty" :  PartParameter("minQty", "Minimum Quantity", "int", Digikey.parseQty, Exact(1))
                })
        self.parameters.update(fields)

        for p in sorted(self.parameters):
            self.__dict__[p] = self.parameters[p]

        self.parameterList = [self.parameters[a] for a in sorted(self.parameters)]

        self.__dict__["partType"] = typename

        if "_db_rec" in args:
            for p in self.parameters.values():
                if p.key in args["_db_rec"]:
                    p.value = p.parse(args["_db_rec"][p.key])
        else:
            for p in args:
                setattr(self,p,args[p])

    def setField(self, name, value):
        self.parameters[name].value = value

    def getField(self, name):
        return self.parameters[name].value

    def renderField(self,name):
        return self.parameters[name].render(self.parameters[name].value)
    
    # magic to allow us to assign query objects to the fields.
    def __setattr__(self, name, value):
        if type(value) is int or type(value) is float:
            self.__dict__[name].value = Exact(value)
        elif type(value) is PartParameter:
            self.__dict__[name].value = value
        else:
            self.__dict__[name] = value
                    
    def getParameter(self, s):
        return getattr(self, s)

    def __str__(self):
        return "; ".join(map(str,self.parameterList))

