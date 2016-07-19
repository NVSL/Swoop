import unittest
import os
from os.path import join
import Swoop
import math

HAVE_DEPENDENCIES = True
try:
    import numpy as np
    import numpy.testing as npt
    import CGAL.CGAL_Kernel
    import Swoop.ext.Geometry as SwoopGeom
    from Swoop.ext.Shapes import Rectangle, LineSegment, RotatedRectangle
except ImportError as e:
    print e
    HAVE_DEPENDENCIES = False


def get_inp(filename):
    return join(os.path.dirname(os.path.realpath(__file__)), "inputs", filename)

def eagle_code(vert_list):
    return "poly " + " ".join(["({0} {1})".format(v[0],v[1]) for v in vert_list])

@unittest.skipUnless(HAVE_DEPENDENCIES, "Need numpy, CGAL python bindings, and Dingo's rectangle to run this")
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
        self.assertEqual(rect,Rectangle( (129.50000, 71.50000), (135.50000, 74.50000)))

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

        rect = board.get_element("TEST-POLYGON").get_package_moved().\
            get_children().get_bounding_box().reduce(Rectangle.union)
        self.assertEqual(rect, Rectangle( (99.33003, 23.26925), (134.14446, 45.35457)))

        rect = board.get_element("ARDUINO").get_package_moved().\
            get_children().get_bounding_box().reduce(Rectangle.union)
        self.assertEqual(rect, Rectangle( (65.44012, 15.95000), (91.43026, 66.66429)))

    def test_bbox_other(self):
        brd = SwoopGeom.WithMixin.from_file(get_inp("loud-flashy-driver.postroute.brd"))
        transform = brd.get_element("L_2_DRIVE").get_transform()
        bbox = Swoop.From(brd).get_element("L_2_DRIVE").\
            find_package().get_children().\
            filtered_by(lambda c: hasattr(c,"get_layer") and c.get_layer()=="tKeepout").\
            get_bounding_box().reduce(Rectangle.union)
        bbox = transform.apply(bbox)
        self.assertEqual(bbox, Rectangle((-15.2535, 76.5065), (34.4035, 127.4335)).rotate(180,False))

        bbox2 = brd.get_element("R_2_DRIVE").find_package().get_bounding_box("tKeepout")
        bbox2 = brd.get_element("R_2_DRIVE").get_transform().apply(bbox2)
        self.assertEqual(bbox2, Rectangle((66.5417619588, 70.8907803168), (116.198761959, 121.817780317)).rotate(200,False))


    def test_bbox_after_filter(self):
        board = SwoopGeom.from_file(get_inp("fp_bbox.brd"))
        bbox = board.get_elements().get_package_moved().get_bounding_box()[0]
        self.assertEqual(bbox, Rectangle( (-17.31000, -39.84350), (31.96520, -21.93650)))
        tface = board.get_elements().\
            get_package_moved().\
            get_children().\
            filtered_by(lambda p: hasattr(p,"layer") and p.layer=="tFaceplate").\
            get_bounding_box()[0]
        self.assertEqual(tface, Rectangle( (-17.00000, -38.00000), (-7.00000, -24.00000)))


    def test_query(self):
        board = SwoopGeom.from_file(get_inp("test_saving.brd"))
        results = board.get_overlapping(83.51, 63.91, 97.25, 71.85)
        self.assertEqual(len(results), 6)
        self.assertEqual(len(results.with_type(Swoop.Element)), 2)
        self.assertEqual(len(results.with_type(Swoop.Wire)), 4)

        board = SwoopGeom.from_file(get_inp("test_query.brd"))

        result = board.get_overlapping(Rectangle((99,47), (104,53)))
        self.assertEqual(len(result), 1)
        result = board.get_overlapping(Rectangle((100,46), (102,48)))
        self.assertEqual(len(result), 1)
        result = board.get_overlapping(Rectangle((107,52), (109,54)))
        self.assertEqual(len(result), 0)
        result = board.get_overlapping(Rectangle((102,38), (104,40)))
        self.assertEqual(len(result), 1)



@unittest.skipUnless(HAVE_DEPENDENCIES, "Need numpy, CGAL python bindings, and Dingo's rectangle to run this")
class TestFilteredBoundingBoxes(unittest.TestCase):
    def test_equality(self):
        r1 = RotatedRectangle(Rectangle((1,2), (3,4)), 120)
        r2 = RotatedRectangle(Rectangle((1,2), (3,4)), 120)

        self.assertEqual(r1, r2)
        r2.rotate(10)
        self.assertNotEqual(r1, r2)

    def test_transform(self):
        brd = Swoop.From(SwoopGeom.WithMixin.from_file(get_inp("loud-flashy-driver.postroute.brd")))
        transform = brd.get_element("R_2_DRIVE").get_transform()[0]

        self.assertEqual(transform.rotation, 200)
        self.assertEqual(transform.mirrored, False)
        npt.assert_allclose(transform.translation, np.array([123,93]))
        bbox = brd.get_element("R_2_DRIVE").find_package().get_children().\
            filtered_by(lambda p: hasattr(p,"get_layer") and p.get_layer()=="bKeepout").get_bounding_box().\
            reduce(Rectangle.union)
        bbox = transform.apply(bbox)
        should_be = RotatedRectangle(Rectangle( (66.5280811531, 70.9283680217), (116.185081153, 121.855368022) ), 200, around_origin=False)
        self.assertEqual(should_be, bbox)
        # print bbox

    def test_filtering(self):
        brd = SwoopGeom.WithMixin.from_file(get_inp("loud-flashy-driver.postroute.brd"))
        bbox = brd.get_element("U1_3_DISPLAY_2").get_bounding_box(type=Swoop.Pad)
        # print bbox.eagle_code()

        # print bbox.eagle_code()

@unittest.skipUnless(HAVE_DEPENDENCIES, "Need numpy, CGAL python bindings, and Dingo's rectangle to run this")
class TestShapeQueries(unittest.TestCase):
    def test_segments(self):
        l1 = LineSegment(np.array([0,0]), np.array([2,2]))
        l2 = LineSegment(np.array([0,0]), np.array([3,-2]))
        self.assertTrue(l1.overlaps(l2))
        self.assertTrue(l2.overlaps(l1))

        l2 = LineSegment(np.array([-1,-1]), np.array([3,3]))
        self.assertTrue(l1.overlaps(l2))
        self.assertTrue(l2.overlaps(l1))

        l2 = LineSegment(np.array([-1,-2]), np.array([4,3]))
        self.assertFalse(l1.overlaps(l2))
        self.assertFalse(l2.overlaps(l1))

        l2 = LineSegment(np.array([3,-1]), np.array([-1,3]))
        self.assertTrue(l1.overlaps(l2))
        self.assertTrue(l2.overlaps(l1))

    def test_recs(self):
        r1 = Rectangle( (-1,-1), (8,7) )
        r2 = Rectangle((8.79, 2.144), (17.79, 11.144)).rotate(-10, around_origin=False)

        self.assertFalse(r1.overlaps(r2))
        self.assertFalse(r2.overlaps(r1))

        r2 = Rectangle((8.5, 2.144), (17.5, 11.144)).rotate(-10, around_origin=False)
        # edges=list(r2.edges())
        # self.assertEqual(len(edges), 4)
        # for e in edges:
        #     print e.p1, e.p2

        self.assertTrue(r1.overlaps(r2))
        self.assertTrue(r2.overlaps(r1))

        r = Rectangle((0.498, -12.082), (13.29, -0.124))
        npt.assert_allclose(r.center(), np.array([ 6.894, -6.103]))
        r1 = r.rotate(10, False)
        npt.assert_allclose(r1.center(), np.array([ 6.894, -6.103]))
        rcopy = r1.copy()
        npt.assert_allclose(rcopy.center(), np.array([ 6.894, -6.103]))
        rcopy = rcopy.rotate(-10, False)
        npt.assert_allclose(rcopy.center(), np.array([ 6.894, -6.103]))

        npt.assert_allclose(r1.center(), np.array([ 6.894, -6.103]))
        r2 = Rectangle((0,-12), (13,0)).rotate(20, False)
        self.assertTrue(r1.overlaps(r2))
        npt.assert_allclose(r1.center(), np.array([ 6.894, -6.103]))
        r2 = Rectangle((3,-9), (9,-5)).rotate(169, False)
        self.assertTrue(r1.overlaps(r2))
        r2 = Rectangle((13,-5), (19,-1)).rotate(169, False)
        self.assertTrue(r1.overlaps(r2))
        r2.move(np.array([1,0]))
        self.assertFalse(r1.overlaps(r2))

        r1 = Rectangle((3,-8), (18,-2)).rotate(0)
        r2 = r1.copy().rotate(90, around_origin=False)
        self.assertTrue(r1.overlaps(r2))
        r2.move(np.array([11,0]))
        self.assertFalse(r1.overlaps(r2))

        r1 = Rectangle((3,-8), (18,-2)).rotate(10,False)
        r2 = Rectangle((-5,-8), (10,-2)).rotate(280,False)
        self.assertTrue(r1.overlaps(r2))
        self.assertTrue(r2.overlaps(r1))

        r2.move(np.array([-3,0]))
        self.assertFalse(r1.overlaps(r2))
        self.assertFalse(r2.overlaps(r1))

    def test_rotated_rec_bug(self):
        # rect R0.0 (42.0028 37.7614999892) (48.2385000242 44.2385000108)
        # rect R180.0 (14.51 1.84) (32.29 27.875)

        # rect R0.0 (42.0028 37.7614999892) (48.2385000242 44.2385000108)
        # rect R180.0 (1.175 2.475) (51.975 54.545)

        led = RotatedRectangle(Rectangle( (42.00280, 37.76150), (48.23850, 44.23850)), 0.0, False)
        motor_bot = RotatedRectangle(Rectangle( (14.51000, 1.84000), (32.29000, 27.87500)), 180.0, False)
        motor_top = RotatedRectangle(Rectangle( (1.17500, 2.47500), (51.97500, 54.54500)), 180.0, False)

        self.assertFalse(led.overlaps(motor_bot))
        self.assertFalse(motor_bot.overlaps(led))

        self.assertTrue(led.overlaps(motor_top))
        self.assertTrue(motor_top.overlaps(led))


    def test_segments_in_rec(self):
        r = Rectangle((0,0), (19,16))
        s = LineSegment(np.array([4,4]), np.array([11,9]))
        self.assertTrue(r.overlaps(s))
        self.assertTrue(s.overlaps(r))

        s2 = LineSegment(np.array([-2,6]), np.array([11,9]))
        self.assertTrue(r.overlaps(s2))
        self.assertTrue(s2.overlaps(r))


if __name__ == '__main__':
    unittest.main()
