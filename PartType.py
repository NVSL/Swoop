from PartParameter import *
from ParameterQuery import *

class PartType:
    partType = "Abstract"
    preference = []

    def __init__(self, typename,args,fields):
        setattr(self,"parameters",fields)
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

