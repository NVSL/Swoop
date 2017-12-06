import unittest
import Swoop
import Swoop.tools
import os
import re
import math
try:
    from . import testExt
except ValueError:
    import testExt

try:
    from . import areaExt as Area
except ValueError:
    import areaExt as Area

from Swoop import *

class TestExtension(unittest.TestCase):

    class MyMixin(object):

        def print_my_type(self):
            print(type(self))
        def print_my_name(self):
            print(self.get_name())
        def get_my_type_name(self):
            return type(self).__name__
        def get_my_name(self):
            return self.get_name()

    def setUp(self):
        #log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        
        NewEagleFile = Swoop.Mixin(self.MyMixin, "Typer")

        self.me = os.path.dirname(os.path.realpath(__file__))
        self.sch = NewEagleFile.from_file(self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.sch")
        self.brd = NewEagleFile.from_file(self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.brd")
        self.lbr = NewEagleFile.from_file(self.me + "/inputs/Components.lbr")

        NewEagleFileMod = Swoop.Mixin(testExt, "Mod")
        #print(NewEagleFile.__name__)
        self.lbr2 = NewEagleFileMod.from_file(self.me + "/inputs/Components.lbr")

        AreaEagleFile = Swoop.Mixin(Area, "Area")
        #print(NewEagleFile.__name__)
        self.lbr_area = AreaEagleFile.from_file(self.me + "/inputs/Components.lbr")

    def test_Mixin(self):

        self.assertEqual(isinstance(From(self.lbr).
                                    get_library().
                                    get_packages()[0],
                                    Swoop.Package), True, "Mixin Inheritance error")

        self.assertEqual(isinstance(From(self.lbr).
                                    get_library().
                                    get_symbols()[0],
                                    Swoop.Symbol), True, "Mixin Inheritance error")

        self.assertEqual(self.lbr.get_library().get_packages()[0].get_my_type_name(),"TyperPackage", "Mixin typename error")

        from_mixin = "DO-1N4148"
        for package in self.lbr.get_library().get_packages():
            if package.get_my_name() == from_mixin:
                break
        else:
            self.fail("Mixin error - did not find package from mixed in library")

    class Jumper(object):
        def do_it(self):
            return "jump"
        def jump(self):
            return "jump"
        
    class Walker(object):
        def do_it(self):
            return "walk"
        def walk(self):
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

    def test_Composition(self):
        J = Swoop.Mixin(self.Jumper, "Jump")
        WJ = Swoop.Mixin(self.Walker, "Walk", base=J)

        wjl = WJ.from_file(self.me + "/inputs/Components.lbr")

        self.assertEqual(wjl.get_library().jump(), "jump", "Extension composition error")
        self.assertEqual(wjl.get_library().walk(), "walk", "Extension composition error")

        WJA = Swoop.Mixin(Area, "Area", base=WJ)
        wjal = WJA.from_file(self.me + "/inputs/Components.lbr")
        self.assertAlmostEqual(From(wjal).
                               get_library().
                               get_packages().
                               get_drawing_elements().
                               with_type(Rectangle).
                               get_area().
                               reduce(lambda x,y:x+y, init=0.0),
                               7711.54157257,
                               places=5,
                               msg="Extension composition error")
        
        A = Swoop.Mixin(Area, "Area")
        AJ = Swoop.Mixin(self.Jumper, "Jump", base=A)
        ajl = AJ.from_file(self.me + "/inputs/Components.lbr")
        self.assertAlmostEqual(From(ajl).
                               get_library().
                               get_packages().
                               get_drawing_elements().
                               with_type(Rectangle).
                               get_area().
                               reduce(lambda x,y:x+y, init=0.0),
                               7711.54157257,
                               places=7,
                               msg="Extension composition error")
        
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


    def test_MixinModule(self):
        self.assertEqual(self.lbr2.get_library().hello(), "Hello from Library", "Module-based extension error")
        self.assertFalse(hasattr(self.lbr2.get_library().get_symbols()[0], "hello"))
        self.assertAlmostEqual(From(self.lbr_area).get_library().get_packages().get_drawing_elements().with_type(Rectangle).get_area().reduce(lambda x,y:x+y, init=0.0),7711.54157257, places=7, msg="Area extension error")
