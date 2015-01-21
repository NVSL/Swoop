
default:
build:

test:
	python ./HighEagleTest.py
	python ./PartResolutionTest.py --ohms Resistor-Yageo.csv --ceramics CeramicCaps-Murata.csv