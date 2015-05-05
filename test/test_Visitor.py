import unittest
import Swoop
import SwoopTools
import os

class Counter(Swoop.EagleFilePartVisitor):
    def __init__(self, root=None):
        Swoop.EagleFilePartVisitor.__init__(self,root)
        self.count = 0;
        self.elementCount = 0
        self.layerCount = 0
    def default_pre(self, efp):
        self.count += 1
    def Element_pre(self, e):
        self.count += 1
        self.elementCount += 1
    def Layer_pre(self, l):
        self.count += 1
        self.layerCount += 1


class TestVisitor(unittest.TestCase):
    
    def setUp(self):
        self.me = os.path.dirname(os.path.realpath(__file__))
        self.sch = Swoop.EagleFile.from_file(self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.sch")
        self.brd = Swoop.EagleFile.from_file(self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.brd")
        self.lbr = Swoop.EagleFile.from_file(self.me + "/inputs/Components.lbr")
        
    def test_counter(self):
        self.assertEqual(Counter(self.sch).go().count, 25394, "Wrong EFP count")
        self.assertEqual(Counter(self.brd).go().count, 17774, "Wrong EFP count")
        self.assertEqual(Counter(self.lbr).go().count, 136, "Wrong EFP count")

        self.assertEqual(Counter(self.sch).go().layerCount, 73, "Wrong Layer count")
        self.assertEqual(Counter(self.brd).go().layerCount, 73, "Wrong Layer count")
        self.assertEqual(Counter(self.lbr).go().layerCount, 133, "Wrong Layer count")

        self.assertEqual(Counter(self.sch).go().elementCount, 0, "Wrong Element count")
        self.assertEqual(Counter(self.brd).go().elementCount, 42, "Wrong Element count")
        self.assertEqual(Counter(self.lbr).go().elementCount, 0, "Wrong Element count")
