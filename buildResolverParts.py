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
 
    lbr.write(args.outLbr[0])
