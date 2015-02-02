#!/usr/bin/env python

import HighEagle as HE
import argparse
import shutil

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix eagle files to make them dtd conforming")
    parser.add_argument("--file", required=True,  type=str, nargs='+', dest='file', help="files to process")
    parser.add_argument("--layers", required=False,  type=str, nargs=1, dest='layers', help="If present, add these layers")
    args = parser.parse_args()
    
    if args.layers:
        layers = HE.LibraryFile.from_file(args.layers[0])

    for i in args.file:
        if i[-3:] in ".sch":
            shutil.copy(i, i + ".bak")
            sch = HE.Schematic.from_file(i)
            if args.layers:
                sch.mergeLayersFromEagleFile(layers, force=True)
            sch.write(i)
            
        elif i[-3:] in ".brd":
            raise NotImplementedError("brd files not supported yet")
            #shutils.copy(i, i + ".bak")
        elif i[-3:] in ".lbr":
            shutil.copy(i, i + ".bak")
            lbr = HE.LibraryFile.from_file(i)
            if args.layers:
                lbr.mergeLayersFromEagleFile(layers, force=True)
            lbr.write(i)
        else:
            raise Exception("File with unknown suffix: " + i);    
        
