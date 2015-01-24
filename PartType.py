from PartParameter import *
from ParameterQuery import *

class PartType:
    partType = "Abstract"
    preference = []

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

