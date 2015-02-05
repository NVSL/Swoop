import re
from Units import *

def parseESR(r):
    r = r.upper()
    m = re.match("(\d+(\.\d+)?) Ohm", r);
    if m is None:
        raise Exception("Can't parse resistance: '" + r + "'")
    return float(m.group(1))

def parseResistance(r):
    r = r.upper()
    m = re.match("(\d+(\.\d+)?)(.?)", r);
 #   print "s = " + r
    if m is None:
        raise Exception("Can't parse resistance: '" + r + "'")
#    print "m = " + m.group(3)
    if m.group(3) is "":
        mult = 1.0
    elif m.group(3) is "K":
        mult = 1000.0
    elif m.group(3) is "M":
        mult = 1000000.0
    else:
        raise Exception("Can't parse resistance: '" + r + "'")

    return mult * float(m.group(1))


def parseTolerance(r):
    r = r.upper()
    if r == "JUMPER":
        return 0.01
    m = re.search("(\d+)%", r);
    if m is None:
        raise Exception("Can't parse tolerance: '" + r + "'")
#    if m is None:
#        print "Can't parse tolerance: " + r + "; setting to 20%"
#        return 0.2
    return float(m.group(1))/100.0

def parseVolts(r):
    r = r.upper()
    m = re.search("(\d+(\.\d+)?)V", r);
    if m is None:
        raise Exception("Can't parse volts: '" + r + "'")
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
        raise Exception("Can't parse package: '" + r + "'")
    
def parseWatts(r):
    r = r.upper()
    m = re.match("(\d+(.\d+)?)W", r);
    if m is None:
        raise Exception("Can't parse Watts: '" + r + "'")
    return float(m.group(1))

def parseQty(r):
    r = r.upper()
    m = re.match("(\d+)", r);
    if m is not None:
        return int(m.group(1))
    else:
        raise Exception("Can't parse qty: '" + r + "'")

def parsePrice(r):
    r = r.upper()
    m = re.match("(\d+.\d+)", r);
    if m:
        return float(m.group(1))
    elif r == "CALL":
        return 1000
    else:
        raise Exception("Can't parse price: " + r)
    
def parseCapacitance(r):
    r = r.upper()
    m = re.match("(\d+(\.\d+)?).?([PU]F?)", r);

    if m is None:
        raise Exception("Can't parse capacitance: '" + r + "'")

    if m.group(3) == "PF":
        mult = pF(1)
    elif m.group(3) == "UF":
        mult = uF(1)
    else:
        raise Exception("Can't parse capacitance: '" + r + "'")

    return mult * float(m.group(1))

def parseNanometer(r):
    r = r.upper()
    m = re.match("((\d+)NM)|\d+K", r);

    if m is None:
        raise Exception("Can't parse nanometer: '" + r + "'")

    if m.group(1) is not None:
        return float(m.group(2))
    else:
        return None

def parseMillicandela(r):
    r = r.upper()
    m = re.match("(\d+(\.\d+)?)MCD", r);

    if m is None:
        raise Exception("Can't parse millicandela: '" + r + "'")

    return float(m.group(1))

def parseAmps(r):
    r = r.upper()
    m = re.match("(\d+(\.\d+)?)([MU]A)", r);

    if m is None:
        raise Exception("Can't parse amps: '" + r + "'")

    if m.group(3) == "MA":
        mult = mA(1)
    elif m.group(3) == "UA":
        mult = uA(1)
    else:
        raise Exception("Can't parse amps: '" + r + "'")

    return mult * float(m.group(1))
