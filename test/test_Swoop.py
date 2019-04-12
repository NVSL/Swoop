import unittest
import Swoop
import Swoop.tools
import os
import re
import math
from lxml import etree as ET

class TestSwoop(unittest.TestCase):

    def setUp(self):
        self.curdir = os.path.dirname(os.path.realpath(__file__))
        self.tmpdir = os.path.join(self.curdir, "temp")
        if not os.path.exists(self.tmpdir):
            os.makedirs(self.tmpdir)

        self.me = os.path.dirname(os.path.realpath(__file__))
        self.sch_file = self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.sch"
        self.sch = Swoop.EagleFile.from_file(self.sch_file);
        self.brd_file = self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.brd"
        self.brd = Swoop.EagleFile.from_file(self.brd_file)
        self.lbr_file = self.me + "/inputs/Components.lbr"
        self.lbr = Swoop.EagleFile.from_file(self.lbr_file)

    def test_Search(self):
        self.assertEqual(len([ x for x in self.brd.get_library("KoalaBuild").get_package("CAPPRD250W50D600H1000_HS").get_drawing_elements() if x.layer=="tDocu"]), 4, "Search failure")
        self.assertEqual(len(self.brd.get_libraries()), len(self.brd.get_libraries()), "Search by type error")
        #print self.brd.get_library("KoalaBuild").get_package("CAPC1608X90_HS").get_drawing_elements(type=Swoop.Wire)
        self.assertEqual(len([x for x in self.brd.get_library("KoalaBuild").get_package("CAPC1608X90_HS").get_drawing_elements() if isinstance(x,Swoop.Wire)]), 12, "Search failure")
        self.assertEqual(len(self.brd.get_library("KoalaBuild").get_package("CAPC1608X90_HS").get_smds()), 2, "Search failure")


    def test_Fluent(self):
        t = Swoop.From(self.sch)
        #print t
        #print t.get_libraries()
        #print t.get_libraries().get_package("CAPC1608X90_HS")
        #print t.get_libraries().get_package("CAPC1608X90_HS").get_drawing_elements(layer="tCream")
        self.assertEqual(t.
                         get_libraries().
                         get_package("CAPC1608X90_HS").
                         get_drawing_elements().
                         with_layer("tCream").
                         count(), 2)#, "Fluent search failure")

        self.assertEqual(t.
                         get_libraries().
                         get_package("CAPC1608X90_HS").
                         get_drawing_elements().
                         with_layer("tCream").
                         with_type(Swoop.Polygon).
                         get_vertices().
                         count(),
                         18, "Fluent container search failure")


        self.assertEqual(len(t.
                             get_libraries().
                             get_package("CAPC1608X90_HS").
                             get_drawing_elements().
                             with_type(Swoop.Polygon).
                             get_vertices().
                             unpack()), 36, "Fluent container search failure")
        self.assertEqual(t.
                         get_libraries().
                         get_package("CAPC1608X90_HS").
                         get_drawing_elements().
                         with_type(Swoop.Polygon).
                         get_vertices().
                         count(), 36, "Fluent container search failure")

        self.assertEqual(t.get_libraries().
                         get_packages().
                         with_name("CAPC1608X90_HS").
                         get_name().
                         lower().
                         unpack()[0], "CAPC1608X90_HS".lower(), "Fluent container search failure")

        self.assertEqual(t.get_libraries().
                         get_packages().
                         with_name("CAPC1608X90_HS").
                         get_name().
                         lower().
                         unpack()[0], "CAPC1608X90_HS".lower(), "Fluent container search failure")

        self.assertEqual(t.
                         get_layers().
                         with_name(lambda x: re.match("^t", x) is not None).
                         count(), 17, "Regex filter failure")

        self.assertEqual(t.get_layers().
                         get_number().
                         reduce(min),
                         1, "From reduction failure")

        self.assertEqual(t.get_layers().
                         get_number().
                         reduce(max), 167, "From reduction failure")

        self.assertEqual(t.get_layers().
                         get_number().
                         map(lambda x: x*2).
                         reduce(max), 334, "From map failure")

        self.assertEqual(t.get_layers().
                         get_number().
                         filtered_by(lambda x: ((x % 2) == 0)).
                         reduce(max), 164, "From filter failure")

        s = 0;
        for i in t.get_layers().get_number():
            s += i

        self.assertEqual(t.get_layers().
                         get_number().
                         reduce(lambda x,y:x + y), s, "iteration failure")

        self.assertEqual(sum(t.get_layers().
                             get_number()), s, "iteration failure")


        self.assertEqual(round(Swoop.From(self.brd).
                               get_signals().
                               get_wires().
                               with_layer("Unrouted").
                               apply(lambda w: math.sqrt(((w.get_x1()-w.get_x2())**2 + (w.get_y1()-w.get_y2())**2))).
                               reduce(lambda x,y:x + y),6), round(1751.08121386,6), "Airwire test error")

        self.assertEqual(Swoop.From(self.brd).
                         get_layers().
                         with_name(Swoop.matching("^t")).
                         count(), 17, "Regex matching failure")

        self.assertEqual(Swoop.From(self.brd).
                         get_layers().
                         with_name(Swoop.not_matching("^t")).
                         count(),56, "Regex not matching failure")

    def test_Detach(self):

        brd = self.brd.clone()

        (Swoop.From(brd).
         get_layers().
         with_name(Swoop.matching("^t")).
         detach())

        self.assertEqual(Swoop.From(brd).
                         get_layers().
                         count(), 56, "Detach Error")

    def test_Rekey(self):
        sch = self.sch.clone()
        brd = self.brd.clone()
        s = Swoop.From(sch).get_libraries().get_symbols()[0]
        l = s.get_parent();

        old = s.get_name()
        self.assertEqual(l.get_symbol(old), s, "Rename precondition error")
        s.set_name("foo")
        self.assertEqual(s.get_name(), "foo", "Rename error")
        self.assertEqual(l.get_symbol("foo"), s,"Rename error")
        self.assertEqual(l.get_symbol(old), None, "Rename error")
        l.check_sanity()


    def test_Lookup(self):
        sch = self.sch.clone()
        brd = self.brd.clone()
        self.assertTrue(isinstance(sch.get_nth_library(0).get_nth_deviceset(0).get_nth_gate(0).find_symbol(), Swoop.Symbol), "wrong type from find_symbol")
        self.assertTrue(isinstance(brd.get_nth_library(0).get_nth_deviceset(2).get_nth_device(0).find_package(), Swoop.Package), "wrong type from find_package")
        self.assertTrue(isinstance(brd.get_nth_element(0).find_library(), Swoop.Library), "wrong type from find_library")
        self.assertTrue(isinstance(brd.get_nth_element(0).find_package(), Swoop.Package), "wrong type from find_package")

        self.assertTrue(isinstance(sch.get_nth_part(3).find_library(), Swoop.Library), "wrong type from find_library")
        self.assertTrue(isinstance(sch.get_nth_part(3).find_deviceset(), Swoop.Deviceset), "wrong type from find_deviceset")
        self.assertTrue(isinstance(sch.get_nth_part(3).find_device(), Swoop.Device), "wrong type from find_device")
        self.assertTrue(isinstance(sch.get_nth_part(3).find_technology(), Swoop.Technology), "wrong type from find_technology")

        threw = False
        try:
            sch.get_sheet(0).get_nth_instance(0).find_gate()
        except:
            threw = True

        self.assertTrue(threw, "not implemented failed")

    def test_Write(self):
        import io
        output = io.StringIO()
        self.sch.write(output)
        try:
            self.sch.write(output)
            self.assertTrue(True, "write to string failed")
        except e:
            self.assertTrue(False, "write to string failed")
            raise e

    def test_TypeCheck(self):
        sch = self.sch.clone()

        l = sch.get_layers()[0]
        with self.assertRaises(Swoop.SwoopError):
            l.set_name(10);
        with self.assertRaises(Swoop.SwoopError):
            l.set_number("hello");

        l.set_name("foo")
        l.set_number(1999)


    def test_ConstantAttrs(self):
        sch = self.sch.clone()

        a = Swoop.From(sch).get_libraries().get_devicesets().get_devices().get_technologies().get_attributes()[0]

        self.assertEqual(a.get_xml(), '<attribute name="CASE" value="" constant="no"/>'.encode('utf8'))
        a.set_constant(True)
        self.assertEqual(a.get_xml(), '<attribute name="CASE" value=""/>'.encode('utf8'))
        a.set_constant(False)
        self.assertEqual(a.get_xml(), '<attribute name="CASE" value="" constant="no"/>'.encode('utf8'))

        brd = self.brd.clone()
        c1a = brd.get_element("C1A")
        c1b = brd.get_element("C1B")
        c1 = brd.get_element("C1")

        self.assertEqual(c1a.get_locked(), True)
        self.assertEqual(c1b.get_locked(), False)
        self.assertEqual(c1.get_locked(), False)
        
    def test_Swoop_openfile(self):
        a = Swoop.EagleFile.from_file(os.path.join(self.me, "inputs/Quadcopter.koala.sch"))

    def test_Swoop_write_with_None(self):
        a = Swoop.EagleFile.from_file(os.path.join(self.me, "inputs/Trinket_Pro_default_SMD_parts_power_breakout.koala.sch"))
        a.write(os.path.join(self.tmpdir, "a.sch"))

    def test_LibraryName(self):
        name = self.lbr.get_library().get_name()
        self.assertNotEqual(name, None)
        
    def test_Clone(self):
        a = Swoop.EagleFile.from_file(os.path.join(self.me, "inputs/Trinket_Pro_default_SMD_parts_power_breakout.koala.sch"))
        a.clone()
        a.write("foo.sch")

        for a in [self.brd, self.sch, self.lbr]:
            b = a.clone()
            b.write("/dev/null")
        
    def tearDown(self):
        # Remove self.tmpdir
        try:
            for root, dirs, files in os.walk(self.tmpdir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.tmpdir)
        except:
            pass

    def test_etreeOpen(self):
        tree = ET.parse(self.sch_file)
        Swoop.SchematicFile.from_etree(tree)
        tree = ET.parse(self.brd_file)
        Swoop.BoardFile.from_etree(tree)
        #tree = ET.parse(self.lbr_file)
        #Swoop.LibraryFile.from_etree(tree)

        
    def test_mirror_layers(self):
        self.assertEqual(self.sch.get_mirrored_layer("Top"), "Bottom", "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer("Bottom"), "Top", "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer("tPlace"), "bPlace", "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer("bPlace"), "tPlace", "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer("Dimension"), "Dimension", "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer("tFaceplateCover"), "tFaceplateCover", "Layer mirroring error")

        self.assertEqual(self.sch.get_mirrored_layer(self.sch.get_layer("Top")).get_name(), "Bottom", "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer(self.sch.get_layer("Bottom")).get_name(), "Top", "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer(self.sch.get_layer("tPlace")).get_name(), "bPlace", "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer(self.sch.get_layer("bPlace")).get_name(), "tPlace", "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer(self.sch.get_layer("Dimension")).get_name(), "Dimension", "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer(self.sch.get_layer("tFaceplateCover")).get_name(), "tFaceplateCover", "Layer mirroring error")

        self.assertEqual(self.sch.get_mirrored_layer(1), 16, "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer(16), 1, "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer(21), 22, "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer(22), 21, "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer(20), 20, "Layer mirroring error")
        self.assertEqual(self.sch.get_mirrored_layer(100), 100, "Layer mirroring error")
