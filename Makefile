
default: 

build: eagleDTD.py

test:
	python ./HighEagleTest.py
	python ./PartResolutionTest.py --ohms Resistor-Yageo.csv --ceramics CeramicCaps-Murata.csv
	python picker.py --in test2.sch  --out out.sch --ohms Resistor-Yageo.csv --ceramics ../../Libraries/Parts/Digikey/CeramicCaps-Murata.csv  --lbr NVSL.lbr
	python QueryParseTest.py
	./checkEagle.py --file *.sch *.lbr

eagleDTD.py: eagle-tweaked.dtd
	echo DTD=\"\"\" > $@
	cat $< >> $@
	echo \"\"\" >> $@