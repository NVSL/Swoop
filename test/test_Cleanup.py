import unittest
import Swoop.tools
import os
import re
import math

#from bin.cleanupEagle import main
from Swoop import *

from Swoop.tools.CleanupEagle import main

class TestCleanup(unittest.TestCase):

    def setUp(self):
        self.me = os.path.dirname(os.path.realpath(__file__))

    def test_Schematic(self):
        main(["--file", self.me + "/inputs/cleanup_test01.sch", "--out", self.me + "/inputs/cleanup_test01.out.sch"])
        ef = EagleFile.from_file(self.me + "/inputs/cleanup_test01.out.sch")
        self.assertEqual(From(ef).get_libraries().count(), 6, "Wrong number of libraries")
        self.assertEqual(From(ef).get_libraries().get_packages().count(), 3, "Wrong number of packages")
        self.assertEqual(From(ef).get_libraries().get_symbols().count(), 10, "Wrong number of symbols")
        self.assertEqual(From(ef).get_libraries().get_devicesets().count(), 9, "Wrong number of devicesets")
        self.assertEqual(From(ef).get_libraries().get_devicesets().get_devices().count(), 9, "Wrong number of devices")

    def test_Board(self):
        main(["--file", self.me + "/inputs/cleanup_test01.brd", "--out", self.me + "/inputs/cleanup_test01.out.brd"])
        ef = EagleFile.from_file(self.me + "/inputs/cleanup_test01.out.brd")
        self.assertEqual(From(ef).get_libraries().count(), 1, "Wrong number of libraries")
        self.assertEqual(From(ef).get_libraries().get_packages().count(), 3, "Wrong number of packages")
        self.assertEqual(From(ef).get_libraries().get_symbols().count(), 0, "Wrong number of symbols")
        self.assertEqual(From(ef).get_libraries().get_devicesets().count(), 0, "Wrong number of devicesets")
        self.assertEqual(From(ef).get_libraries().get_devicesets().get_devices().count(), 0, "Wrong number of devices")
        
    
    def test_Library(self):
        main(["--file", self.me + "/inputs/cleanup_test01.lbr", "--out", self.me + "/inputs/cleanup_test01.out.lbr"])
        ef = EagleFile.from_file(self.me + "/inputs/cleanup_test01.out.lbr")
        self.assertEqual(From(ef).get_library().get_packages().count(), 35, "Wrong number of packages")
        self.assertEqual(From(ef).get_library().get_symbols().count(), 97, "Wrong number of symbols")
        self.assertEqual(From(ef).get_library().get_devicesets().count(),96, "Wrong number of devicesets")
        self.assertEqual(From(ef).get_library().get_devicesets().get_devices().count(), 101, "Wrong number of devices")
        
    
