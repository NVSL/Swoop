import re

def pF(x):
    return x * 1e-12

def uF(x):
    return x * 1e-6

def mA(x):
    return x * 1e-3

def mV(x):
    return x * 1e-3

def uA(x):
    return x * 1e-6

def F(x):
    return x

def M(x):
    return 1e6*x

def k(x):
    return 1e3*x

def mW(x):
    return 1e-3*x

def MHz(x):
    return x * 1e6

def KHz(x):
    return x * 1e3

def GHz(x):
    return x * 1e9

def M(x):
    return x * 1e6

def K(x):
    return x * 1e3

def G(x):
    return x * 1e9


def p(x):
    return x * 1e-12

def n(x):
    return x * 1e-9

def u(x):
    return x * 1e-6

def m(x):
    return x * 1e-3



def trimPointZero(x):
    m = re.search("(.*)\.0+$",str(x))
    if m:
        return m.group(1)
    else:
        return str(x)

def renderOhms(x):
    if x < k(1):
        return trimPointZero(x)
    elif x <= M(1):
        return trimPointZero(x/k(1)) + "K"
    elif x <= G(1):
        return trimPointZero(x/M(1)) + "M"
    else:
        return trimPointZero(x/G(1)) + "G"
        

def renderFarads(x):
    if x < u(1)/100:
        return trimPointZero(x/p(1)) + "pF"
#    elif x <= u(1):
#        return trimPointZero(x/n(1)) + "nF"
    elif x <= 1:
        return trimPointZero(x/u(1)) + "uF"
    else:
        return trimPointZero(x) + "F"
        
def renderVolts(x):
    if x < 1:
        return trimPointZero(x/m(1)) + "mV"
    else:
        return trimPointZero(x) + "V"
        
def renderHz(x):
    if x <= k(1):
        return trimPointZero(x) + "Hz"
    elif x <= M(1):
        return trimPointZero(x/K(1)) + "KHz"
    elif x <= G(1):
        return trimPointZero(x/M(1)) + "MHz"
    else:
        return trimPointZero(x/G(1)) + "GHz"
        
def renderWatts(x):
    if x < 1:
        return trimPointZero(x/m(1)) + "mW"
    else:
        return trimPointZero(x) + "W"

def renderAmps(x):
    if x < m(1):
        return trimPointZero(x/u(1)) + "uA"
    elif x < 1:
        return trimPointZero(x/m(1)) + "mA"
    else:
        return trimPointZero(x) + "A"


def renderTolerance(x):
    return str(trimPointZero(x*100)) + "%"

