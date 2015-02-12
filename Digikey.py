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
    m = re.search("((\d+(\.\d+)?)(M)?)V( @ (\d+m?A))?", r);
    if m is None:
        raise Exception("Can't parse volts: '" + r + "'")

    if m.group(4) == "M":
        multiplier = mV(1)
    elif m.group(4) is None:
        multiplier = 1.0
    else:
        raise Exception("Can't parse volts: '" + r + "'")
    #print r
    #print m.group(2)
    return float(m.group(2)) * multiplier

def parseSize(r):
    r = r.upper()
    sizeMap = {"0805": "large",
               "0805 (2012 METRIC)": "large",
               "805": "large",
               "0603": "small",
               "0603 (1608 METRIC)": "small",
               "603": "small",
               "1206 (3216 METRIC)": "large",
               "1210 (3528 METRIC)": "large",
               "0805 (2012 Metric)": "large",
               "2312 (6032 METRIC)": "large",
               "2917 (7343 METRIC)": "large",
               "T-18, AXIAL": "TH",
               "DO-41": "TH",
               "AXIAL": "TH",
               "RADIAL": "TH",
               "DO-204AL, DO-41, AXIAL" : "TH",
               "DO-201AD, AXIAL": "TH",
               "SOD-323": "large",
               "SC-76, SOD-323": "large",
               "SOD-123F":"large",
               "S-FLAT (1.6X3.5)": "large",
               "3-SMD, NON-STANDARD" : "large",
               "RADIAL - 3 LEAD, 2.50MM PITCH" : "TH"
               }
    try:
        return sizeMap[r]
    except Exception as e:              
        raise Exception("Unknown package: '" + r + "'")


               
def parsePackage(r):
    r = r.upper()
    if re.search("0?805", r):
        return "0805"
    elif re.search("0?603", r):
        return "0603"
    elif re.search("1206", r):
        return "1206"
    elif re.search("1210", r):
        return "1210"
    elif re.search("2917", r):
        return "2917"
    elif re.search("AXIAL", r):
        return "TH"
    elif re.search("RADIAL", r):
        return "TH"
    elif re.search("DO-201AD", r):
        return "TH"
    elif re.search("DO-41", r):
        return "TH"
    elif re.search("SOD-323", r):
        return "SOD-323"
    elif r == "3-SMD, NON-STANDARD":
        return "3-SMD, NON-STANDARD"
    elif r == "S-FLAT (1.6X3.5)":
        return "SOD-123F"
    else:
        raise Exception("Can't parse package: '" + r + "'")
    
def parseWatts(r):
    r = r.upper()
    m = re.match("(\d+(.\d+)?)([M]?W)", r);
    if m is None:
        raise Exception("Can't parse Watts: '" + r + "'")

    if m.group(3) == "MW":
        mult = mW(1)
    elif m.group(3) == "W":
        mult = 1.0
    else:
        raise Exception("Can't parse Watts: '" + r + "'")

    return float(m.group(1)) * mult

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

def parseFrequency(r):
    r = r.upper()
    m = re.match("(\d+(\.\d+)?).?([MK]HZ?)", r);

    if m is None:
        raise Exception("Can't parse frequency: '" + r + "'")

    if m.group(3) == "MHZ":
        mult = MHz(1)
    elif m.group(3) == "KHZ":
        mult = KHz(1)
    else:
        raise Exception("Can't parse capacitance: '" + r + "'")

    return mult * float(m.group(1))

def parseNanometer(r):
    r = r.upper()
    m = re.match("((\d+(.\d+))NM)|(\d+K)", r);
#    print m
 #   print r
    if m is None:
        raise Exception("Can't parse nanometer: '" + r + "'")

    if m.group(1) is not None:
        return float(m.group(2))
    else:
        return "unknown"

def parseNanoseconds(r):
    r = r.upper()
    m = re.match("((\d+)NS)|(-)", r);

    if m is None:
        raise Exception("Can't parse nanoseconds: '" + r + "'")

    if m.group(1) is not None:
        return float(m.group(2))
    else:
        return "unknown"

def parseMillicandela(r):
    r = r.upper()
    m = re.match("(\d+(\.\d+)?)MCD", r);

    if m is None:
        raise Exception("Can't parse millicandela: '" + r + "'")

    return float(m.group(1))

def parseAmps(r):
    r = r.upper()
    m = re.match("(\d+(\.\d+)?)([MU]?A)", r);

    if m is None:
        raise Exception("Can't parse amps: '" + r + "'")

    if m.group(3) == "MA":
        mult = mA(1)
    elif m.group(3) == "UA":
        mult = uA(1)
    elif m.group(3) == "A":
        mult = 1.0
    else:
        raise Exception("Can't parse amps: '" + r + "'")

    return mult * float(m.group(1))
