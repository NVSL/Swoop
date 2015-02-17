#!/usr/bin/env python
import argparse
from EagleUtil import *
from HighEagle import *
import sys
import re
import shutil

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge library into an eagle file")
    parser.add_argument("--src", required=True,  type=str, nargs=1, dest='src', help="libraries to merge into the other file")
    parser.add_argument("--dst", required=True,  type=str, nargs=1, dest='dst', help="the other file (sch, lbr, or pcb)")
    args = parser.parse_args()

    m = re.match("(.*\.(lbr|sch|pcb))(:(.+))?", args.src[0])
    if m is None:
        raise HighEagleError("Unparsable file name: '" + args.src[0] + "'")

    f = m.group(1)
    srcLib = m.group(4)
    suffix=m.group(2)

    if suffix == "sch":
        src = Schematic.from_file(f)
        srcLib = dst.get_library(srcLib)
    elif suffix == "brd":
        raise NotImplementedError("brd files not supported yet")
    elif suffix == "lbr":
        src = LibraryFile.from_file(f)
        srcLib = src.get_library()
    else:
        raise Exception("File with unknown suffix: " + suffix);    

    ####################################################################

    m = re.match("(.*\.(lbr|sch|pcb))(:(.+))?", args.dst[0])
    if m is None:
        raise HighEagleError("Unparsable file name: '" + args.dst[0] + "'")

    f = m.group(1)
    dstLib = m.group(4)
    suffix=m.group(2)

    shutil.copy(f, f + ".bak")

    if suffix == "sch":
        dst = Schematic.from_file(f)
        dstLib = dst.get_library(dstLib)

        #for p in dst.get_parts().values():
        #    if re.match("^GENERIC-(CAPACITOR-NP|CAPACITOR-POL|DIODE-LED|DIODE-SCHOTTKY|DIODE-ZENER|RESISTOR|RESONATOR)", p.deviceset) is not None:
        #        print "Scubbed " + p.name
        #        p.device = ""
                        

    elif suffix == "brd":
        raise NotImplementedError("brd files not supported yet")
    elif suffix == "lbr":
        dst = LibraryFile.from_file(f)
        dstLib = dst.get_library()
    else:
        raise Exception("File with unknown suffix: " + suffix);    

    for i in srcLib.symbols.values():
        dstLib.add_symbol(i.clone())
    for i in srcLib.packages.values():
        dstLib.add_package(i.clone())
    for i in srcLib.devicesets.values():
#        if re.match("^(GENERIC|RESOLVED|UNRESOLVED)-(CAPACITOR-NP|CAPACITOR-POL|DIODE-LED|DIODE-SCHOTTKY|DIODE-ZENER|RESISTOR|RESONATOR)", i.name) is not None:
 #           print "copying " + i.name
        dstLib.add_deviceset(i.clone())

    
        
    dst.write(f)
