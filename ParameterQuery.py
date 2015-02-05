import re

float_re = "([-+]?\d*\.\d+|[-+]?\d+)"
pos_float_re = "(\d*\.\d+|\d+)"
int_re = "([-+]?\d+)"
unit_re = "(([unpkM\%]?)([FHW]?))?"

def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]

class ParameterQuery(object):
    def __init__(self, p):
        self.predicate = p;
        self.s = "?predicate?"

    def eval(self, part):
        return self.predicate(part)

    def __str__(self):
        return "(" +self.s + ")";
    
    @staticmethod
    def parseMultiplier(x):
        if x is None:
            return 1.0
        m = re.search(unit_re,x)
        if m is not None:
            if m.group(2) == "p":
                return 1e-12
            elif m.group(2) == "u":
                return 1e-6
            elif m.group(2) == "n":
                return 1e-9
            elif m.group(2) == "K" or m.group(2) == "k":
                return 1e3
            elif m.group(2) == "M":
                return 1e6
            elif m.group(2) == "%":
                return 1e-2
            elif m.group(2) == "" or m.group(2) is None:
                return 1.0
            else:
                raise Exception("Can't parse units: '" + x +"'")
        elif x is "":
            return 1.0
        else:
            raise Exception("Can't parse units: '" + x +"'")
    
    @staticmethod
    def parse(s):
        r = None
        stripped = s.replace(" ","")
        for c in all_subclasses(ParameterQuery):
            #print c.getRE()
            #print stripped
            regex = "^"+c.getRE()+"$"
            #print regex
            #print stripped
            match = re.search(regex, stripped)
            if match is not None:
                t = c.buildFromMatch(match)
                if r is not None:
                    print stripped + "is ambiguous " + str(c) + ": " + str(r)
                r = t
        return r

class Range(ParameterQuery):

    def __init__(self, min, max):
        ParameterQuery.__init__(self, lambda x: x.value >= min and x.value <= max)
        self.s = str(max) + " >= v >= " + str(min)
        
    @staticmethod
    def getRE():
        return "\[" + float_re + unit_re + "," + float_re + unit_re + "\]"

    @staticmethod
    def buildFromMatch(match):
        m1 = ParameterQuery.parseMultiplier(match.group(2))
        m2 = ParameterQuery.parseMultiplier(match.group(5))
        return Range(float(match.group(1)) * m1 , float(match.group(4)) * m2)

class Approx(ParameterQuery):
    def __init__(self, target, var=0.1):
        ParameterQuery.__init__(self, lambda x: x.value >= target - (var*target) and x.value <= target + (var *target))
        self.s = str(target) + " +/- " + str(var*100) + "%"

    @staticmethod
    def getRE():
        return pos_float_re + unit_re + "\+/-" + pos_float_re + "%"

    @staticmethod
    def buildFromMatch(match):
        m = ParameterQuery.parseMultiplier(match.group(2))
        return Approx(float(match.group(1)) * m, float(match.group(4))/100.0)

class LT(ParameterQuery):

    def __init__(self, max):
        ParameterQuery.__init__(self, lambda x: x.value <= max)
        self.s = " <= " + str(max)

    @staticmethod
    def getRE():
        return "<=?" + float_re + unit_re

    @staticmethod
    def buildFromMatch(match):
        m = ParameterQuery.parseMultiplier(match.group(2))
        return LT(float(match.group(1)) * m)        


class GT(ParameterQuery):
    def __init__(self, min):
        ParameterQuery.__init__(self, lambda x: x.value >= min)
        self.s = " >= " + str(min)

    @staticmethod
    def getRE():
        return ">=?" + float_re + unit_re

    @staticmethod
    def buildFromMatch(match):
        m = ParameterQuery.parseMultiplier(match.group(2))
        return GT(float(match.group(1)) * m)        

class Exact(ParameterQuery):
    v = None
    def __init__(self, v):
        ParameterQuery.__init__(self, lambda x: x.value == v)
        self.s = " == " + str(v)

    @staticmethod
    def getRE():
        return "(" + float_re + unit_re +")|(.*)"

    @staticmethod
    def buildFromMatch(match):
        if match.group(1) is not None:
            m = ParameterQuery.parseMultiplier(match.group(3))
            return Exact(float(match.group(2)) * m)        
        else:
            return Exact(match.group(6))
