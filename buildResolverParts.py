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
    parser = argparse.ArgumentParser(description="Generate libraries for part resolution")
    parser.add_argument("--baselib", required=True,  type=str, nargs=1, dest='baselib', help="input base library")
    parser.add_argument("--designlib", required=True,  type=str, nargs=1, dest='designlib', help="Output library with parts to be used for design.")
    parser.add_argument("--buildlib", required=True,  type=str, nargs=1, dest='buildlib', help="Output libbray with resolved/unresolved parts.")

    args = parser.parse_args()

    lbr = LibraryFile.from_file(args.baselib[0])
    designLib = LibraryFile.from_file(args.baselib[0])
    buildLib = LibraryFile.from_file(args.baselib[0])

    # Build symbols
    for s in lbr.library.symbols.values():
        g = re.match("_BASE-", s.name) 
        if g is not None:

            g = s.clone()
            g.name = s.name.replace("_BASE-", "GENERIC-")
            for x in g.drawingElements:
                if x.layer == "Unresolved":
                    x.layer = "Generic"
                    x.width = "0.2"
            
            u = s.clone()
            u.name = s.name.replace("_BASE-", "UNRESOLVED-")

            r = s.clone()
            r.name = s.name.replace("_BASE-", "RESOLVED-")

            for x in r.drawingElements:
                if x.layer == "Unresolved":
                    x.layer = "Resolved"
                    x.width = "0.2"
            
            designLib.library.add_symbol(g)
            buildLib.library.add_symbol(u)
            buildLib.library.add_symbol(r)
    
    for s in lbr.library.devicesets.values():
        g = re.match("_BASE-", s.name)
        if g is not None:
            for i in ["GENERIC-", "RESOLVED-", "UNRESOLVED-"]:
                n = s.clone()
                n.name = n.name.replace("_BASE-", i)
                if len(n.get_gates()) != 1:
                    raise NotImplementedError("Multiple gates not supported")
                n.gates[n.gates.keys()[0]].symbol = n.gates[n.gates.keys()[0]].symbol.replace("_BASE-", i)
                if i != "RESOLVED-":
                    n.convertToExternal()
                    
                if i in ["UNRESOLVED-", "RESOLVED-"]:
                    buildLib.library.add_deviceset(n)
                else:
                    designLib.library.add_deviceset(n)
        else:
            raise Exception("Found device set with name not beginning with '_BASE' in base library '" + args.baselib[0] + "'")

    for lbr in [designLib, buildLib]:
        for s in lbr.library.devicesets.values():
            if re.match("_BASE-", s.name) is not None:
                lbr.library.remove_deviceset(s)
        for s in lbr.library.symbols.values():
            if re.match("_BASE-", s.name) is not None:
                lbr.library.remove_symbol(s)

    for p in designLib.library.packages.values():
        designLib.library.remove_package(p)
        
    designLib.write(args.designlib[0])
    buildLib.write(args.buildlib[0])
