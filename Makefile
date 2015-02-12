
default: build test

build: eagleDTD.py Resolver.lbr

PARTS=--ohms ../../Libraries/Parts/Digikey/Resistors-{0805,0603,TH}.csv --ceramics ../../Libraries/Parts/Digikey/Capacitors-{Ceramic0805,Ceramic0603,CeramicTH,TantalumSMD,TantalumTH,Extras}.csv --leds ../../Libraries/Parts/Digikey/LEDs-{0805,0603,TH}.csv --zdiodes ../../Libraries/Parts/Digikey/Zener-Diodes-{TH,SMD}.csv  --sdiodes ../../Libraries/Parts/Digikey/Schottky-Diodes-{TH,SMD}.csv --resonators ../../Libraries/Parts/Digikey/Resonators-{SMD,TH}.csv

test: build test2.th.resolved.sch Xperimental_Trinket_Pro_small_parts_power_breakout.th.resolved.sch Xperimental_Trinket_Pro_small_parts_power_breakout.handsolder.resolved.sch Xperimental_Trinket_Pro_small_parts_power_breakout.small.resolved.sch eagleDTD.py
	python ./HighEagleTest.py
	python ./PartResolutionTest.py $(PARTS)
	python QueryParseTest.py
	./buildResolverParts.py --lbr Base.lbr --out out.lbr
	./checkEagle.py --file *.sch *.lbr

%.resolved.sch: %.sch eagleDTD.py
	python picker.py --in $<  --out $@ $(PARTS) --goal handsolder --lbr newNVSL.lbr

%.th.resolved.sch: %.sch eagleDTD.py
	python picker.py --in $<  --out $@ $(PARTS) --goal th --lbr newNVSL.lbr

%.small.resolved.sch: %.sch eagleDTD.py
	python picker.py --in $<  --out $@ $(PARTS) --goal small --lbr newNVSL.lbr

%.handsolder.resolved.sch: %.sch eagleDTD.py
	python picker.py --in $<  --out $@ $(PARTS) --goal handsolder --lbr newNVSL.lbr

eagleDTD.py: eagle-tweaked.dtd
	echo DTD=\"\"\" > $@
	cat $< >> $@
	echo \"\"\" >> $@

Resolver.lbr: Base.lbr
	./buildResolverParts.py --lbr $< --out $@

clean:
	rm -rf *resolved.sch
	rm -rf eagleDTD.py
	rm -rf Resolver.lbr

