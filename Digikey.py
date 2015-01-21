import re
from Units import *

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
