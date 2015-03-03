
default: build test HighEagle.py doc

build: eagleDTD.py HighEagle.py

test: build $(TARGETS)  eagleDTD.py
	#	python ./HighEagleTest.py --layers NVSLLayers.lbr
	./checkEagle.py --file test2.sch Xperimental_Trinket_Pro_small_parts_power_breakout.sch

doc: HighEagle.py
	#$(MAKE) -C doc html

eagleDTD.py: eagle-tweaked.dtd
	echo DTD=\"\"\" > $@
	cat $< >> $@
	echo \"\"\" >> $@

HighEagle.py: HighEagle.jinja.py GenerateHighEagle.py
	python GenerateHighEagle.py --in tag-summary.dat --out $@

#tag-summary.dat: eagle-tweaked.dtd Makefile
#	cat $< | perl -ne 's/ +/ /g; s/\n/,/g;s/>/>\n/g;print' | perl -ne 's/^,*\s*</</g;s/, >/>/g;s/\%\w+;//g;print' | grep ATTLIST | perl -ne 's/!ATTLIST //g; s/"\w*"/OPTIONAL/g; s/#//g; s/<|>//g; s/,/:/; print'  > $@
#	echo "sheet: \nsegment: \ncompatibility: " >> $@  # these two tags have no attributes



clean:
	rm -rf eagleDTD.py
	rm -rf *.broken.xml
	rm -rf HighEagleBaseClasses.py EagleUtilBase.py EagleUsefulSkeleton.py
	rm -rf HighEagle.py
	rm -rf tag-summary.dat

