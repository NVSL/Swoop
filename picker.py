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

import EagleTools
import GadgetronConfig

import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Part picker")
    parser.add_argument("--resistors", required=False,  type=str, nargs='+', default=GadgetronConfig.config.PART_PICKER_RESISTORS.split(), dest='resistors', help="Resistors csv")
    parser.add_argument("--capacitors", required=False,  type=str, nargs='+', default=GadgetronConfig.config.PART_PICKER_CAPACITORS.split(), dest='capacitors', help="Capacitors csv")
    parser.add_argument("--leds", required=False,  type=str, nargs='+', default=GadgetronConfig.config.PART_PICKER_LEDS.split(), dest='leds', help="Leds csv")
    parser.add_argument("--zenerdiodes", required=False,  type=str, nargs='+', default=GadgetronConfig.config.PART_PICKER_ZENERDIODES.split(), dest='zdiodes', help="Zener diodes csv")
    parser.add_argument("--schotkkydiodes", required=False,  type=str, nargs='+', default=GadgetronConfig.config.PART_PICKER_SCHOTKKYDIODES.split(), dest='sdiodes', help="Schotkky diodes csv")
    parser.add_argument("--resonators", required=False,  type=str, nargs='+', default=GadgetronConfig.config.PART_PICKER_RESONATORS.split(), dest='resonators', help="Resonators csv")
    parser.add_argument("--layers", required=False, type=str, nargs=1, default=[GadgetronConfig.config.CBC_STARDARD_LAYERS], dest='layers', help="lbr file with standard layers in it.")
    parser.add_argument("--lbr", required=False,  type=str, nargs=1, default=[GadgetronConfig.config.PART_PICKER_EAGLE_LIB], dest='lbr', help="library resolved parts")
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
                                          db=PartDB(Resistor, "Resistor", args.resistors),
                                          preferences=[Prefer("STOCK", ["STOCK", "SPECIAL-ORDER"]),
                                                       sizePref,
                                                       Prefer("TOL", [0.05, 0.01]),
                                                       Minimize("PWR"),
                                                       Minimize("PRICE")])
    
    ceramicCaps = PartResolutionEnvironment("CeramicCapacitor",
                                            db=PartDB(CeramicCapacitor, "CeramicCapacitor", args.capacitors),
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
    layers = LibraryFile.from_file(args.layers[0])

    # make sure the schematics layers are sane
    EagleTools.normalizeLayers(sch, layers)

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
                        if r.getField(a.name) is None:
                            raise HighEagleError("Missing parameter '" + a.name +"' for schematic part '"+ i.name + "' on library part " + str(r))
                        i.set_attribute(a.name + "_QUERY", a.value)
                        a.value = r.renderField(a.name)
                        # print a.name
                        # print a.value
                        # print r.getField(field)
                i.set_attribute("VALUE_QUERY", i.value)
                #print str(r)
                #print i.name
                i.value = r.renderField("VALUE")
                i.set_device(deviceset=i.get_deviceset().name.replace("GENERIC","RESOLVED"))


                try:
                    #print i.name +  " " + r.getField("DEVICE")
                    i.set_device(device=r.getField("DEVICE"))
                except:
                    pass
                
                resolved.append(str(r))
            else:
                unresolved.append(i)
                i.set_device(deviceset=i.get_deviceset().name.replace("GENERIC","UNRESOLVED"))

            r = None
    print str(len(resolved)) + " resolved parts."
    #for r in resolved:
    #    print r

    print str(len(unresolved)) + " unresolved parts."
    #for u in unresolved:
    #    print u.name


    sch.write(args.outSch[0])
