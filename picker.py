#!/usr/bin/env python
import argparse

from PartResolutionEnvironment import *
from Resistor import Resistor
from ZenerDiode import ZenerDiode
from ZenerDiode import SchottkyDiode
from Capacitor import CeramicCapacitor
from Resonator import Resonator
#from Diodes import SchottkyDiode
from LED import LED
from PartType import *
from PartDatabase import PartDB
from PartParameter import *
from ParameterQuery import *
from Units import *
from EagleUtil import *
from HighEagle import *

import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Part picker")
    parser.add_argument("--ohms", required=True,  type=str, nargs='+', dest='ohms', help="Resistors csv")
    parser.add_argument("--ceramics", required=True,  type=str, nargs='+', dest='ceramics', help="ceramic caps csv")
    parser.add_argument("--leds", required=True,  type=str, nargs='+', dest='leds', help="LED csv")
    parser.add_argument("--zdiodes", required=True,  type=str, nargs='+', dest='zdiodes', help="Zener diode csv")
    parser.add_argument("--sdiodes", required=True,  type=str, nargs='+', dest='sdiodes', help="Schottky diode csv")
    parser.add_argument("--resonators", required=True,  type=str, nargs='+', dest='resonators', help="Resonators csv")
    parser.add_argument("--lbr", required=True,  type=str, nargs=1, dest='lbr', help="libraries to draw from")
    parser.add_argument("--in", required=True,  type=str, nargs=1, dest='inSch', help="input sch")
    parser.add_argument("--out", required=True,  type=str, nargs=1, dest='outSch', help="output sch")
    parser.add_argument("--goal", required=True,  type=str, nargs=1, dest='goal', help="part selection goal")

    args = parser.parse_args()

    # define a resolution environment. It's a map between part type names and
    # tuples.  The first entry of the tuple is a database of parts of that
    # type.  The entry of the tuple is a list priorities for selecting a part.
    # In this case, we prefer 0805 to 0603 to through hole, 10% over 5%, lower
    # power, and low priced (prioritized in that order).
    
    strategies = {"small": Prefer("SIZE", ["small", "large", "TH"]),
                  "handsolder" :  Prefer("SIZE", ["large", "small", "TH"]),
                  "th" : Prefer("SIZE", ["TH", "large", "small"])}
    
    sizePref = strategies[args.goal[0]]
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

    leds = PartResolutionEnvironment("LED",
                                     db=PartDB(LED, "LED", args.leds),
                                     preferences=[Prefer("STOCK", ["STOCK", "SPECIAL-ORDER"]),
                                                  sizePref,
                                                  Minimize("PRICE")])

    zennerDiodes = PartResolutionEnvironment("ZenerDiode",
                                             db=PartDB(ZenerDiode, "ZenerDiode", args.zdiodes),
                                             preferences=[Prefer("STOCK", ["STOCK", "SPECIAL-ORDER"]),
                                                          sizePref,
                                                          Minimize("PRICE")])

    schottkyDiodes = PartResolutionEnvironment("SchottkyDiode",
                                               db=PartDB(SchottkyDiode, "SchottkyDiode", args.sdiodes),
                                               preferences=[Prefer("STOCK", ["STOCK", "SPECIAL-ORDER"]),
                                                            sizePref,
                                                            Minimize("PRICE")])

    resonators = PartResolutionEnvironment("Resonator",
                                           db=PartDB(Resonator, "Resonator", args.resonators),
                                           preferences=[Prefer("STOCK", ["STOCK", "SPECIAL-ORDER"]),
                                                        sizePref,
                                                        Minimize("PRICE")])
    
    resolverMap = {
        "GENERIC-RESISTOR_":resistors,
        "GENERIC-CAPACITOR-NP_": ceramicCaps,
        "GENERIC-DIODE-LED_": leds,
        "GENERIC-DIODE-ZENER_": zennerDiodes,
        "GENERIC-DIODE-SCHOTTKY_": schottkyDiodes,
        "GENERIC-RESONATOR_": resonators
        }


    sch = Schematic.from_file(args.inSch[0])
    lbr = LibraryFile.from_file(args.lbr[0])

    sch.mergeLayersFromEagleFile(lbr)

    sch.add_library(lbr.get_library_copy())

    partCount = 0
    unresolved = []
    resolved = []
    for i in sch.get_parts().values():
        resolver = resolverMap.get(i.get_deviceset().name)
        partCount = partCount + 1
        if resolver is not None:
            #print i
            #print i.name 
            #print [(k.name, k.value) for k in i.get_attributes().values() ]
            #print resolver
            r = resolver.db.partType()
            #print str(r)
            for a in i.get_attributes().values():
                if a.name in r.parameters and a.value is not "":
                    #print "here" + field
                    #print str(a)
                    q = ParameterQuery.parse(r.parameters[a.name].type, str(a.value))
                    if q is None:
                        raise Exception("Couldn't parse '" + a.value + "' for part '" + i.name + "'")
                    else:
                        r.setField(a.name, q)
                        
            #print str(i.get_attributes())
            if i.value is not "":
                q = ParameterQuery.parse(r.parameters["VALUE"].type,str(i.value))
                if q is None:
                    raise Exception("Couldn't parse '" + i.value + "' for part '" + i.name + "'")
                else:
                    r.setField("VALUE", q)

            #print r
            if resolver.resolveInPlace(r) is not None:
                #print r
                # print resolved
                # ET.dump(i.get_et())
                for a in i.get_attributes().values():
                    # field = Resistor.attrToField(a.name)
                    # print "=="
                    # print field
                    if a.name in r.parameters:
                        a.value = r.getField(a.name)
                        # print a.name
                        # print a.value
                        # print r.getField(field)
                i.value = r.getField("VALUE")
                i.set_device(deviceset=i.get_deviceset().name.replace("GENERIC","RESOLVED"))
                resolved.append(str(r))
            else:
                unresolved.append(i)
                i.set_device(deviceset=i.get_deviceset().name.replace("GENERIC","UNRESOLVED"))

            r = None
    print str(len(resolved)) + " resolved parts."
    for r in resolved:
        print r

    print str(len(unresolved)) + " unresolved parts."
    for u in unresolved:
        print u.name


    sch.write(args.outSch[0])
