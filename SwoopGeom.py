

import Swoop
from Rectangle import Rectangle
from CGAL.CGAL_Kernel import \
    Segment_2,\
    Polygon_2,\
    Point_2,\
    Bbox_2,\
    Iso_rectangle_2,\
    do_intersect
import numpy as np
import Dingo.Component
import math

def np2cgal(numpy_point):
    return Point_2(numpy_point[0], numpy_point[1])

def isinstance_any(object, list):
    for c in list:
        if isinstance(object, c):
            return True
    return False


class GeometryMixin(object):
    def get_point(self, i=None):
        """
        Get a coordinate as a numpy array
        Ex: wire.get_point(1) would be (wire.get_x1(), wire.get_y1())
        """
        if i is not None:
            i = str(i)
            return np.array([getattr(self, "get_x" + i)(), getattr(self, "get_y" + i)()])
        else:
            return np.array([getattr(self, "get_x")(), getattr(self, "get_y")()])

    def set_point(self, i, pt):
        i = str(i)
        getattr(self,"set_x" + i)(pt[0])
        getattr(self,"set_y" + i)(pt[1])


    def get_bounding_box(self):
        """
        Get the minimum bounding box enclosing this list of primitive elements
        """
        if isinstance(self, Swoop.Polygon):
            vertices = [v.get_point() for v in self.get_vertices()]
            return Rectangle.from_vertices(vertices)
        elif isinstance(self, Swoop.Wire):
            return Rectangle.from_vertices([self.get_point(1), self.get_point(2)])
        elif isinstance(self, Swoop.Via) or isinstance(self, Swoop.Pad):
            #TODO: pads with funny shapes
            center = self.get_point()
            if self.get_diameter() is None:
                # Gotta figure it out from drill
                radius = (0.351 + 1.251*self.get_drill())/2.0 * np.ones(2)
                return Rectangle(center - radius, center + radius)
            else:
                radius = self.get_diameter()/2.0 * np.ones(2)
                return Rectangle(center - radius, center + radius)
        elif isinstance(self, Swoop.Smd):
            center = self.get_point()
            radius = np.array([self.get_dx(), self.get_dy()]) / 2.0
            if self.get_rot() is not None:
                angle = Dingo.Component.angle_match(self.get_rot())
                radius = abs(Rectangle.rotation_matrix(math.radians(angle['angle'])).dot(radius))
            return Rectangle(center - radius, center + radius)
        else:
            return None


class GeoElem(object):
    """
    A CGAL shape and a Swoop object
    """
    def __init__(self, cgal_elem, swoop_elem):
        self.cgal_elem = cgal_elem
        self.swoop_elem = swoop_elem
        bbox = cgal_elem.bbox()

        #do_intersect only works with iso_rectangle, not bbox
        self.iso_rect = Iso_rectangle_2(bbox.xmin(), bbox.ymin(), bbox.xmax(), bbox.ymax())
        self.rect = Rectangle.from_cgal_bbox(bbox)

    def overlaps(self, iso_rect_query):
        """
        Does this element overlap the bounding box?

        :param bbox_query: CGAL bounding box to check against
        :return: Bool
        """
        if isinstance(self.cgal_elem, Polygon_2):
            #Check bounding box intersection first, it's faster
            if do_intersect(self.iso_rect, iso_rect_query):
                for edge in self.cgal_elem.edges():   #do_intersect does not work with Polygon_2 for some reason
                    if do_intersect(edge, iso_rect_query):
                        return True
        else:
            return do_intersect(self.cgal_elem, iso_rect_query)

WithMixin = Swoop.Mixin(GeometryMixin, "geo")

class BoardFile(Swoop.From):
    """
    A wrapper around Swoop.BoardFile that adds some geometric methods
    """
    def __init__(self, filename):
        """
        Completely overrides the parent constructor

        Need a few things to init from:
        -All <elements> (parts on the board)
        -Random other stuff from <signals> or <plain>

        :param filename: .brd file to create self from
        :return:
        """
        # From needs this in order to work

        super(BoardFile, self).__init__(WithMixin.from_file(filename))

        # Tuples of (geometry element, swoop element)
        # Everything that you can see on the board
        self._elements = []

        #Add all the stuff in <signals>
        for wire in self.get_signals().get_wires():
            p1 = np.array([wire.get_x1(), wire.get_y1()])
            p2 = np.array([wire.get_x2(), wire.get_y2()])
            if p1[0] > p2[0]:
                p1,p2 = p2,p1   # p1 is the left endpoint
            elif p1[0]==p2[0] and p1[1] > p2[1]:
                p1,p2 = p2,p1   # or the bottom

            width = wire.get_width()
            if width==0:    #No width, just a line segment
                seg = Segment_2(Point_2(p1[0], p1[1]), Point_2(p2[0], p2[1]))
                self._elements.append(GeoElem(seg, wire))
            else:           #Has width
                vec = (p2 - p1)
                vec /= np.linalg.norm(vec)          # Normalize
                radius = np.array(vec[1], -vec[0])
                radius *= width/2.0     # "Radius" of the wire, perpendicular to it

                vertices = []
                # Go around the vertices of the wire in CCW order
                # This should give you a rotated rectangle
                vertices.append(np2cgal( p1 + radius ))
                vertices.append(np2cgal( p2 + radius ))
                vertices.append(np2cgal( p2 - radius ))
                vertices.append(np2cgal( p1 - radius ))
                self._elements.append(GeoElem(Polygon_2(vertices), wire))

    def draw_rect(self, rectangle, layer):
        swoop_rect = WithMixin.class_map["rectangle"]()
        swoop_rect.set_point(1, rectangle.bounds[0])
        swoop_rect.set_point(2, rectangle.bounds[1])
        swoop_rect.set_layer(layer)
        self.add_plain_element(swoop_rect)

    def get_overlapping(self, rectangle):
        query = Iso_rectangle_2(*rectangle.bounds_tuple)
        return Swoop.From([x.swoop_elem for x in self._elements if x.overlaps(query)])








