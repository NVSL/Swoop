import HighEagle as HE

print "Making empty schematic."
print
schematic = HE.Schematic()
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
