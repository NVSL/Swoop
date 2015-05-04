#!/usr/bin/env python

import Swoop
import argparse
import shutil
import SwoopTools
import sys
import CleanupEagle
        
def main(argv):
    parser = argparse.ArgumentParser(description="Remove unused library items from a schematic or board.")
    parser.add_argument("--file", required=True,  type=str, nargs='+', dest='file', help="files to process")
    parser.add_argument("--out", required=True,  type=str, nargs='+', dest='out', help="output file")
    args = parser.parse_args(argv)
    
    ef = Swoop.EagleFile.from_file(args.file[0])

    CleanupEagle.removeDeadEFPs(ef)

    ef.write(args.out[0])
    
if __name__ == "__main__":
    main(sys.argv[1:])
    
