import unittest
import os
from os.path import join
import Swoop
import numpy as np
import numpy.testing as npt
import math

WE_HAVE_CGAL = True
try:
    import CGAL.CGAL_Kernel
    import SwoopGeom
    from Rectangle import Rectangle
except ImportError:
    WE_HAVE_CGAL = False


def get_inp(filename):
    return join(os.path.dirname(os.path.realpath(__file__)), "inputs", filename)

def eagle_code(vert_list):
    return "poly " + " ".join(["({0} {1})".format(v[0],v[1]) for v in vert_list])

@unittest.skipUnless(WE_HAVE_CGAL, "Need cgal bindings to run this")
class TestBoundingBoxes(unittest.TestCase):

    def test_correct_shape(self):
        board = SwoopGeom.from_file(get_inp("test_saving.brd"))
        polygon = board.get_element_shape("ARDUINO")
        vertices = map(SwoopGeom.cgal2np, polygon.vertices())
        should_be = [np.array([ 82.89493007,  15.0384369 ]),
                     np.array([ 65.25997764,  18.14795481]),
                     np.array([ 73.81652632,  66.67455381]),
                     np.array([ 91.45147876,  63.56503589])]
        for actual,desired in zip(vertices, should_be):
            npt.assert_allclose(actual, desired)

    def test_bounding_boxes(self):
        board = SwoopGeom.from_file(get_inp("test_saving.brd"))
        rect = board.get_element("R1").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (84.70000, 67.32380), (87.30000, 68.67620)))

        rect = board.get_element("TEST-ARC1").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (104.85650, 75.60080), (114.97665, 87.59554)))

        rect = board.get_element("TEST-ARC2").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (122.93650, 77.73274), (131.06350, 82.06350)))

        rect = SwoopGeom.arc_bounding_box(np.array([-1,2]), np.array([-1,-2]), math.pi)
        self.assertEqual(rect, Rectangle((-3,-2),(-1,2)))

        rect = board.get_element("TEST-ARC3").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (135.93650, 85.93650), (138.06350, 90.06350)))

        rect = board.get_element("TEST-PAD1").get_bounding_box()[0]
        self.assertEqual(rect,Rectangle( (124.50000, 87.50000), (130.50000, 90.50000)))

        rect = board.get_element("TEST-PAD2").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (116.50000, 89.25000), (119.50000, 90.75000)))

        rect = board.get_element("TEST-PAD-SQUARE").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (117.50000, 73.77000), (120.50000, 76.77000)))

        rect = board.get_element("TEST-PAD-ROUND").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (130.25000, 75.25000), (131.75000, 76.75000)))

        rect = board.get_element("TEST-PAD-ROT").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (137.54523, 78.99348), (140.45477, 81.00652)))

        rect = SwoopGeom.arc_bounding_box(np.array([-2,1]), np.array([1,-2]), math.pi)
        self.assertEqual(rect, Rectangle( (-2.62132, -2.62132), (1.00000, 1.00000)))

        rect = board.get_element("TEST-PAD-OCT").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (111.88653, 67.88653), (116.11347, 72.11347)))

        rect = board.get_element("TEST-PAD-OCT2").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (124.00000, 70.00000), (128.00000, 74.00000)))

        rect = board.get_element("TEST-PAD-SQUARE-ROT").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (118.13116, 82.13116), (119.86884, 83.86884)))

        rect= board.get_element("TEST-CIRCLE").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (132.72190, 49.88190), (152.03810, 69.19810)))

        rect = board.get_element("TEST-HOLE").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (113.45000, 58.45000), (114.55000, 59.55000)))

        print board.get_element("ARDUINO").get_package_moved().\
            get_children().get_bounding_box().reduce(Rectangle.union).eagle_code()

        arduino_package = board.get_element("ARDUINO").get_package_moved()[0]
        arduino_package.set_name("TEST-PACKAGE")
        lib = board.get_library("BOBs")[0]
        lib.add_package(arduino_package)
        elem = SwoopGeom.WithMixin.class_map["element"]()
        elem.set_name("OUTPUT")
        elem.set_library("BOBs")
        elem.set_package("TEST-PACKAGE")
        elem.set_x(0)
        elem.set_y(0)
        board.add_element(elem)
        board.write("out.brd")


    def test_query(self):
        board = SwoopGeom.from_file(get_inp("test_saving.brd"))
        results = board.get_overlapping(83.51, 63.91, 97.25, 71.85)
        self.assertEqual(len(results), 6)
        self.assertEqual(len(results.with_type(Swoop.Element)), 2)
        self.assertEqual(len(results.with_type(Swoop.Wire)), 4)





if __name__ == '__main__':
    unittest.main()
