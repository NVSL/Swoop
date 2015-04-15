import unittest
import os
from os.path import join
import SwoopGeom
import Swoop
from Rectangle import Rectangle
import numpy as np
import numpy.testing as npt

WE_HAVE_CGAL = True
try:
    import CGAL.CGAL_Kernel
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

        rect = board.get_element("TEST-PAD1").get_bounding_box()[0]
        self.assertEqual(rect,Rectangle( (124.50000, 87.50000), (130.50000, 90.50000)))

        rect = board.get_element("TEST-PAD2").get_bounding_box()[0]
        # print rect.eagle_code()

        rect = board.get_element("TEST-PAD-SQUARE").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (117.50000, 73.77000), (120.50000, 76.77000)))

        rect = board.get_element("TEST-PAD-ROUND").get_bounding_box()[0]
        self.assertEqual(rect, Rectangle( (130.25000, 75.25000), (131.75000, 76.75000)))


    def test_query(self):
        board = SwoopGeom.from_file(get_inp("test_saving.brd"))
        results = board.get_overlapping(83.51, 63.91, 97.25, 71.85)
        self.assertEqual(len(results), 6)
        self.assertEqual(len(results.with_type(Swoop.Element)), 2)
        self.assertEqual(len(results.with_type(Swoop.Wire)), 4)





if __name__ == '__main__':
    unittest.main()
