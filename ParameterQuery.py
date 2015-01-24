import re

float_re = "([-+]?\d*\.\d+|[-+]?\d+)"
pos_float_re = "(\d*\.\d+|\d+)"
int_re = "([-+]?\d+)"


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
    def parse(s):
        r = None
        stripped = s.replace(" ","")
        for c in all_subclasses(ParameterQuery):
            try:
                #print c.getRE()
                #print stripped
                match = re.search("^"+c.getRE()+"$", stripped)
                if match is not None:
                    t = c.buildFromMatch(match)
                    if r is not None:
                        print stripped + "is ambiguous " + str(c) + ": " + str(r)
                    r = t
            except:
                continue;
        return r

class Range(ParameterQuery):

    def __init__(self, min, max):
        ParameterQuery.__init__(self, lambda x: x.value >= min and x.value <= max)
        self.s = str(max) + " >= v >= " + str(min)
        
    @staticmethod
    def getRE():
        return "\[" + float_re + "," + float_re +"\]"

    @staticmethod
    def buildFromMatch(match):
        return Range(float(match.group(1)), float(match.group(2)))

class Approx(ParameterQuery):
    def __init__(self, target, var=0.1):
        ParameterQuery.__init__(self, lambda x: x.value >= target - (var*target) and x.value <= target + (var *target))
        self.s = str(target) + " +/- " + str(var*100) + "%"

    @staticmethod
    def getRE():
        return pos_float_re + "\+/-" + pos_float_re + "%"

    @staticmethod
    def buildFromMatch(match):
        return Approx(float(match.group(1)), float(match.group(2))/100.0)

class LT(ParameterQuery):

    def __init__(self, max):
        ParameterQuery.__init__(self, lambda x: x.value <= max)
        self.s = " <= " + str(max)

    @staticmethod
    def getRE():
        return "<=?" + float_re

    @staticmethod
    def buildFromMatch(match):
        return LT(float(match.group(1)))        


class GT(ParameterQuery):
    def __init__(self, min):
        ParameterQuery.__init__(self, lambda x: x.value >= min)
        self.s = " >= " + str(min)

    @staticmethod
    def getRE():
        return ">=?" + float_re

    @staticmethod
    def buildFromMatch(match):
        return GT(float(match.group(1)))        

class Exact(ParameterQuery):
    v = None
    def __init__(self, v):
        ParameterQuery.__init__(self, lambda x: x.value == v)
        self.s = " == " + str(v)

    @staticmethod
    def getRE():
        return float_re

    @staticmethod
    def buildFromMatch(match):
        return Exact(float(match.group(1)))        
