

class PartParameter:
    name = None
    type = "str"
    value = None
    key = None
    def __init__(self, name, key, type = "str", parse = lambda x:x, value = None):
        self.name = name
        self.type = type
        self.value = value
        self.key = key
        self.parse = parse
    def __str__(self):
        return self.name + " = " + (str(self.value) if self.value != None else "*")

class ParameterQuery(object):
    def __init__(self, p):
        self.predicate = p;
        self.s = "?predicate?"

    def eval(self, part):
        return self.predicate(part)

    def __str__(self):
        return "(" +self.s + ")";

class Range(ParameterQuery):
    def __init__(self, min, max):
        ParameterQuery.__init__(self, lambda x: x.value >= min and x.value <= max)
        self.s = str(max) + " >= v >= " + str(min)

class Approx(ParameterQuery):
    def __init__(self, target, var=0.1):
        ParameterQuery.__init__(self, lambda x: x.value >= target - (var*target) and x.value <= target + (var *target))
        self.s = str(target) + " +/- " + str(var*100) + "%"


class LT(ParameterQuery):
    def __init__(self, max):
        ParameterQuery.__init__(self, lambda x: x.value <= max)
        self.s = " <= " + str(max)

class GT(ParameterQuery):
    def __init__(self, min):
        ParameterQuery.__init__(self, lambda x: x.value >= min)
        self.s = " >= " + str(min)

class Exact(ParameterQuery):
    v = None
    def __init__(self, v):
        ParameterQuery.__init__(self, lambda x: x.value == v)
        self.s = " == " + str(v)

