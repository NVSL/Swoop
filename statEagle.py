#!/usr/bin/env python

import Swoop as HE
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix eagle files to make them dtd conforming")
    parser.add_argument("--file", required=True,  type=str, nargs='+', dest='file', help="files to process")
    args = parser.parse_args()
    
    for i in args.file:
        if i[-3:] in ".sch":
            sch = HE.Schematic.from_file(i)
            print sch.get_manifest()
        elif i[-3:] in ".brd":
            raise NotImplementedError("brd files not supported yet")
            #shutils.copy(i, i + ".bak")
        elif i[-3:] in ".lbr":
            lbr = HE.LibraryFile.from_file(i)
            print lbr.get_manifest()
        else:
            raise Exception("File with unknown suffix: " + i);    
        
