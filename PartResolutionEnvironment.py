from PartParameter import *

class ParameterOrder(object):
    def __init__(self, key, cmp):
        self.cmp = cmp
        self.key = key
        self.str = "?Ordering on " + key + "?"
    def __str__(self):
        return self.str

class Minimize(ParameterOrder):
    def __init__(self, key):
        ParameterOrder.__init__(self,key, cmp)
        self.str = "Minimize " + "key"
class Maximize(ParameterOrder):
    def __init__(self, key):
        ParameterOrder.__init__(self,key, lambda x,y : cmp(y,x))
        self.str = "Maximize " + "key"

def sortByList(x, y, prefs):
    for i in prefs:
        if x == i and y != i:
            return -1
        elif x != i and y == i:
            return 1
        elif x == i and y == i:
            return 0
    return 0
            
class Prefer(ParameterOrder):
    def __init__(self, key, prefs):
        ParameterOrder.__init__(self,key, lambda x, y: sortByList(x, y, prefs))
        self.str = "Prefer " + str(key) + " to be " + " ".join(map(str,prefs))


class PartResolutionEnvironment:
    
    def __init__(self, config):
        self.config = config

    def getPreferences(self, type):
        return self.config[type][0]
        
    def alternatives(self, component):
        possibilities = []
        for r in self.config[component.partType][0].parts:
            v = True;
            for p in zip(r.parameters, component.parameters):
                if isinstance(p[1].value, ParameterQuery):
                    #print " ".join(map(str,p))
                    v = v and p[1].value.eval(p[0])
            if v:
                possibilities.append(r)

        for i in reversed(component.preference + self.config[component.partType][1]):
            possibilities.sort(i.cmp, lambda x: x.getParameter(i.key).value)

        return possibilities

    def resolve(self, component):
        return self.alternatives(component)[0]
