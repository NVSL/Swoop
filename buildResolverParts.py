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
    parser.add_argument("--lbr", required=True,  type=str, nargs=1, dest='lbr', help="library containing input symbols, etc.")
    parser.add_argument("--out", required=True,  type=str, nargs=1, dest='outLbr', help="output sch")

    args = parser.parse_args()

    lbr = LibraryFile.from_file(args.lbr[0])

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
            
            lbr.library.add_symbol(g)
            lbr.library.add_symbol(u)
            lbr.library.add_symbol(r)
    

    for s in lbr.library.devicesets.values():
        g = re.match("_BASE-", s.name)
        if g is not None:
            for i in ["GENERIC-", "RESOLVED-", "UNRESOLVED-"]:
                n = s.clone()
                n.name = n.name.replace("_BASE-", i)
                if len(n.get_gates()) != 1:
                    raise NotImplementedError("Multiple gates not supported")
                n.gates[n.gates.keys()[0]].symbol = n.gates[n.gates.keys()[0]].symbol.replace("_BASE-", i)
                lbr.library.add_deviceset(n)

    for s in lbr.library.devicesets.values():
        if re.match("_BASE-", s.name) is not None:
            lbr.library.remove_deviceset(s)

    lbr.write(args.outLbr[0])
