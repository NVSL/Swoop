import unittest
import Swoop.tools
import os
import re
import math

#from bin.cleanupEagle import main
from Swoop import *


class TestSimpleGeometry(unittest.TestCase):

    def setUp(self):
        self.me = os.path.dirname(os.path.realpath(__file__))

    def test_geo(self):
        ef = From(EagleFile.from_file(self.me + "/inputs/geo_test.sch"))
        part = ef.get_nth_sheet(0).get_nth_instance(1)[0]
        rotpart = ef.get_nth_sheet(0).get_nth_instance(0)[0]
        circle = ef.get_nth_sheet(0).get_plain_elements().with_type(Circle)[0]
        measure = ef.get_nth_sheet(0).get_plain_elements().with_type(Dimension)[0]
        wire = ef.get_nth_sheet(0).get_nets().get_segments().get_wires()[0]
        module = ef.get_nth_module(0)[0]
        rect = ef.get_nth_sheet(0).get_plain_elements().with_type(Rectangle)[0]

        self.assertEqual(part.get_location(), [67,45])
        self.assertEqual(rotpart.get_location(), [54,45])
        self.assertEqual(rotpart.get_rotation(), 90)
        self.assertEqual(rotpart.get_mirrored(), True)
        self.assertEqual(rotpart.get_spin(), False)
        self.assertEqual(wire.get_points(), [58,38, 84,39])
        self.assertEqual(circle.get_radius(), 4)
        self.assertEqual(circle.get_diameter(), 8)
        self.assertEqual(rect.get_corners(), [68, 50,73,55])
        self.assertEqual(measure.get_align(), [93.03448125,53.913790625])
        self.assertEqual(module.get_size(), [30,20])
        
        part.set_location(68,46)
        self.assertEqual(part.get_location(), [68,46])

        From([part, circle, measure, wire, rect]).translate(1,-1)

        self.assertEqual(part.get_location(), [69,45])
        self.assertEqual(wire.get_points(), [59,37, 85,38])
        self.assertEqual(rect.get_corners(), [69, 49,74,54])
        self.assertEqual(measure.get_align(), [94.03448125,52.913790625])

        module.set_size(68,46)
        self.assertEqual(module.get_size(), [68,46])

        rotpart.set_rotation(95);
        rotpart.set_spin(True);
        rotpart.set_mirrored(False);
        self.assertEqual(rotpart.get_rotation(), 95)
        self.assertEqual(rotpart.get_mirrored(), False)
        self.assertEqual(rotpart.get_spin(), True)
        
