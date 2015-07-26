#!/usr/bin/env python

import Swoop
import argparse
import shutil
import Swoop.tools
import GadgetronConfig

def main():
    parser = argparse.ArgumentParser(description="Fix eagle files to make them dtd conforming")
    parser.add_argument("--file", required=True,  type=str, nargs='+', dest='file', help="files to process")
    parser.add_argument("--layers", required=False, default=[GadgetronConfig.config.GADGETRON_STANDARD_LAYERS],  type=str, nargs=1, dest='layers', help="Layers to use")
    parser.add_argument("--force", required=False,  action="store_true", dest='force', help="Overwrite layers in file.")
    args = parser.parse_args()
    
    if args.layers:
        layers = Swoop.LibraryFile.from_file(args.layers[0])

    for f in args.file:

        ef = Swoop.EagleFile.from_file(f)


        if args.layers:
            Swoop.tools.normalizeLayers(ef, layers, force=args.force)
            
            
        ef.write(f)

if __name__ == "__main__":
    main()
    
