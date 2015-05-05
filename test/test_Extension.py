import unittest
import Swoop
import SwoopTools
import os
import re
import math

from Swoop import *


class TestExtension(unittest.TestCase):

    class MyMixin(object):

        def print_my_type(self):
            print type(self)
        def print_my_name(self):
            print self.get_name()
        def get_my_type_name(self):
            return type(self).__name__
        def get_my_name(self):
            return self.get_name()

    def setUp(self):

        NewEagleFile = Swoop.Mixin(self.MyMixin, "Typer")
        #print NewEagleFile.__name__
        self.me = os.path.dirname(os.path.realpath(__file__))
        self.sch = NewEagleFile.from_file(self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.sch")
        self.brd = NewEagleFile.from_file(self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.brd")
        self.lbr = NewEagleFile.from_file(self.me + "/inputs/Components.lbr")
        
    def test_Mixin(self):

        self.assertEqual(isinstance(From(self.lbr).
                                    get_library().
                                    get_packages()[0],
                                    Swoop.Package), True, "Mixin Inheritance error")

        self.assertEqual(isinstance(From(self.lbr).
                                    get_library().
                                    get_symbols()[0],
                                    Swoop.Symbol), True, "Mixin Inheritance error")

        #print "here " + str(type(self.lbr.get_library().get_packages()[0]))
        self.assertEqual(self.lbr.get_library().get_packages()[0].get_my_name(),"DO-1N4148", "Mixin error")

        self.assertEqual(self.lbr.get_library().get_packages()[0].get_my_type_name(),"TyperPackage", "Mixin typename error")

    class Jumper(object):
        def do_it(self):
            return "jump"

    class Walker(object):
        def do_it(self):
            return "walk"


    def test_Heterogenous(self):

        J = Swoop.Mixin(self.Jumper, "Jump")
        W = Swoop.Mixin(self.Walker, "Walk")

        js = J.from_file(self.me + "/inputs/test06.sch")
        ws = W.from_file(self.me + "/inputs/test06.sch")

        jl = J.from_file(self.me + "/inputs/Components.lbr")
        wl = W.from_file(self.me + "/inputs/Components.lbr")

        # print EagleFile.class_map["library"]
        # print J.class_map["library"]
        # print W.class_map["library"]

        # print "2here " + str(type(js.get_libraries()[0]))
        # print js.get_libraries()[0].do_it()
        # print ws.get_libraries()[0].do_it()

        # print jl.get_library().get_packages()[0].do_it()
        # print wl.get_library().get_packages()[0].do_it()

        self.assertEqual(js.get_libraries()[0].do_it(), "jump", "Heterogenous extension error")
        self.assertEqual(ws.get_libraries()[0].do_it(), "walk", "Heterogenous extension error")
        self.assertEqual(jl.get_library().get_packages()[0].do_it(), "jump", "Heterogenous extension error")
        self.assertEqual(wl.get_library().get_packages()[0].do_it(), "walk", "Heterogenous extension error")
        
        self.assertEqual(type(jl.new_Package()), type(jl.get_library().get_packages()[0]), "EFP factory error")

    def test_Visitor(self):
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

        oldsch = EagleFile.from_file(self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.sch")
        self.assertEqual(Counter(oldsch).go().elementCount, Counter(self.sch).go().elementCount, "Extensions + visitor error")
        self.assertEqual(Counter(oldsch).go().count, Counter(self.sch).go().count, "Extensions + visitor error")

    def test_Example(self):
        class AttrMixin(object):
            def __init__(self):
                self.attrs = {}
            def set_attr(self, n, v):
                self.attrs[n] = v
                return self
            def get_attr(self, n):
                return self.attrs.get(n)

        AttrEagleFile = Swoop.Mixin(AttrMixin, "Attr")
        
        sch = AttrEagleFile.open(self.me + "/inputs/test05.sch")
        sch.get_library("PickerDesign").get_symbol("GENERIC-RESISTOR_").set_attr("good?", "yes!")
        self.assertEqual(sch.get_library("PickerDesign").get_symbol("GENERIC-RESISTOR_").get_attr("good?"), "yes!", "Attr mixin error")

    
