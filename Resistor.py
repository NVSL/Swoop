#!/usr/bin/env python
import csv
import argparse
import re

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

class PartDB:
    def __init__(self, partObjectType, partType, db):
        self.name = db
        self.partType = partType
        r = csv.DictReader(open(db, "rU"))
        self.parts = [partObjectType(_db_rec=h) for h in r]
        #print self.name + " = " + "\n".join(map(str,self.parts))
        for l in self.parts:
            l.db.value = db

        
class Parameter:
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

def parseResistance(r):
    r = r.upper()
    m = re.match("(\d+(\.\d+)?)(.?)", r);
 #   print "s = " + r
    assert(m is not None)
#    print "m = " + m.group(3)
    if m.group(3) is "":
        mult = 1.0
    elif m.group(3) is "K":
        mult = 1000.0
    elif m.group(3) is "M":
        mult = 1000000.0
    else:
        print m.group(0)
        assert(False)

    return mult * float(m.group(1))

def pF(x):
    return x * 1e-12

def uF(x):
    return x * 1e-6

def F(x):
    return x

def parseCapacitance(r):
    r = r.upper()
    m = re.match("(\d+(\.\d+)?)(.*)", r);
    assert(m is not None)
    if m.group(3) == "PF":
        mult = pF(1)
    elif m.group(3) == "UF":
        mult = uF(1)
    else:
        print m.group(0)
        print m.group(3)
        assert(False)

    return mult * float(m.group(1))

def parseTolerance(r):
    r = r.upper()
    if r == "JUMPER":
        return 0.01
    m = re.search("(\d+)%", r);
    if m is None:
        print "Can't parse tolerance: " + r + "; setting to 20%"
        return 0.2
    return float(m.group(1))/100.0

def parseVolts(r):
    r = r.upper()
    m = re.search("(\d+(\.\d+)?)V", r);
    return float(m.group(1))

def parsePackage(r):
    r = r.upper()
    if re.search("0?805", r):
        return "0805"
    elif re.search("0?603", r):
        return "0603"
    elif re.search("AXIAL", r):
        return "TH"
    else:
        print r
        assert(False)
        return None
    
def parseWatts(r):
    r = r.upper()
    m = re.match("(\d+(.\d+)?)W", r);
    return float(m.group(1))

def parseQty(r):
    r = r.upper()
    m = re.match("(.\d+)", r);
    if m:
        return int(m.group(1))
    else:
        return 1000

def parsePrice(r):
    r = r.upper()
    m = re.match("(\d+.\d+)", r);
    if m:
        return float(m.group(1))
    else:
        return 1000
    
class PartType:
    pmap ={}
    partType = "Abstract"
    preference = []

    # magic to allow us to assign query objects to the fields.
    def __setattr__(self, name, value):
        self.__dict__[name].value = value
                    
    def getParameter(self, s):
        return getattr(self, s)

    def __str__(self):
        return "; ".join(map(str,self.parameters))


class Resistor(PartType):
    def __init__(self, **args):
        self.__dict__["partType"] = "Resistor"
        self.__dict__["resistance"] = Parameter("resistance", "Resistance (Ohms)", "float", parseResistance, Exact(330));
        self.__dict__["tolerance"] = Parameter("tolerance", "Tolerance", "float", parseTolerance, LT(0.1));
        self.__dict__["watts"] = Parameter("watts", "Power (Watts)", "int",  parseWatts, GT(0.125));
        self.__dict__["package"] = Parameter("package", "Supplier Device Package", "str", parsePackage, None);
        self.__dict__["partnumber"] = Parameter("partnumber", "Digi-Key Part Number", "str", lambda x : x, None);
        self.__dict__["price"] = Parameter("price", "Unit Price (USD)", "float", parsePrice, None);
        self.__dict__["stock"] = Parameter("stock", "Stock", "str", lambda x : x, None);
        self.__dict__["db"] = Parameter("db", "db", "str", lambda x : x, None);
        self.__dict__["minQty"] =  Parameter("minQty", "Minimum Quantity", "int", parseQty, Exact(1));
        self.__dict__["parameters"] = [self.resistance, self.price, self.tolerance, self.watts, self.package, self.partnumber, self.db]
        
        if "_db_rec" in args:
            for p in self.parameters:
                if p.key in args["_db_rec"]:
                    p.value = p.parse(args["_db_rec"][p.key])
        else:
            for p in args:
                setattr(self,p,args[p])


class CeramicCapacitor(PartType):
    def __init__(self, **args):
        self.__dict__["partType"] = "CeramicCapacitor"
        self.__dict__["capacitance"] = Parameter("capacitance", "Capacitance", "float", parseCapacitance, Exact(pF(1))); 
        self.__dict__["tolerance"] = Parameter("tolerance", "Tolerance", "float", parseTolerance, None)
        self.__dict__["volts"] = Parameter("volts", "Voltage - Rated", "float",  parseVolts, GT(5))
        self.__dict__["package"] = Parameter("package", "Package / Case", "str", parsePackage, None)
        self.__dict__["partnumber"] = Parameter("partnumber", "Digi-Key Part Number", "str", lambda x : x, None)
        self.__dict__["price"] = Parameter("price", "Unit Price (USD)", "float", parsePrice, None)
        self.__dict__["stock"] = Parameter("stock", "Stock", "str", lambda x : x, None)
        self.__dict__["db"] = Parameter("db", "db", "str", lambda x : x, None)
        self.__dict__["minQty"] =  Parameter("minQty", "Minimum Quantity", "int", parseQty, Exact(1))
        self.__dict__["parameters"] = [self.capacitance, self.price, self.tolerance, self.volts, self.package, self.partnumber, self.db]
        
        if "_db_rec" in args:
            for p in self.parameters:
                if p.key in args["_db_rec"]:
                    p.value = p.parse(args["_db_rec"][p.key])
        else:
            for p in args:
                setattr(self,p,args[p])


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
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resistor Library Test")
    parser.add_argument("--ohms", required=True,  type=str, nargs=1, dest='ohms', help="Spec for device list to build")
    parser.add_argument("--ceramics", required=True,  type=str, nargs=1, dest='ceramics', help="Spec for device list to build")
    args = parser.parse_args()
    
    # define a resolution environment. It's a map between part type names and
    # tuples.  The first entry of the tuble is a database of parts of that
    # type.  The entry of the tuple is a list priorities for selecting a part.
    # In this case, we prefer 0805 to 0603 to through hole, 10% over 5%, lower
    # power, and low priced (prioritized in that order).

    resolver = PartResolutionEnvironment({"Resistor": (PartDB(Resistor, "Resistor", args.ohms[0]),
                                                       [Prefer("stock", ["onhand", "stardardline", "nonstock"]),
                                                        Prefer("package", ["0805", "0603", "TH"]),
                                                        Prefer("tolerance", [0.1, 0.05]),
                                                        Minimize("watts"),
                                                        Minimize("price")]),
                                          "CeramicCapacitor": (PartDB(CeramicCapacitor, "CeramicCapacitor", args.ceramics[0]),
                                                               [Prefer("stock", ["onhand", "stardardline", "nonstock"]),
                                                                Prefer("package", ["0805", "0603", "TH"]),
                                                                Minimize("price")])
                                          })
    
    # A 1K resistor that can disapate at least 0.5W
    highWatt = Resistor()
    highWatt.resistance.value = Exact(1000)
    highWatt.watts.value = GT(0.5)

    # A 1K resistor that can disapate at least 0.125W (and fancy args)
    lowWatt = Resistor(resistance=Exact(1000),
                       watts=GT(0.125))
    
    # A high tolerance 1K resistor
    tightTolerance = Resistor(resistance = Exact(1000))
    tightTolerance.tolerance = LT(0.01)
    
    print "high watt"
    print resolver.resolve(highWatt)
    print "low watt"
    print resolver.resolve(lowWatt)
    print "tight tolerance"
    print resolver.resolve(tightTolerance)

    print "10 pF Cap"
    c = CeramicCapacitor(capacitance=Exact(pF(10)))
    print c
    print resolver.resolve(c)

    print "Approximately 17 pF Cap"
    c = CeramicCapacitor(capacitance=Approx(pF(17)))
    print c
    print resolver.resolve(c)
