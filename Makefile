
default: build test

build: eagleDTD.py

test: build
	python ./HighEagleTest.py
	python ./PartResolutionTest.py --ohms Resistor-Yageo.csv --ceramics CeramicCaps-Murata.csv
	python picker.py --in test2.sch  --out out.sch --ohms Resistor-Yageo.csv --ceramics CeramicCaps-Murata.csv  --lbr NVSL.lbr
	python QueryParseTest.py
	./buildResolverParts.py --lbr Symbols.lbr --out out.lbr
	./checkEagle.py --file *.sch *.lbr

eagleDTD.py: eagle-tweaked.dtd
	echo DTD=\"\"\" > $@
	cat $< >> $@
	echo \"\"\" >> $@