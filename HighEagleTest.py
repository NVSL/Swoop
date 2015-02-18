#!/usr/bin/env python

import HighEagle as HE

import argparse
import EagleTools

parser = argparse.ArgumentParser(description="Fix eagle files to make them dtd conforming")
parser.add_argument("--layers", required=False,  type=str, nargs=1, dest='layers', help="If present, add these layers")
args = parser.parse_args()

layers = HE.LibraryFile.from_file(args.layers[0])

print "Making empty schematic."
print
schematic = HE.Schematic()
EagleTools.normalizeLayers(schematic, layers)
print

print "Exporting empty schematic."
print
schematic.write("empty.sch")
print

filename = "Trinket_TH_thru_parts_power_breakout.sch"
print "Loading", filename
print
loaded_schematic = HE.Schematic.from_file(filename)
print

print "Exporting loaded file."
print 
loaded_schematic.write("test_load.sch")

filename = "newNVSL.lbr"
print "Loading", filename
print
loaded_lbr = HE.LibraryFile.from_file(filename)
print

print "Exporting loaded file."
print 
loaded_lbr.write("test_load.lbr")
