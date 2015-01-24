#!/usr/bin/env python
import argparse

from PartResolutionEnvironment import *
from Resistor import Resistor
from Capacitor import CeramicCapacitor
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
    parser.add_argument("--ohms", required=True,  type=str, nargs=1, dest='ohms', help="Resistors csv")
    parser.add_argument("--ceramics", required=True,  type=str, nargs=1, dest='ceramics', help="ceramic caps csv")
    parser.add_argument("--lbr", required=True,  type=str, nargs=1, dest='lbr', help="libraries to draw from")
    parser.add_argument("--in", required=True,  type=str, nargs=1, dest='inSch', help="input sch")
    parser.add_argument("--out", required=True,  type=str, nargs=1, dest='outSch', help="output sch")

    args = parser.parse_args()

    # define a resolution environment. It's a map between part type names and
    # tuples.  The first entry of the tuple is a database of parts of that
    # type.  The entry of the tuple is a list priorities for selecting a part.
    # In this case, we prefer 0805 to 0603 to through hole, 10% over 5%, lower
    # power, and low priced (prioritized in that order).

    resistors = PartResolutionEnvironment("Resistor", 
                                          db=PartDB(Resistor, "Resistor", args.ohms[0]),
                                          preferences=[Prefer("STOCK", ["onhand", "stardardline", "nonstock"]),
                                                       Prefer("CASE", ["0805", "0603", "TH"]),
                                                       Prefer("TOL", [0.1, 0.05]),
                                                       Minimize("PWR"),
                                                       Minimize("PRICE")])
    
    ceramicCaps = PartResolutionEnvironment("CeramicCapacitor",
                                            db=PartDB(CeramicCapacitor, "CeramicCapacitor", args.ceramics[0]),
                                            preferences=[Prefer("STOCK", ["onhand", "stardardline", "nonstock"]),
                                                         Prefer("CASE", ["0805", "0603", "TH"]),
                                                         Minimize("PRICE")])

    resolverMap = {"GENERIC-RESISTOR_":resistors}

    # print ParameterQuery.parse("[4, 10]")
    # print ParameterQuery.parse("[4.2, 10]")
    # print ParameterQuery.parse("[4, -1.0]")
    # print ParameterQuery.parse("[-4 , 10]")
    # print ParameterQuery.parse("[ 4,10 ]")
    # print ParameterQuery.parse("[ 4,10 ] ")
    # print ParameterQuery.parse(" [ 4,10 ] ")
    # print ParameterQuery.parse(" [ 4, 10 ]")
    # print ParameterQuery.parse(" [ 4, 10 ] aoeu")
    # print ParameterQuery.parse(" [ 4, 10 ]")
    # print ParameterQuery.parse("<4")
    # print ParameterQuery.parse("<=4")
    # print ParameterQuery.parse("<=4.0")
    # print ParameterQuery.parse("<=-4.0")
    # print ParameterQuery.parse(">=-4.0")
    # print ParameterQuery.parse(">=4.0")
    # print ParameterQuery.parse("4.0")
    # print ParameterQuery.parse("10 +/- 14%")
    # sys.exit()

    sch = Schematic.from_file(args.inSch[0])
    lbr = LibraryFile.from_file(args.lbr[0])

    sch.add_library(lbr.get_library_copy())

    for i in sch.get_parts().values():
        resolver = resolverMap.get(i.get_deviceset().name)
        if resolver is not None:
            #print i
            print i.name 
            #print [(k.name, k.value) for k in i.get_attributes().values() ]
            r = Resistor();
            for a in i.get_attributes().values():
                if a.name in r.parameters and a.value is not "":
                    #print "here" + field
                    q = ParameterQuery.parse(str(a.value))
                    if q is None:
                        print "Couldn't parse " + a.value
                    else:
                        r.setField(field, q)

            if i.value is not "":
                q = ParameterQuery.parse(str(i.value))
                if q is None:
                    print "Couldn't parse " + i.value
                else:
                    r.setField("VALUE", q)

            print r
            if resolver.resolveInPlace(r) is not None:
                print r
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
            else:
                i.set_device(deviceset=i.get_deviceset().name.replace("GENERIC","UNRESOLVED"))

            r = None

 
    sch.write(args.outSch[0])
