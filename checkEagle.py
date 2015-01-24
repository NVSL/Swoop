#!/usr/bin/env python

import HighEagle as HE
import argparse
import shutil
from lxml import etree as ET
import sys
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check whether eagle files are dtd conforming")
    parser.add_argument("--file", required=True,  type=str, nargs='+', dest='file', help="files to process")
    parser.add_argument("-q", "--quiet", required=False,  default=False, action="store_true", dest='quiet', help="supress output")
    
    args = parser.parse_args()

    passed = True
    for i in args.file:
        if not args.quiet:
            print "Validating " + i + ": ",
        if i[-3:] in ".sch":
            f = HE.Schematic.from_file(i)
        elif i[-3:] in ".brd":
            raise NotImplementedError("brd files not supported yet")
            #shutils.copy(i, i + ".bak")
        elif i[-3:] in ".lbr":
            f = HE.LibraryFile.from_file(i)
        else:
            raise Exception("File with unknown suffix: " + i);    
        
        if f.validate():
            if not args.quiet:
                print "valid"
        else:
            passed = False
            if not args.quiet:
                print "invalid"

    if passed:
        sys.exit(0)
    else:
        sys.exit(1)
