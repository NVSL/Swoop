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

dumping_geometry_works = True
try:
    import matplotlib
    from matplotlib import pyplot as plt
    from descartes import PolygonPatch
except RuntimeError as e:
    dumping_geometry_works = False
              

strict = False;

class ShapelyEagleFilePart():

    def __init__(self):
        pass

    def _apply_width(self, shape, width=None):
        if width is None:
            width = self.get_width()
            
        if width > 0:
            return shape.buffer(width/2, resolution=16)
        else:
            return shape

    def _apply_transform(self, shape, origin=(0,0)):
        if shape.is_empty:
            return shape
        r = shape
        r = affinity.rotate(r, self.get_rotation(), origin=origin)
        r = affinity.scale(r, xfact=(-1 if self.get_mirrored() else 1), origin=(0,0))
        return r;

    def _apply_inverse_transform(self, shape, origin=(0,0)):
        if shape.is_empty:
            return shape
        r = shape
        r = affinity.scale(r, xfact=(-1 if self.get_mirrored() else 1), origin=(0,0))
        r = affinity.rotate(r, -self.get_rotation(), origin=origin)
        return r;

    def _layer_matches(self, query, layer_name):
        if query is None:
            return True
        
        if isinstance(query, str):
            return query == layer_name
        elif  isinstance(query, int):
            return query == self.get_file().layer_number_to_name(layer)
        elif  isinstance(query, Swoop.Layer):
            return query == query.get_name()
        else:
            raise Swoop.SwoopError("illegal layer query: {}".format(query))

    POLYGONIZE_NONE = 0;
    POLYGONIZE_BEST_EFFORT = 1;
    POLYGONIZE_STRICT = 2;
    
    def _do_polygonize_wires(self, mode, wires, layer_query):
        
        """
        Try to deal with lines enclose areas.
        """
       
        #log.debug("_do_polygonize_wires {} {} {}".format(mode, wires, layer_query))
        if mode == ShapelyEagleFilePart.POLYGONIZE_NONE:
            return shapely.ops.unary_union(wires.get_geometry(layer_query=layer_query))
        else:
            widths = wires.get_width().unique();
            result = shapes.LineString()

            for w in widths:
                geometry = wires.with_width(w).get_geometry(apply_width=False,layer_query=layer_query);
                polygons, dangles, cuts, invalids = shapely.ops.polygonize_full(list(geometry))
                if mode == ShapelyEagleFilePart.POLYGONIZE_STRICT:
                    if len(dangles) + len(cuts) + len(invalids) > 0:
                        raise SwoopError("Tried to polygonize non-polygon ({})".format(self))

                combined = shapely.ops.unary_union([polygons, dangles, cuts, invalids])
                combined = self._apply_width(combined, width=w)

                result = result.union(combined)

        if mode != ShapelyEagleFilePart.POLYGONIZE_STRICT and mode != ShapelyEagleFilePart.POLYGONIZE_BEST_EFFORT:
            raise Swoop.SwoopError("Unknown polygonize mode: {}".mode)

        return result

    def get_geometry(self, layer_query=None, polygonize_wires=POLYGONIZE_NONE):
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
        if strict:
            raise NotImplemented("Can't get shape for {}".format(self.__class__.__name__()))
        else:
            return shapes.LineString()

class BoardFile(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):
        brd = Swoop.From(self)

        wires = self._do_polygonize_wires(polygonize_wires,
                                          brd.
                                          get_plain_elements().
                                          with_type(Wire),
                                          layer_query=layer_query)

        parts = (brd.get_elements() +
                 brd.get_plain_elements().without_type(Wire) +
                 brd.get_signals().get_wires() +
                 brd.get_signals().get_vias())

        return shapely.ops.unary_union(parts.get_geometry(layer_query=layer_query, polygonize_wires=polygonize_wires) + [wires])
            
class Circle(ShapelyEagleFilePart):
    # Fixme:  Cut out center
    
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):
        if self._layer_matches(layer_query, self.get_layer()):
            circle = shapes.Point(self.get_x(), self.get_y()).buffer(self.get_radius())
            return self._apply_width(circle)
        else:
            return shapes.LineString()
    
class Rectangle(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):
        assert not self.get_mirrored()  # When I select "mirrored" in Eagle, it just modifies the rotation angle.

        if self._layer_matches(layer_query, self.get_layer()):

            # if self.get_mirrored():
            #     mirror = shapely.affinity.scale(xfact=-1, center=(0,0,0))
            # else:
            #     mirror = shapely.affinity.scale(xfact=1, center=(0,0,0))

            box = shapes.box(min(self.get_x1(), self.get_x2()),
                             min(self.get_y1(), self.get_y2()),
                             max(self.get_x1(), self.get_x2()),
                             max(self.get_y1(), self.get_y2()))
            box = affinity.rotate(box, self.get_rotation())

            return box;
        else:
            return shapes.LineString()

class Polygon(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self)

    def get_geometry(self, layer_query=None, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):
        if self._layer_matches(layer_query, self.get_layer()):
            polygon = shapes.Polygon([(v.get_x(), v.get_y()) for v in self.get_vertices()])
            return self._apply_width(polygon)
        else:
            return shapes.LineString()
            

class Package(ShapelyEagleFilePart):
    
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

        
    def get_geometry(self, layer_query=None, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):
        package = Swoop.From(self)

        wires = self._do_polygonize_wires(polygonize_wires,
                                          package.
                                          get_drawing_elements().
                                          with_type(Wire),
                                          layer_query=layer_query)

        parts = (package.get_drawing_elements().without_type(Wire) +
                 package.get_smds() +
                 package.get_pads())

        
        return shapely.ops.unary_union(parts.get_geometry(layer_query=layer_query, polygonize_wires=polygonize_wires) + [wires])
    
        
class Element(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def _apply_transform(self, shape):
        r = ShapelyEagleFilePart._apply_transform(self, shape)
        return affinity.translate(r, xoff=self.get_x(), yoff=self.get_y())

    def _apply_inverse_transform(self, shape):
        r = affinity.translate(shape, xoff=-self.get_x(), yoff=-self.get_y())
        return ShapelyEagleFilePart._apply_inverse_transform(self, r)

    def map_board_geometry_to_package_geometry(self, shape):
        return self._apply_inverse_transform(shape)

    def get_geometry(self, layer_query=None, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):
        if self.get_mirrored() and layer_query is not None:
            layer_query = self.get_file().get_mirrored_layer(layer_query)

        #log.debug("Getitng geometry for {}. {} {}".format(self.get_name(), layer_query, polygonize_wires))
        shape = self.find_package().get_geometry(layer_query=layer_query, polygonize_wires=polygonize_wires);
        return self._apply_transform(shape)

class Wire(ShapelyEagleFilePart):
    # Fixme: handle curves
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, apply_width=True, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):
        if self._layer_matches(layer_query, self.get_layer()):
            line = shapes.LineString([(self.get_x1(), self.get_y1()), (self.get_x2(), self.get_y2())])
            if apply_width:
                line = self._apply_width(line)
            return line
        else:
            return shapes.LineString()
    


class Smd(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):
        if self._layer_matches(layer_query, self.get_layer()):
            box = shapes.box(self.get_x()-self.get_dx()/2.0,
                             self.get_y()-self.get_dy()/2.0,
                             self.get_x() + self.get_dx()/2.0,
                             self.get_y() + self.get_dy()/2.0)
            return self._apply_transform(box, origin=(self.get_x(), self.get_y()))
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
                                
class Frame(ShapelyEagleFilePart):
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

class Hole(ShapelyEagleFilePart):
    # Fixme : Generate tStop and bStop
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def get_geometry(self, layer_query=None, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):
        if self._layer_matches(layer_query, "Holes"):
            circle = shapes.Point(self.get_x(), self.get_y()).buffer(self.get_drill()/2)
            return circle;
        else:
            return shapes.LineString()
        
class Pad(ShapelyEagleFilePart):
    # Fixme: handle other shapes.
    # Fixme : Generate tStop and bStop
    # Fixme: Pads should be different sizes or different layers.
    # Fixme: Pads should maybe generate keepout geometry as well?
        
    def __init__(self):
        ShapelyEagleFilePart.__init__(self);

    def render_pad(self, layer_query, drill, rest_ring):

        if layer_query is not None and self.get_file().get_layer(layer_query).get_number() > 16:
            return shapes.LineString()

        radius = (drill/2) + rest_ring * drill
    
        if self.get_shape() == "square":
            shape = shapes.box(self.get_x() - radius,
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
            shape = None
        elif self.get_shape() == "offset":
            shape = None
        else:
            raise Swoop.SwoopError("Unknown pad shape: '{}'".format(self.get_shape()))

        if strict and shape is None:
            raise NotImplemented("Geometry for pad shape '{}' is not implemented yet.".format(self.get_shape()))
        elif shape is None:
            shape = shapes.LineString()

        return shape

    def get_geometry(self, layer_query=None, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):

        shape = self.render_pad(layer_query, self.get_drill(), 0.25)
        # By default, the radius of the circle of copper
        # is drill radius + 25% of the drill diameter.
        # The percentage is a parameter set in the DRC
        # settings of Eagle.  Swoop doesn't
        # know about the DRC settings, so we
        # just us the default.
        return self._apply_transform(shape, origin=(self.get_x(), self.get_y()))
                               
class Via(Pad):
    def __init__(self):
        Pad.__init__(self);

    def get_geometry(self, layer_query=None, polygonize_wires=ShapelyEagleFilePart.POLYGONIZE_NONE):
        # This isn't quite right.  Via size is set in the DRC file.
        return self.render_pad(layer_query, self.get_drill(), 0.25)

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

        self.subfig.xaxis.set_ticks(range(int(math.floor(float(bounds[0]))), int(math.ceil(float(bounds[2])))))
        self.subfig.yaxis.set_ticks(range(int(math.floor(float(bounds[1]))), int(math.ceil(float(bounds[3])))))
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

def polygon_as_svg(shapely_polygon, svgclass=None, style=None):
    if svgclass is None:
        svgclass = ""
    else:
        svgclass = "class='{}'".format(svgclass)
        
    if style is None:
        style = ""
    else:
        style = "style='{}'".format(style)

    if isinstance(shapely_polygon, shapely.geometry.polygon.Polygon):
        l = [shapely_polygon]
    else:
        l = shapely_polygon.geoms

    r = ""
    # Fixme:  Really, this should be a <path> and we should render the interior points to create holes.
    for i in l:
        points = " ".join(["{},{}".format(round(p[0],5),round(p[1],5)) for p in i.exterior.coords])
        r = r + ("<polygon {} {} points='{}'/>".format(svgclass, style, points))
    return r

def hash_geometry(geo):
    """
    Hash a shapley geometry object by converting it to string, rounding all the floats it contains and taking a hash of the resulting string.  
    
    The rounding prevents false failures due to floating point errors.
    """
    def trim(match):
        return str(round(float(match.group(0)), 5))
    v = re.sub("-?\d+(\.\d+)?", trim, str(geo))
    return hash(v)



import sys
ShapelySwoop = Swoop.Mixin(sys.modules[__name__], "Shapely")
