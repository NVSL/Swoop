
default: build test

build: eagleDTD.py

test: build
	python ./HighEagleTest.py
	python ./PartResolutionTest.py --ohms ../../Libraries/Parts/Digikey/Resistors-{0805,0603,TH}.csv --ceramics ../../Libraries/Parts/Digikey/Capacitors-{Ceramic0805,Ceramic0603,CeramicTH,TantalumSMD,TantalumTH,Extras}.csv
	python picker.py --in Xperimental_Trinket_Pro_small_parts_power_breakout.sch  --out Xperimental_Trinket_Pro_small_parts_power_breakout.resolved.sch --ohms ../../Libraries/Parts/Digikey/Resistors-{0805,0603,TH}.csv --ceramics ../../Libraries/Parts/Digikey/Capacitors-{Ceramic0805,Ceramic0603,CeramicTH,TantalumSMD,TantalumTH,Extras}.csv --leds ../../Libraries/Parts/Digikey/LEDs-{0805,0603,TH}.csv  --lbr newNVSL.lbr --zdiodes ../../Libraries/Parts/Digikey/Zener-Diodes-{TH,SMD}.csv  --sdiodes ../../Libraries/Parts/Digikey/Schottky-Diodes-{TH,SMD}.csv --goal handsolder
	python QueryParseTest.py
	./buildResolverParts.py --lbr Base.lbr --out out.lbr
	./checkEagle.py --file *.sch *.lbr

eagleDTD.py: eagle-tweaked.dtd
	echo DTD=\"\"\" > $@
	cat $< >> $@
	echo \"\"\" >> $@