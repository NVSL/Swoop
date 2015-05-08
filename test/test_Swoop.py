import unittest
import Swoop
import Swoop.tools
import os
import re
import math

class TestSwoop(unittest.TestCase):
    
    def setUp(self):
        self.me = os.path.dirname(os.path.realpath(__file__))
        self.sch = Swoop.EagleFile.from_file(self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.sch")
        self.brd = Swoop.EagleFile.from_file(self.me + "/inputs/Xperimental_Trinket_Pro_small_parts_power_breakout.picked.brd")
        self.lbr = Swoop.EagleFile.from_file(self.me + "/inputs/Components.lbr")
        
    def test_Search(self):
        self.assertEqual(len([ x for x in self.brd.get_library("KoalaBuild").get_packages()[0].get_drawing_elements() if x.layer=="tDocu"]), 4, "Search failure")
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
                         count(), 2, "Fluent search failure")
        
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
        import StringIO
        output = StringIO.StringIO()
        self.sch.write(output)
        try:
            self.sch.write(output)
            self.assertTrue(True, "write to string failed")
        except e:
            self.assertTrue(False, "write to string failed")
            raise e
        
