
default: build

build: eagleDTD.py Swoop.py

.PHONY: test
test: eagleDTD.py Swoop.py
	python -m unittest discover

#	#	python ./SwoopTest.py --layers NVSLLayers.lbr
#	#	./checkEagle.py --file test2.sch Xperimental_Trinket_Pro_small_parts_power_breakout.sch

.PHONY: doc
doc: Swoop.py GenerateSwoop.py $(wildcard doc/*.rst)
	$(MAKE) -C doc html

eagleDTD.py: eagle-tweaked.dtd
	echo DTD=\"\"\" > $@
	cat $< >> $@
	echo \"\"\" >> $@

Swoop.py: Swoop.jinja.py GenerateSwoop.py
	python GenerateSwoop.py --out $@

#tag-summary.dat: eagle-tweaked.dtd Makefile
#	cat $< | perl -ne 's/ +/ /g; s/\n/,/g;s/>/>\n/g;print' | perl -ne 's/^,*\s*</</g;s/, >/>/g;s/\%\w+;//g;print' | grep ATTLIST | perl -ne 's/!ATTLIST //g; s/"\w*"/OPTIONAL/g; s/#//g; s/<|>//g; s/,/:/; print'  > $@
#	echo "sheet: \nsegment: \ncompatibility: " >> $@  # these two tags have no attributes



clean:
	rm -rf eagleDTD.py
	rm -rf *.broken.xml
	rm -rf Swoop.py
	$(MAKE) -C doc clean
