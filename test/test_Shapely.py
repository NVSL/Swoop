import unittest
import Swoop
import Swoop.ext.ShapelySwoop
from Swoop.ext.ShapelySwoop import ShapelyEagleFilePart as SEFP
import os
import shapely
import re
from Swoop.ext.ShapelySwoop import GeometryDump as GeoDump
from Swoop.ext.ShapelySwoop import ShapelySwoop as ShapelySwoop
from Swoop.ext.ShapelySwoop import hash_geometry as hash_geo

def dump(test, geo, title, c, color):
    hash = hash_geo(geo)
    print """("{}", {}, "{}"),""".format(test[0], hash, test[2])
    Swoop.ext.ShapelySwoop.dump_geometry(geo, "{} ({})".format(title,hash) , "{0:03d}.pdf".format(c), color)


class TestShapely(unittest.TestCase):
    
    def setUp(self):
        self.me = os.path.dirname(os.path.realpath(__file__))
        self.testbrd1 = ShapelySwoop.from_file(self.me + "/inputs/shapeTest1.brd")
        self.testbrd2 = ShapelySwoop.from_file(self.me + "/inputs/shapeTest2.brd")
        self.testbrd3 = ShapelySwoop.from_file(self.me + "/inputs/shapeTest3.brd")

        self.boardtest = ShapelySwoop.from_file(self.me + "/inputs/test_saving.brd")
        
    def test_element(self):
        tests = [
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd1).get_elements().get_geometry())", 6504294297733679555, "#000000"),
            ("self.testbrd1.get_element('U$1').get_geometry()", -2789613719270802873, "#000000"),
            ("self.testbrd1.get_element('U$2').get_geometry()", 1650928756827396133, "#000000"),
            ("self.testbrd1.get_element('U$2').get_geometry(layer_query='Top')", -2316119240083132091, "#ff0000"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd1).get_elements().get_geometry(layer_query='Top'))", -1405743727263307022, "#ff0000"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry())", -8790793505350002856, "#000000"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='tPlace'))", 4675948399285872422, "#000000"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='bPlace'))", -8147871516156910189, "#000000"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_element('U$1').get_geometry(layer_query='Top'))", -5301026454227315084, "#ff0000"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_element('U$1').get_geometry(layer_query='Bottom'))", -5999577188847035307, "#0000ff"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='tTest2'))", -8049353574747205132, "#ff00ff"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='bTest2'))", 3934649351525441535, "#ff00ff"),
            ("shapely.ops.cascaded_union(self.boardtest.get_geometry())", -5479704724911999023, "#000000"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='Holes'))", 7701255143946384531, "#000000"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='tKeepout', polygonize_wires=SEFP.POLYGONIZE_BEST_EFFORT))", -5168448055214345009, "#000000"),
            ("shapely.ops.cascaded_union(Swoop.From(self.testbrd2).get_elements().get_geometry(layer_query='tKeepout', polygonize_wires=SEFP.POLYGONIZE_NONE))", 7043720151262557027, "#000000"),
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
            self.assertEqual(hash_geo(geo), i[1], "Geometry failure on test {}".format(c))
            c = c + 1
