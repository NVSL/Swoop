""".. module:: ShapelySwoop

.. moduleauthor:: Steven Swanson (swanson@cs.ucsd.edu)

ShapleySwoop is a Swoop extension that lets you extract geometry information
from the a Eagle file.  It adds a single method
:meth:`ShapelyEagleFilePart.get_geometry`, that returns an object that
represents the shape of :class:`EagleFilePart` objects that have a meaningful
shape (e.g., packages, pads, smds, wires, and rectangles, among others).

ShapelySwoop is built on the `Shapely library
<http://toblerity.org/shapely/manual.html>`_ , and you can use that libraries
operations to do whatever you'd like with the resulting geometry.

The core of ShapelySwoop is a the :class:`ShapelyEagleFilePart` class.  It
defines the interface ShapelySwoop adds to :class:`EagleFilePart` subclasses
for objects that have meaningful shapes.

The goal is to mimic what Eagle does, so if you ask for layer "Holes,"
:class:`Via` should give a circle with the same diameter as the hole in
the middle of the via, while "Top" should give you the diameter of the
restring.  

ShapelySwoop is currently very incomplete.  Check your results with the
debugging facilities before relying on it.

"""
import shapely.geometry as shapes
import shapely.affinity as affinity
import shapely
import shapely.ops
import math
import Swoop
import logging as log
import re
import copy
import collections
from Swoop.ext.VectorFont.VectorFont import vectorFont

dumping_geometry_works = True
try:
    import matplotlib
    from matplotlib import pyplot as plt
    from descartes import PolygonPatch
except RuntimeError as e:
    dumping_geometry_works = False
except ImportError as e:
    dumping_geometry_works = False

def getFacets(p1,p2, curve):
    
    if p2.x == p1.x:
        leveling_angle = math.radians(90)
    else:
        leveling_angle = -math.atan((p2.y-p1.y)/(p2.x-p1.x))
    p1p = p1#rotate(p1, leveling_angle, origin=p1, use_radians=True)
    p2p = affinity.rotate(p2, leveling_angle, origin=p1, use_radians=True) # rotate p2 around p1, so they lie on a horizontal line.  Finding the center is easier this way.
    
    l = (p2p.x-p1p.x)/2  # half the distance between the points.
    h = l/math.tan(-curve/2) # compute the distance to the center of the circle
                             # from the line connecting the two points.
    
    cp = shapes.Point(p1p.x + l, p1p.y-h) # the center of the (rotated) circle.
    c = affinity.rotate(cp, -leveling_angle, origin=p1, use_radians=True)  # unrotate the circle to get the center of the original circle.

    # how man line segments to use to approximate the curve.  Bound the angle between consecutive segments to 5 degrees. ALways have at least 10 segments.
    facets = max(10, int(math.ceil(abs(curve)/5)))
    
    points = []
    t = p1
    for i in range(1,facets + 2):  # Generate the segments by rotating p1
                                   # around the center a little bit at a time.
        points.append(t)
        t = affinity.rotate(t, curve/facets, origin=c, use_radians=True)

    return points

def getFacetsForWire(wire):
    if wire.get_curve() == 0:
        return [shapes.Point(wire.get_x1(), wire.get_y1()), shapes.Point(wire.get_x2(), wire.get_y2())]
    
    curve = math.radians(wire.get_curve())
    p1= shapes.Point(wire.get_x1(),wire.get_y1())
    p2= shapes.Point(wire.get_x2(),wire.get_y2())
    return getFacets(p1,p2,curve)


def facetizeWire(wire):

    if wire.get_curve() == 0:
        return [wire]

    points = getFacetsForWire (wire)
    wires =[]
    for i in range(0, len(points)-1):
        wires.append(Swoop.Wire()
                     .set_points(points[i].x, points[i].y, points[i+1].x, points[i+1].y)
                     .set_layer(wire.get_layer())
                     .set_width(wire.get_width()))
    return wires

class ShapelyEagleFilePart():

    POLYGONIZE_NONE = 0;
    POLYGONIZE_BEST_EFFORT = 1;
    POLYGONIZE_STRICT = 2;

    def __init__(self):
        pass

    def _apply_width(self, shape, width=None, **options):

        if options and "apply_width" in options:
            aw = options["apply_width"]
        else:
            aw = True

        #print "aw = {} for {}".format(aw, shape)
        if width is None:
            width = self.get_width()
            
        if aw and width > 0 :
            if options and "width_smoothness" in options:
                r = options["width_smoothness"]
            else:
                r = 16
            return shape.buffer(width/2, resolution=r)
        else:
            return shape

    @staticmethod
    def _do_transform(shape, rotation, mirrored, rotation_origin=(0,0), scale_origin=(0,0)):
        if shape is None or shape.is_empty:
            return shape
        r = shape
        r = affinity.rotate(r, rotation, origin=rotation_origin)
        r = affinity.scale(r, xfact=(-1 if mirrored else 1), origin=scale_origin)
        return r;

    def _apply_transform(self, shape, rotation_origin=(0,0), scale_origin=(0,0)):
        return ShapelyEagleFilePart._do_transform(shape, self.get_rotation(), self.get_mirrored(), rotation_origin=rotation_origin, scale_origin=scale_origin)

    @staticmethod
    def _do_inverse_transform(shape, rotation, mirrored, rotation_origin=(0,0), scale_origin=(0,0)):
        if shape is None or shape.is_empty:
            return shape
        r = shape
        r = affinity.scale(r, xfact=(-1 if mirrored else 1), origin=scale_origin)
        r = affinity.rotate(r, -rotation, origin=rotation_origin)
        return r;

    def _apply_inverse_transform(self, shape, rotation_origin=(0,0), scale_origin=(0,0)):
        return ShapelyEagleFilePart._do_inverse_transform(shape, self.get_rotation(), self.get_mirrored, rotation_origin=rotation_origin, scale_origin=scale_origin)

    def _layer_matches(self, query, layer_name):
        if query is None:
            return True
        
        if isinstance(query, str):
            return query == layer_name
        elif  isinstance(query, int):
            return query == self.get_file().layer_name_to_number(layer_name)
        elif  isinstance(query, Swoop.Layer):
            return query == query.get_name()
        elif isinstance(query, list):
            return layer_name in query
        elif hasattr(query, '__call__'):
            return query(layer_name)
        else:
            raise Swoop.SwoopError("illegal layer query: {}".format(query))
    
    def _do_polygonize_wires(self, wires, layer_query, **options):
        
        """
        Try to deal with lines enclose areas.
        """
        if "polygonize_wires" in options:
            mode = options["polygonize_wires"]
        else:
            mode = ShapelyEagleFilePart.POLYGONIZE_NONE

        #log.debug("_do_polygonize_wires {} {} {}".format(mode, wires, layer_query))
        if mode == ShapelyEagleFilePart.POLYGONIZE_NONE:
            return shapely.ops.unary_union(wires.get_geometry(layer_query=layer_query, **options))
        else:
            widths = wires.get_width().unique();
            result = shapes.LineString()

            for w in widths:
                o = copy.copy(options)
                o["apply_width"]=False
                geometry = wires.with_width(w).get_geometry(layer_query=layer_query,**o);
                polygons, dangles, cuts, invalids = shapely.ops.polygonize_full(list(geometry))
                if mode == ShapelyEagleFilePart.POLYGONIZE_STRICT:
                    if len(dangles) + len(cuts) + len(invalids) > 0:
                        raise SwoopError("Tried to polygonize non-polygon ({})".format(self))

                combined = shapely.ops.unary_union([polygons, dangles, cuts, invalids])
                combined = self._apply_width(combined, width=w, **options)

                result = result.union(combined)

        if mode != ShapelyEagleFilePart.POLYGONIZE_STRICT and mode != ShapelyEagleFilePart.POLYGONIZE_BEST_EFFORT:
            raise Swoop.SwoopError("Unknown polygonize mode: {}".mode)

        return result

    def get_geometry(self, layer_query=None, **options):
        """Get the Shapely geometry for this :code:`EagleFilePart` object on a particular layer.

        If you pass :code:`polygonize_wires`, then this function will try to
        deal with lines that enclose areas intelligently.

        * For :code:`ShapelyEagleFilePart.POLYGONIZE_NONE` (the default), do nothing but return the
          normal geometry for the lines.  As near as I can tell, this is what Eagle does.
        
        * For :code:`ShapelyEagleFilePart.POLYGONIZE_BEST_EFFORT`, use shapely to build what
          polygons it can, and return everything else as wires (i.e., lines).  The rule is that
          we try to merge wires of the same width into polygons.

        * For :code:`ShapelyEagleFilePart.POLYGONIZE_STRICT`, do the same thing, but throw an error if there
          are any invalid, incomplete polygons.

        :param layer_query: The layer you want the geometry for.  :code:`None` for everything. (Default = :code:`None`)
        :param polygonize_wires: Whether you want to polygonize wires.  (Default = :code:`ShapelyEagleFilePart.POLYGONIZE_NONE`)
        :returns: The geometry
        :rtype: A Shapely geometry object

        """

        if options and "fail_on_missing" in options and options["fail_on_missing"]:
            raise NotImplemented("Can't get shape for {}".format(self.__class__.__name__()))
        else:
            return shapes.LineString()

class BoardFile(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, **options):
        brd = Swoop.From(self)


        wires = self._do_polygonize_wires(
                                          brd.
                                          get_plain_elements().
                                          with_type(Wire),
                                          layer_query=layer_query,
                                          **options)

        parts = (brd.get_elements() +
                 brd.get_plain_elements().without_type(Wire) +
                 brd.get_signals().get_wires() +
                 brd.get_signals().get_vias())

        return shapely.ops.unary_union(parts.get_geometry(layer_query=layer_query, **options) + [wires])
            
class Circle(ShapelyEagleFilePart):
    # Fixme:  Cut out center
    
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, **options):
        if self._layer_matches(layer_query, self.get_layer()):
            circle = shapes.Point(self.get_x(), self.get_y()).buffer(self.get_radius())
            if "fill_circles" in options and options['fill_circles']:
                return circle
            else:
                return shapes.LinearRing(circle.exterior)
        else:
            return shapes.LineString()
    
class Rectangle(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, **options):
        

        if self._layer_matches(layer_query, self.get_layer()):

            # if self.get_mirrored():
            #     mirror = shapely.affinity.scale(xfact=-1, center=(0,0,0))
            # else:
            #     mirror = shapely.affinity.scale(xfact=1, center=(0,0,0))

            box = shapes.box(min(self.get_x1(), self.get_x2()),
                             min(self.get_y1(), self.get_y2()),
                             max(self.get_x1(), self.get_x2()),
                             max(self.get_y1(), self.get_y2()))
            # When I select "mirrored" in Eagle, it just modifies the rotation angle.
            if self.get_mirrored():
                angle = 180-self.get_rotation()
            else:
                angle = self.get_rotation()
            box = affinity.rotate(box, angle)
            return box;
        else:
            return shapes.LineString()

class Polygon(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self)

    def get_geometry(self, layer_query=None, **options):
        # if self.get_width() == 0 and options["hide_zero_width_items"]:
        #     return shapes.LineString()

        if self._layer_matches(layer_query, self.get_layer()):
            polygon = shapes.Polygon([(v.get_x(), v.get_y()) for v in self.get_vertices()])
            return self._apply_width(polygon, **options)
        else:
            return shapes.LineString()
            

class Package(ShapelyEagleFilePart):
    
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

        
    def get_geometry(self, layer_query=None, **options):
        package = Swoop.From(self)

        if "polygonize_wires" in options:
            pw = options["polygonize_wires"]
        else:
            pw = ShapelyEagleFilePart.POLYGONIZE_NONE
            
        wires = self._do_polygonize_wires(package.
                                          get_drawing_elements().
                                          with_type(Wire),
                                          layer_query=layer_query,
                                          **options)

        parts = (package.get_drawing_elements().without_type(Wire) +
                 package.get_smds() +
                 package.get_pads())

        return shapely.ops.unary_union(parts.get_geometry(layer_query=layer_query, **options) + [wires])
    
        
class Element(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);


    @staticmethod
    def _do_transform(shape, x,y,rotation,mirrored):
        if shape is None or shape.is_empty:
            return shape
        r = ShapelyEagleFilePart._do_transform(shape, rotation, mirrored)
        return affinity.translate(r, x, y)

    @staticmethod
    def _do_inverse_transform(shape, x,y,rotation,mirrored):
        if shape is None or shape.is_empty:
            return shape

        r = affinity.translate(shape, xoff=-x, yoff=-y)
        return ShapelyEagleFilePart._do_inverse_transform(r, rotation,mirrored)
        
    def _apply_transform(self, shape):
        return Element._do_transform(shape, self.get_x(), self.get_y(), self.get_rotation(), self.get_mirrored())
        #r = ShapelyEagleFilePart._apply_transform(self, shape)
        #return affinity.translate(r, xoff=self.get_x(), yoff=self.get_y())

    def _apply_inverse_transform(self, shape):
        return Element._do_inverse_transform(shape, self.get_x(), self.get_y(), self.get_rotation(), self.get_mirrored())

    def map_board_geometry_to_package_geometry(self, shape):
        return self._apply_inverse_transform(shape)

    def get_geometry(self, layer_query=None, **options):
        if self.get_mirrored() and layer_query is not None:
            layer_query = self.get_file().get_mirrored_layer(layer_query)

        #log.debug("Getitng geometry for {}. {} {}".format(self.get_name(), layer_query, polygonize_wires))
        shape = self.find_package().get_geometry(layer_query=layer_query, **options);
        return self._apply_transform(shape)

class Wire(ShapelyEagleFilePart):
    # Fixme: handle curves
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, **options):
        # if self.get_width() == 0 and options["hide_zero_width_items"]:
        #     return shapes.LineString()

        if self._layer_matches(layer_query, self.get_layer()):
            shape = shapes.LineString(getFacetsForWire(self))

            shape = self._apply_width(shape, **options)
            return shape
        else:
            return shapes.LineString()

class Smd(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, **options):

        DRU = self.get_DRU();
        if (self._layer_matches(layer_query, self.get_layer()) or
            (self._layer_matches(self.get_layer(), "Top") and self._layer_matches(layer_query, "tStop")) or
            (self._layer_matches(self.get_layer(), "Bottom") and self._layer_matches(layer_query, "bStop"))):
            box = shapes.box(self.get_x()-self.get_dx()/2.0,
                             self.get_y()-self.get_dy()/2.0,
                             self.get_x() + self.get_dx()/2.0,
                             self.get_y() + self.get_dy()/2.0)
            if self._layer_matches(layer_query,"tStop") or self._layer_matches(layer_query, "bStop"):
                box = box.buffer(computeStopMaskExtra(min(self.get_dx(), self.get_dy()), DRU))
            return self._apply_transform(box, rotation_origin=(self.get_x(), self.get_y()), scale_origin=(self.get_x(), self.get_y()))
        else:
             return shapes.LineString()
             
        
class Module(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);
        
class ModuleInst(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Gate(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Dimension(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Text(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, **options):
        if not self._layer_matches(layer_query, self.get_layer()):
            return shapes.LineString()

        if self.get_align() == "center":
            h_align = "center"
            v_align = "center"
        else:
            m = re.match("(\w+)-(\w+)", self.get_align())
            v_align = m.group(1)
            h_align = m.group(2)

        lines = self.get_text().split("\n")

        stroke_width = self.get_ratio()/100.0
        yscale = (vectorFont.base_height - stroke_width)/vectorFont.base_height
        RenderedLine = collections.namedtuple("RenderedLine", ["width", "shape"])

        rendered_lines = []
        for l in lines:
            cursor = 0
            text = shapes.LineString()
            for character in l:
                glyph_data = vectorFont.glyphs[character]
                if glyph_data.width == 0:
                    xscale = 1
                else:
                    xscale = ((glyph_data.width - stroke_width/2)/glyph_data.width + glyph_data.width)/2  # emperical formula
                glyph = shapes.MultiLineString(glyph_data.lines)
                glyph = affinity.scale(glyph,# the width of the lines we use for drawing must fit within the line height.
                                       yfact=yscale,
                                       xfact=xscale,
                                       origin=(0,0)) 
                # Put the character at the cursor and move it down to accomodate the stroke thickness.  emprical value
                glyph = affinity.translate(glyph,
                                           cursor + stroke_width/2,
                                           -stroke_width/2); 
                text = text.union(glyph)
                effective_width = glyph_data.width
                cursor = cursor + effective_width + vectorFont.base_kerning
            width = cursor - vectorFont.base_kerning
            rendered_lines.append(RenderedLine(width, text))

        max_width = max([x.width for x in rendered_lines])

        baseline_skip = vectorFont.base_height + self.get_distance()/100.0*vectorFont.base_height;

        text = shapes.LineString()
        v_cursor = 0
        for l in rendered_lines:
            if h_align == "left":
                dx = 0
            elif h_align == "center":
                dx = (max_width - l.width)/2 - max_width/2
            elif h_align == "right":
                dx = (max_width - l.width) - max_width
            else:
                assert False, "illegal h_align: {}".format(h_align)
            text = text.union(affinity.translate(l.shape, dx, v_cursor))

            v_cursor = v_cursor - baseline_skip

        height = -v_cursor - self.get_distance()/100.0*vectorFont.base_height

        if v_align == "top":
            dy = 0
        elif v_align == "center": 
            dy = height/2
        elif v_align == "bottom":
            dy = height
        else:
            assert False, "illegal v_align: {}".format(v_align)

        text = affinity.translate(text,0,dy)

        text = affinity.scale(text, xfact=self.get_size(), yfact=self.get_size(), origin=(0,0))
        text = affinity.translate(text, self.get_x(), self.get_y())
        text = self._apply_transform(text, rotation_origin=(self.get_x(), self.get_y()), scale_origin=(self.get_x(), self.get_y()))
        text = self._apply_width(text, width=stroke_width*self.get_size(),**options)
        return text
        
class Frame(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

def scaleAndBound(value, maxv, minv, percent):
    extra = percent * value
    extra = max(extra, minv)
    extra = min(extra, maxv)
    return extra
    
def computeStopMaskExtra(radius, DRU):
    return scaleAndBound(radius, DRU.mvStopFrame, DRU.mlMinStopFrame, DRU.mlMaxStopFrame)
    
class Hole(ShapelyEagleFilePart):
    # Fixme : Generate tStop and bStop
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, **options):
        DRU = self.get_DRU();
        if self._layer_matches(layer_query, "Holes"):
            circle = shapes.Point(self.get_x(), self.get_y()).buffer(self.get_drill()/2)
            return circle;
        elif self._layer_matches(layer_query, "tStop") or self._layer_matches(layer_query, "bStop"):
             radius = self.get_drill()/2
             circle = shapes.Point(self.get_x(), self.get_y()).buffer(radius + computeStopMaskExtra(radius, DRU))
             return circle;
        else:
            return shapes.LineString()
        
class Pad(ShapelyEagleFilePart):
    # Fixme: handle other shapes.
    # Fixme : Generate tStop and bStop correctly
    # Fixme: Pads should be different sizes or different layers.
    # Fixme: Pads should maybe generate keepout geometry as well?
        
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def render_pad(self, layer_query, drill, **options):

        DRU = self.get_DRU()
        if self._layer_matches(layer_query, "Holes"):
            hole = shapes.Point(self.get_x(), self.get_y()).buffer(drill/2)
            return hole;

        radius = (drill/2);
        radius = radius + scaleAndBound(radius, DRU.rvPadTop, DRU.rlMinPadTop, DRU.rlMaxPadTop)
        
        if layer_query is not None and self.get_file().get_layer(layer_query).get_number() > 16 and not self._layer_matches(layer_query, "tStop") and  not self._layer_matches(layer_query,"bStop"):
            return shapes.LineString()

        if self.get_shape() == "square":
            shape = shapes.box(self.get_x() - radius ,
                               self.get_y() - radius,
                               self.get_x() + radius,
                               self.get_y() + radius)
        elif self.get_shape() == "round" or self.get_shape() is None:
            shape = shapes.point.Point(self.get_x(), self.get_y()).buffer(radius)
        elif self.get_shape() == "octagon":
            shape = shapes.box(self.get_x() - radius,
                               self.get_y() - radius,
                               self.get_x() + radius,
                               self.get_y() + radius)
            shape = shape.intersection(affinity.rotate(shape, 45))
        elif self.get_shape() == "long":
            shape = shapely.ops.unary_union([shapes.point.Point(self.get_x() + DRU.psElongationLong/100.0 * radius,
                                                                self.get_y()).buffer(radius),
                                             shapes.point.Point(self.get_x() - DRU.psElongationLong/100.0 * radius,
                                                                self.get_y()).buffer(radius),
                                             shapes.box(self.get_x() - DRU.psElongationLong/100.0 * radius,
                                                        self.get_y() - radius,
                                                        self.get_x() + DRU.psElongationLong/100.0 * radius,
                                                        self.get_y() + radius)])
        elif self.get_shape() == "offset":
            shape = shapely.ops.unary_union([shapes.point.Point(self.get_x() + DRU.psElongationOffset/100.0 * radius * 2,
                                                                self.get_y()).buffer(radius),
                                             shapes.point.Point(self.get_x(),
                                                                self.get_y()).buffer(radius),
                                             shapes.box(self.get_x(),
                                                        self.get_y() - radius,
                                                        self.get_x() + DRU.psElongationLong/100.0 * radius * 2,
                                                        self.get_y() + radius)
                                         ])
        else:
            raise Swoop.SwoopError("Unknown pad shape: '{}'".format(self.get_shape()))

        if shape is not None:
            if self._layer_matches(layer_query,"tStop") or self._layer_matches(layer_query, "bStop"):
                shape = shape.buffer(computeStopMaskExtra(radius, DRU))

        if options and "fail_on_missing" in options and options["fail_on_missing"] and shape is None:
            raise NotImplemented("Geometry for pad shape '{}' is not implemented yet.".format(self.get_shape()))
        elif shape is None:
            shape = shapes.LineString()

        return shape

    def get_geometry(self, layer_query=None, **options):

        shape = self.render_pad(layer_query, self.get_drill())
        return self._apply_transform(shape, rotation_origin=(self.get_x(), self.get_y()), scale_origin=(self.get_x(), self.get_y()))
                               
class Via(Pad):
    def __init__(self):
        Pad.__init__(self);

    def get_geometry(self, layer_query=None, **options):
        # This isn't quite right.  Via size is set in the DRC file.
        DRU = self.get_DRU()
        if (self._layer_matches(layer_query, "tStop") or self._layer_matches(layer_query, "bStop")) and self.get_drill() < DRU.mlViaStopLimit:
            return shapes.LineString()
        else:
            return self.render_pad(layer_query, self.get_drill(), **options)

class Pin(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Label(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Junction(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class GeometryDump:
    """Utility class for dumping multiple Shapley geometry objects.

    You can only have one of these going at once, otherwise the output will get
    confused.

    """
    RED = "#ff0000"
    GREEN = "#00ff00"
    BLACK = "#000000"
    WHITE = "#ffffff"
    GRAY = "#888888"
    BLUE = "#0000ff"
    YELLOW = "#ff00ff"
    PURPLE = "#ff00ff"
    
    
    def __init__(self, title, filename):
        """
        Prepare to dump geometry.  It'll end up in :code:`filename` (a pdf) with :code:`title` as the title.
        """
        if not dumping_geometry_works:
            log.warning("Can't use matplotlib on macosx due to virtualenv.  Dumping to pdf won't work.  Talk to Steve if you need to fix.")
            return

        self.everything = shapes.LineString()
        self.title = title
        self.filename = filename
        self.fig = plt.figure(2, figsize=(10,10), dpi=90)
        self.subfig = self.fig.add_subplot(111)

        
    def add_geometry(self, mp, width=0, alpha=1, facecolor='none', edgecolor="#0000ff"):
        """
        Add a piece of geometry to the output.
        
        :param mp: The geometry.
        :param width: the width of the border.
        :param alpha: alpha blending value.
        :param facecolor: color of the inside of the geometry.
        :param edgecolor: color of the border.
        
        """
        if not dumping_geometry_works:
            log.warn("Can't dump geometry because matplotlib doesn't work in virtualenv.")
            return

        if not mp:
            return
        if isinstance(mp, shapely.geometry.polygon.Polygon):
            l = [mp]
        else:
            l = mp.geoms
        for p in l:
            if not isinstance(p, shapely.geometry.polygon.Polygon):
                self.subfig.plot([i[0] for i in p.coords], [i[1] for i in p.coords], color=facecolor)
            elif p:
                ring_patch = PolygonPatch(p, facecolor=facecolor, edgecolor=edgecolor, linewidth=width, alpha=alpha)
                self.subfig.add_patch(ring_patch)
            self.everything= self.everything.union(p)


    def dump(self):
        """
        Write out the geometry.
        """
        bounds = self.everything.bounds
        width  = abs(bounds[2] - bounds[0])
        height = abs(bounds[3] - bounds[1])
        xrange = [bounds[0] - 0.1*width,  bounds[2] + 0.1*width]
        yrange = [bounds[1] - 0.1*height, bounds[3] + 0.1*height]
        self.subfig.set_xlim(*xrange)
        self.subfig.set_ylim(*yrange)
        self.subfig.set_aspect(1)

        self.subfig.xaxis.set_ticks(list(range(int(math.floor(float(bounds[0]))), int(math.ceil(float(bounds[2]))))))
        self.subfig.yaxis.set_ticks(list(range(int(math.floor(float(bounds[1]))), int(math.ceil(float(bounds[3]))))))
        self.subfig.grid(True)        
        plt.title(self.title)
    
        self.fig.savefig(self.filename, format='pdf')
        self.fig.clf()

def dump_geometry(geometry, title, filename, color="#888888"):
    """
    Dump a Shapely :code:`geometry` object to :code:`filename`, title the figure it draws :code:`title`, and draw it in :code:`color`
    """
    
    dump = GeometryDump(title,filename)
    dump.add_geometry(geometry, facecolor=color,alpha=1)
    dump.dump()

def polygon_as_svg(shapely_polygon, svgclass=None, style=None, close_paths=True):
    if svgclass is None:
        svgclass = ""
    else:
        svgclass = "class='{}'".format(svgclass)
        
    if style is None:
        style = ""
    else:
        style = "style='{}'".format(style)

    if isinstance(shapely_polygon, shapely.geometry.polygon.Polygon) or isinstance(shapely_polygon, shapes.LineString) :
        l = [shapely_polygon]
    else:
        l = shapely_polygon.geoms

    r = ""

    if close_paths:
        closer = " Z"
    else:
        closer = ""
        
    for i in l:
        if isinstance(i, shapes.LineString):
            data = "M{} {}".format(i.coords[0][0],i.coords[0][1]) + " ".join(["L{} {}".format(x[0],x[1]) for x in i.coords[1:]])
        else:
            data = "M{} {} ".format(i.exterior.coords[0][0],i.exterior.coords[0][1]) + " ".join(["L{} {}".format(x[0],x[1]) for x in i.exterior.coords[1:]]) + closer
            for k in i.interiors:
                data = data + "M{} {} ".format(k.coords[0][0],k.coords[0][1]) + " ".join(["L{} {}".format(x[0],x[1]) for x in k.coords[1:]]) + closer
        
        r = r + ("<path {} {} d='{}'/>".format(svgclass, style, data))
    return r


def hash_geometry(geo):
    """Hash a shapley geometry object.  The algorithm is a little ad hoc: We
    converting it to string, rounding all the floats found in the string, and
    sort the contents of the string character-wise, and take a hash of the
    result.  This handles allows for matches even when the answers differ very
    slightly due to floating point problems and the unfortunate fact that
    Shapely doesn't always return objects in the same order.
    

    """
    def trim(match):
        return str(round(float(match.group(0)), 5))
    v = re.sub("-?\d+(\.\d+)?", trim, str(geo))
    
    return hash("".join(sorted(v)))



import sys
ShapelySwoop = Swoop.Mixin(sys.modules[__name__], "Shapely")
