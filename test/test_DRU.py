# -*- coding: utf-8 -*-
import unittest
import Swoop
import os
import re
import math
class TestDRU(unittest.TestCase):

    def setUp(self):
        self.curdir = os.path.dirname(os.path.realpath(__file__))
        self.me = os.path.dirname(os.path.realpath(__file__))
        
    def test_Parsing(self):
        with open(self.me + "/inputs/default.dru") as f:
            dru = Swoop.DRUFile(f)

        # wierdness with eval is to get the \n's match properly
        self.assertEqual(eval("\"{}\"".format(dru.get_value("description")["de"])), """<b>EAGLE Design Rules</b>\n<p>\nDie Standard-Design-Rules sind so gewählt, dass siefür \ndie meisten Anwendungen passen. Sollte ihre Platine \nbesondere Anforderungen haben, treffen Sie die erforderlichen\nEinstellungen hier und speichern die Design Rules unter \neinem neuen Namen ab.""")
        self.assertEqual(eval("\"{}\"".format(dru.get_value("description")["en"])), "<b>EAGLE Design Rules</b>\n<p>\nThe default Design Rules have been set to cover\na wide range of applications. Your particular design\nmay have different requirements, so please make the\nnecessary adjustments and save your customized\ndesign rules under a new name.")

        self.assertEqual(dru.get_value("layerSetup"), "(1*16)")

        self.assertEqual(dru.get_value("mdWireWire"), 0.2032)
        self.assertEqual(dru.get_value("rlMaxViaOuter"), 0.508)
        self.assertEqual(dru.get_value("mnLayersViaInSmd"), 2)
        self.assertEqual(dru.get_value("msMicroVia"), 9.99)
        self.assertEqual(dru.get_value("mtCopper")[0], 0.035)
        self.assertEqual(dru.get_value("mtIsolate")[1], 0.15)
        self.assertEqual(dru.get_value("psTop"), -1)
        
        def quick_test(dru):
            self.assertEqual(dru.layerSetup, "(1*16)")
            self.assertEqual(dru.mdWireWire, 0.2032)
            self.assertEqual(dru.rlMaxViaOuter, 0.508)
            self.assertEqual(dru.mnLayersViaInSmd, 2)
            self.assertEqual(dru.msMicroVia, 9.99)
            self.assertEqual(dru.mtCopper[0], 0.035)
            self.assertEqual(dru.mtIsolate[1], 0.15)
            self.assertEqual(dru.psTop, -1)
        quick_test(dru)
                
        sch_file = self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.sch"
        sch = Swoop.EagleFile.from_file(sch_file);

        quick_test(sch.get_DRU())

        sch = Swoop.EagleFile.from_file(sch_file, self.me + "/inputs/default.dru", );
        quick_test(sch.get_DRU())
        self.assertEqual(dru.foobar, 100)
