
default: build test

build: eagleDTD.py

test: build $(TARGETS)  eagleDTD.py
	python ./HighEagleTest.py --layers NVSLLayers.lbr
	./checkEagle.py --file test2.sch Xperimental_Trinket_Pro_small_parts_power_breakout.sch

eagleDTD.py: eagle-tweaked.dtd
	echo DTD=\"\"\" > $@
	cat $< >> $@
	echo \"\"\" >> $@

clean:
	rm -rf eagleDTD.py
	rm -rf *.broken.xml
