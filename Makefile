
default: build test

build: eagleDTD.py Resolver.lbr

PARTS=--ohms ../../Libraries/Parts/Digikey/Resistors-{0805,0603,TH}.csv --ceramics ../../Libraries/Parts/Digikey/Capacitors-{Ceramic0805,Ceramic0603,CeramicTH,TantalumSMD,TantalumTH,Extras}.csv --leds ../../Libraries/Parts/Digikey/LEDs-{0805,0603,TH}.csv --zdiodes ../../Libraries/Parts/Digikey/Zener-Diodes-{TH,SMD}.csv  --sdiodes ../../Libraries/Parts/Digikey/Schottky-Diodes-{TH,SMD}.csv --resonators ../../Libraries/Parts/Digikey/Resonators-{SMD,TH}.csv

TARGETS=test2.th.resolved.sch Xperimental_Trinket_Pro_small_parts_power_breakout.th.resolved.sch Xperimental_Trinket_Pro_small_parts_power_breakout.handsolder.resolved.sch Xperimental_Trinket_Pro_small_parts_power_breakout.small.resolved.sch Resolver.lbr 

test: build $(TARGETS)  eagleDTD.py
	python ./HighEagleTest.py --layers NVSLLayers.lbr
	python ./PartResolutionTest.py $(PARTS)
	python QueryParseTest.py
	./checkEagle.py --file $(TARGETS)

#%.resolved.sch: %.sch eagleDTD.py
#	python picker.py --in $<  --out $@ $(PARTS) --goal handsolder --lbr out.lbr

%.th.resolved.sch: %.sch eagleDTD.py Resolver.lbr NVSLLayers.lbr
	python picker.py --in $<  --out $@ $(PARTS) --goal th --lbr Resolver.lbr --layers NVSLLayers.lbr

%.small.resolved.sch: %.sch eagleDTD.py Resolver.lbr NVSLLayers.lbr
	python picker.py --in $<  --out $@ $(PARTS) --goal small --lbr Resolver.lbr --layers NVSLLayers.lbr

%.handsolder.resolved.sch: %.sch eagleDTD.py Resolver.lbr NVSLLayers.lbr
	python picker.py --in $<  --out $@ $(PARTS) --goal handsolder --lbr Resolver.lbr --layers NVSLLayers.lbr

Resolver.lbr: Base.lbr
	./buildResolverLibrary.py --lbr $< --out $@

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
	rm -rf $(TARGETS)
	rm -rf *.broken.xml
