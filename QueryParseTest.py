#!/usr/bin/env python
import argparse

from PartResolutionEnvironment import *
from Resistor import Resistor
from Capacitor import CeramicCapacitor
from PartType import *
from PartDatabase import PartDB
from PartParameter import *
from ParameterQuery import *
from Units import *
from EagleUtil import *
from HighEagle import *

import sys

if __name__ == "__main__":

    print ParameterQuery.parse("[4, 10]")
    print ParameterQuery.parse("[4.2, 10]")
    print ParameterQuery.parse("[4, -1.0]")
    print ParameterQuery.parse("[-4 , 10]")
    print ParameterQuery.parse("[ 4,10 ]")
    print ParameterQuery.parse("[ 4,10 ] ")
    print ParameterQuery.parse(" [ 4,10 ] ")
    print ParameterQuery.parse(" [ 4, 10 ]")
    print ParameterQuery.parse(" [ 4, 10 ] aoeu")
    print ParameterQuery.parse(" [ 4uF, 10pF ]")
    print ParameterQuery.parse(" [ 4k, 10M ]")
    print ParameterQuery.parse(" [ 4, 10 ]")
    print ParameterQuery.parse("<4")
    print ParameterQuery.parse("<4pH")
    print ParameterQuery.parse("<=4")
    print ParameterQuery.parse("<=4.0")
    print ParameterQuery.parse("<=-4.0")
    print ParameterQuery.parse(">=-4.0")
    print ParameterQuery.parse(">=4.0")
    print ParameterQuery.parse("4.0")
    print ParameterQuery.parse("10 +/- 14%")
    print ParameterQuery.parse("10nF +/- 14%")
    print ParameterQuery.parse("10nF+/- 14%")
    print ParameterQuery.parse("10nF +/-14% ")
    sys.exit()
