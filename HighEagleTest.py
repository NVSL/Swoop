import HighEagle as HE

print "Making empty schematic."
print
schematic = HE.Schematic()
print

print "Exporting empty schematic."
print
schematic.write("test.sch")
print

filename = "Adafruit-Trinket-5V.sch"
print "Loading", filename
print
loaded_schematic = HE.Schematic.from_file(filename)
print