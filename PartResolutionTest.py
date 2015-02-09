#!/usr/bin/env python
import argparse

from PartResolutionEnvironment import *
from Resistor import Resistor
from Capacitor import CeramicCapacitor
from PartType import *
from PartDatabase import PartDB
from PartParameter import *
from Units import *

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resistor Library Test")
    parser.add_argument("--ohms", required=True,  type=str, nargs='+', dest='ohms', help="Resistors csv")
    parser.add_argument("--ceramics", required=True,  type=str, nargs='+', dest='ceramics', help="ceramic caps csv")
    parser.add_argument("--leds", required=True,  type=str, nargs='+', dest='leds', help="LED csv")
    parser.add_argument("--zdiodes", required=True,  type=str, nargs='+', dest='zdiodes', help="Zener diode csv")
    parser.add_argument("--sdiodes", required=True,  type=str, nargs='+', dest='sdiodes', help="Schottky diode csv")
    args = parser.parse_args()

    # define a resolution environment. It's a map between part type names and
    # tuples.  The first entry of the tuple is a database of parts of that
    # type.  The entry of the tuple is a list priorities for selecting a part.
    # In this case, we prefer 0805 to 0603 to through hole, 10% over 5%, lower
    # power, and low priced (prioritized in that order).

    sizePref =  Prefer("SIZE", ["large", "small", "TH"])
                  
    
    resistors = PartResolutionEnvironment("Resistor", 
                                          db=PartDB(Resistor, "Resistor", args.ohms),
                                          preferences=[Prefer("STOCK", ["STOCK", "SPECIAL-ORDER"]),
                                                       sizePref,
                                                       Prefer("TOL", [0.05, 0.01]),
                                                       Minimize("PWR"),
                                                       Minimize("PRICE")])
    
    ceramicCaps = PartResolutionEnvironment("CeramicCapacitor",
                                            db=PartDB(CeramicCapacitor, "CeramicCapacitor", args.ceramics),
                                            preferences=[Prefer("STOCK", ["STOCK", "SPECIAL-ORDER"]),
                                                         sizePref,
                                                         Minimize("PRICE")])

    
    # A 1K resistor that can dissipate at least 0.5W
    highWatt = Resistor()
    highWatt.VALUE.value = Exact(1000)
    highWatt.PWR.value = GT(0.5)

    # A 1K resistor that can dissipate at least 0.125W (and fancy args)
    lowWatt = Resistor(VALUE=Exact(1000),
                       PWR=GT(0.125))
    
    # A high tolerance 1K resistor
    tightTolerance = Resistor(VALUE = Exact(1000))
    tightTolerance.tolerance = LT(0.01)
    
#    print "high watt"
#    print resistors.resolve(highWatt)
    print "low watt"
    print resistors.resolve(lowWatt)
    print "tight tolerance"
    print resistors.resolve(tightTolerance)

    print "10 pF Cap"
    c = CeramicCapacitor(VALUE=Exact(pF(10)))
    print c
    print ceramicCaps.resolve(c)

    print "0.1 uF Cap"
    c = CeramicCapacitor(VALUE=uF(0.1)) # if you leave off the query, it defaults to exact
    print c
    print ceramicCaps.resolve(c)

    print "Approximately 17 pF Cap"
    c = CeramicCapacitor(VALUE=Approx(pF(17)))
    print c
    print ceramicCaps.resolve(c)
