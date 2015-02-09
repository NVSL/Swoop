from PartParameter import *
from ParameterQuery import *

class ParameterOrder(object):
    def __init__(self, key, compare):
        self.compare = lambda x,y: compare(x.getParameter(key).value,y.getParameter(key).value)
        self.key = key
        self.str = "?Ordering on " + key + "?"
    def __str__(self):
        return self.str

class Minimize(ParameterOrder):
    def __init__(self, key):
        ParameterOrder.__init__(self,key, cmp)
        self.str = "Minimize " + key

class Maximize(ParameterOrder):
    def __init__(self, key):
        ParameterOrder.__init__(self,key, lambda x,y : cmp(y,x))
        self.str = "Maximize " + key

def sortByList(x, y, prefs):

    c = 0
    x_index = None
    y_index = None
    for i in prefs:
        c = c + 1
        if x == i:
            x_index = c
        if y == i:
            y_index = c

    if x_index is None:
        x_index = c + 1
    if y_index is None:
        y_index = c + 1
        
    #print str(x) + " = " + str(x_index)
    #print str(y) + " = " + str(y_index)

    if x_index > y_index:
        return 1
    elif x_index < y_index:
        return -1
    else:
        return 0
            
class Prefer(ParameterOrder):
    def __init__(self, key, prefs):
        ParameterOrder.__init__(self,key, lambda x, y: sortByList(x, y, prefs))
        self.str = "Prefer " + str(key) + " to be " + " ".join(map(str,prefs))


class PartResolutionEnvironment:
    
    def __init__(self, partType, db, preferences):
        self.partType = partType
        self.db = db;
        self.preferences = preferences

    def getPreferences(self):
        return self.preferences
        
    def alternatives(self, component):
        possibilities = []
        for r in self.db.parts:
            v = True;
            #print "============= " +  str(r.DIST1PN.value)
            for p in zip(r.parameterList, component.parameterList):
                #print str(p[1].name) + "<->" + str(type(p[1].value))
                if isinstance(p[1].value, ParameterQuery):
                    #print "-- " + " ".join(map(str,p))
                    v = v and p[1].value.eval(p[0])
            if v:
                #print r
                possibilities.append(r)
            else:
                #print str(r.DIST1PN.value) + " is not a match"
                pass

        for i in reversed(component.preference + self.preferences):
#            print "===== : " + i.str
#            print "\n".join(map(str,possibilities))
#            print str(i.compare) + " "+ i.key
            possibilities.sort(i.compare)
#            print "----------"
#            print "\n".join(map(str,possibilities))
#            print str(i.compare) + " "+ i.key

#        print "====="
#        print "\n".join(map(str,possibilities))

        return possibilities

    def resolve(self, component):
        #print  component.partType + " " + self.partType
        assert component.partType == self.partType
        return self.alternatives(component)[0]

    def resolveInPlace(self, component):
        #print component.partType, self.partType
        assert component.partType == self.partType
        options = self.alternatives(component)
        if len(options) != 0:
            r = options[0]
            for p in r.parameters:
                component.parameters[p].value = r.parameters[p].value
            return component
        else:
            return None
