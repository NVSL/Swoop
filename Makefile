
default: build test

build: eagleDTD.py

TARGETS=test2.th.resolved.sch Xperimental_Trinket_Pro_small_parts_power_breakout.th.resolved.sch Xperimental_Trinket_Pro_small_parts_power_breakout.handsolder.resolved.sch Xperimental_Trinket_Pro_small_parts_power_breakout.small.resolved.sch 

test: build $(TARGETS)  eagleDTD.py
	python ./HighEagleTest.py --layers NVSLLayers.lbr
	#python ./PartResolutionTest.py $(PARTS)
	python QueryParseTest.py
	./checkEagle.py --file $(TARGETS)

#%.resolved.sch: %.sch eagleDTD.py
#	python picker.py --in $<  --out $@  --goal handsolder --lbr out.lbr

%.th.resolved.sch: %.sch eagleDTD.py 
	python picker.py --in $<  --out $@  --goal th 

%.small.resolved.sch: %.sch eagleDTD.py 
	python picker.py --in $<  --out $@  --goal small

%.handsolder.resolved.sch: %.sch eagleDTD.py 
	python picker.py --in $<  --out $@  --goal handsolder

eagleDTD.py: eagle-tweaked.dtd
	echo DTD=\"\"\" > $@
	cat $< >> $@
	echo \"\"\" >> $@


clean:
	rm -rf *resolved.sch
	rm -rf eagleDTD.py
	rm -rf $(TARGETS)
	rm -rf *.broken.xml
