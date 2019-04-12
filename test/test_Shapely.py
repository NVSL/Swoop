import unittest
import Swoop
import Swoop.ext.ShapelySwoop
from Swoop.ext.ShapelySwoop import ShapelyEagleFilePart as SEFP
import os
import sys
import shapely
import re
from Swoop.ext.ShapelySwoop import GeometryDump as GeoDump
from Swoop.ext.ShapelySwoop import ShapelySwoop as ShapelySwoop
from Swoop.ext.ShapelySwoop import hash_geometry as hash_geo

def dump(test, geo, title, c, color):
    hash = hash_geo(geo)
    print("""("{}", {}, "{}"),""".format(test[0], hash, test[2]))
    #Swoop.ext.ShapelySwoop.dump_geometry(geo, "{} ({})".format(title,hash) , "{0:03d}.pdf".format(c), color)


class TestShapely(unittest.TestCase):
    
    def setUp(self):
        self.me = os.path.dirname(os.path.realpath(__file__))
        self.testbrd1 = ShapelySwoop.open(self.me + "/inputs/shapeTest1.brd")
        self.testbrd2 = ShapelySwoop.open(self.me + "/inputs/shapeTest2.brd")
        self.testbrd3 = ShapelySwoop.open(self.me + "/inputs/shapeTest3.brd")
        self.testbrd5 = ShapelySwoop.open(self.me + "/inputs/shapeTest5.brd")

        self.boardtest = ShapelySwoop.open(self.me + "/inputs/test_saving.brd")
        self.curvetest = ShapelySwoop.open(self.me + "/inputs/curve_test.brd")
        self.textTest =  ShapelySwoop.open(self.me + "/inputs/ShapelyTextTest.brd")

    @unittest.skipIf(sys.version_info >= (3,0), "hashes changed in Py3k")
    def test_element(self):
        tests = [
("self.testbrd5.get_element('U1_8_DISPLAY_2').get_geometry(layer_query='Top')", 6132383853822173047, "#ff0000"),
("shapely.ops.cascaded_union(Swoop.From(self.testbrd1).get_elements().get_geometry())", 3019186457803611298, "#000000"),
("self.testbrd1.get_element('U$1').get_geometry()", -3905289220812110970, "#000000"),
("self.testbrd1.get_element('U$2').get_geometry()", 7149781817599939921, "#000000"),
("self.testbrd1.get_element('U$2').get_geometry(layer_query='Top')", -592898454734508401, "#ff0000"),

("shapely.ops.cascaded_union(Swoop.From(self.testbrd1).get_elements().get_geometry(layer_query='Top'))", 8175878824730081580, "#ff0000"),
("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry())", 5269961155734272488, "#000000"),
("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='tPlace'))", 1859631802219965328, "#000000"),
("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='bPlace'))", 2736247162424655875, "#000000"),
("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_element('U$1').get_geometry(layer_query='Top'))", 3934072499983631454, "#ff0000"),
("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_element('U$1').get_geometry(layer_query='Bottom'))", -2769906635547204865, "#0000ff"),
("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='tTest2'))", -7429633510224712854, "#ff00ff"),
("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='bTest2'))", -4332886659677625739, "#ff00ff"),
("shapely.ops.cascaded_union(self.curvetest.get_geometry())", -1509359968350351720, "#000000"),
("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='Holes'))", 7495755189664780231, "#000000"),
("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='tKeepout', polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT))", 8476310128833764099, "#000000"),
("shapely.ops.cascaded_union(Swoop.From(self.textTest).get_geometry(layer_query='tPlace', polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT))", 1368976510290104576, "#000000"),
        ]

        c = 0
        # We compare the geometry the commands produced with a hash of the
        # correct geometry.  If you need to update the correct answers,
        # uncomment the "dump" below, and comment out the assert.  Run
        # "frameworkpython -m unittest test_Shapely.TestShapely.test_element"
        # and then look at all ???.pdf files.  Check that they correct.  When
        # they are replace the array above with the output of the command.
        # It's the commands with the updated hashes.  Questions? ask Steve.
        for i in tests:
            geo = eval(i[0])
            #dump(i, geo, i[0], c, i[2])
            #print(geo)
            self.assertEqual(hash_geo(geo), i[1], "Geometry failure on test {}".format(c))
            c = c + 1

