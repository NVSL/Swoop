#!/usr/bin/env python

import HighEagle as HE
import argparse
import shutil

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix eagle files to make them dtd conforming")
    parser.add_argument("--file", required=True,  type=str, nargs='+', dest='file', help="files to process")
    args = parser.parse_args()
    
    for i in args.file:
        if i[-3:] in ".sch":
            shutil.copy(i, i + ".bak")
            loaded_schematic = HE.Schematic.from_file(i)
            loaded_schematic.write(i)
        elif i[-3:] in ".brd":
            raise NotImplementedError("brd files not supported yet")
            #shutils.copy(i, i + ".bak")
        elif i[-3:] in ".lbr":
            shutil.copy(i, i + ".bak")
            loaded_lbr = HE.LibraryFile.from_file(i)
            loaded_lbr.write(i)
        else:
            raise Exception("File with unknown suffix: " + i);    
        
