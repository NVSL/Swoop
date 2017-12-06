# coding=utf-8
import numpy as np
import math
from math import sin,cos
import random

from numpy.linalg import det
import itertools


class LineSegment(object):
    """
    Simple line segment
    Lower-Left endpoint comes first
    """

    def __init__(self, p1, p2):
        assert isinstance(p1, np.ndarray)
        assert isinstance(p2, np.ndarray)
        # Make p1 the lower-left endpoint
        if p1[0] > p2[0]:
            p1,p2 = p2,p1   # Left greater than right, swap
        elif p1[0] == p2[0] and p1[1] > p2[1]:
            p1,p2 = p2,p1   # Aligned on X, swap if p1 above p2
        self.p1 = p1
        self.p2 = p2

    @property
    def x1(self):
        return self.p1[0]

    @property
    def y1(self):
        return self.p1[1]

    @property
    def x2(self):
        return self.p2[0]

    @property
    def y2(self):
        return self.p2[1]

    @property
    def points(self):
        yield self.p1
        yield self.p2

    @property
    def vertices(self):
        yield self.p1
        yield self.p2

    @property
    def length(self):
        return np.linalg.norm(self.p2 - self.p1)

    def bounding_box(self):
        """
        Return a minimal Rectangle bounding self
        CAREFUL: rectilinear line segments will cause an error
        """
        return Rectangle(np.minimum.reduce([self.p1, self.p2]),
                         np.maximum.reduce([self.p1, self.p2]))

    def copy(self):
        return LineSegment(self.p1.copy(), self.p2.copy())

    def rotate(self, angle_degrees):
        rmatrix = Rectangle.rotation_matrix(math.radians(angle_degrees))
        self.p1 = rmatrix.dot(self.p1)
        self.p2 = rmatrix.dot(self.p2)
        if self.p1[0] > self.p2[0]:
            self.p1, self.p2 = self.p2, self.p1
        elif self.p1[0]==self.p2[0] and self.p1[1] > self.p2[1]:
            self.p1, self.p2 = self.p2, self.p1
        return self


    def overlaps(self, other):
        """
        If there is a common point between self and other, return true
        """

        # The implementations should be in [more complicated] overlaps [less complicated]
        if isinstance(other, Rectangle):
            return other.overlaps(self)

        if isinstance(other, RotatedRectangle):
            return other.overlaps(self)

        if not isinstance(other, LineSegment):
            raise TypeError("Cannot test overlap between {0} and {1}".format(self.__class__,other.__class__))

        for s in (self,other):
            assert s.x1 <= s.x2
            if s.x1 == s.x2:
                assert s.y1 <= s.y2

        for p1,p2 in itertools.product(self.points,other.points):
            if np.allclose(p1,p2):
                return True     # Common endpoint
        #Stolen from: http://stackoverflow.com/questions/563198/how-do-you-detect-where-two-line-segments-intersect
        p = self.p1
        q = other.p1
        r = self.p2 - self.p1
        s = other.p2 - other.p1
        qpxr = det([q - p, r])
        rxs = det([r, s])
        if rxs == 0 and qpxr == 0:
            # Collinear
            t0 = (q - p).dot(r) / r.dot(r)
            t1 = (q + s - p).dot(r) / r.dot(r)
            if 0 <= t0 <= 1 or 0 <= t1 <= 1:
                return True
            else:
                return False
        if rxs==0:
            # Parallel, but no chance of collinear
            return False
        u = qpxr / rxs
        t = det([q - p, s])
        t /= rxs
        low = 0.0
        high = 1.0
        return (low <= u <= high and low <= t <= high)


class RotatedRectangle(object):
    """
    A rectangle with a rotation attribute
    """
    def __init__(self, rect, angle_degrees, around_origin=True):
        assert isinstance(rect, Rectangle)
        self._angle = 0
        self._rect = rect
        self.rotate(angle_degrees, around_origin)

    def __eq__(self, other):
        return self.angle == other.angle and self._rect == other._rect

    def __repr__(self):
        return "RotatedRectangle({0}, {1}, {2})".format(self._rect.__repr__(), self._angle, False)

    def overlaps(self, other):
        if isinstance(other, Rectangle):
            for edge in self.edges():
                if other.overlaps(edge):
                    return True
            for edge in other.edges():
                if self.overlaps(edge):
                    return True
            return False
        elif isinstance(other, RotatedRectangle):
            # Make one rectangle rectilinear, then use above method
            rectilinear = self.copy().rotate(-self.angle)
            rotated = other.copy().rotate(-self.angle)
            assert abs(rectilinear.angle) < 0.00001
            return rectilinear.bounding_box().overlaps(rotated)
        elif isinstance(other, LineSegment):
            rectilinear = self.copy().rotate(-self.angle)
            rotated_segment = other.copy().rotate(-self.angle)
            assert abs(rectilinear.angle) < 0.00001
            return rectilinear.bounding_box().overlaps(rotated_segment)
        else:
            raise TypeError("Cannot test overlap between {0} and {1}".format(self.__class__,other.__class__))

    def edges(self):
        c = self._rect.center()
        verts = list([self._rmatrix.dot(v-c)+c for v in self._rect.vertices()])
        for i in range(4):
            yield LineSegment(verts[i], verts[(i+1) % 4])

    def eagle_code(self):
        return "rect R{0} ({1} {2}) ({3} {4})".format(*((self.angle,) + self._rect.bounds_tuple))

    def rotate(self, angle_degrees, around_origin=True):
        self._angle = (self._angle + angle_degrees) % 360.0
        self._rmatrix = Rectangle.rotation_matrix(math.radians(self._angle))

        # Change the origin of the underlying rectilinear rectangle
        if around_origin:
            c = self._rect.center()
            c = Rectangle.rotation_matrix(math.radians(angle_degrees)).dot(c)
            self._rect.move_to(c)
        # Otherwise, we rotate around the rectangle center
        return self

    def center(self):
        return self._rect.center()

    def move(self, vector):
        self._rect.move(vector)
        return self

    def bounding_box(self):
        return self._rect.rotate_resize(self.angle, around_origin=False)

    def copy(self):
        return RotatedRectangle(self._rect.copy(), self.angle, around_origin=False)

    @property
    def angle(self):
        return self._angle



class Rectangle(object):
    """
    The glorious Rectangle, the standard container for parts
    Its main claim to fame is randomized splitting for rectilinear partitioning
    """
    @staticmethod
    def rotation_matrix(radians):
        assert not math.isnan(radians)
        return np.array([[cos(radians),-sin(radians)],
                        [sin(radians),cos(radians)]])

    @staticmethod
    def from_cgal_bbox(bbox, check=True):
        return Rectangle((bbox.xmin(), bbox.ymin()), (bbox.xmax(), bbox.ymax()), check=check)

    @staticmethod
    def random(begin=(-50,-50), end=(50,50)):
        return Rectangle(   (random.uniform(begin[0], end[0]), random.uniform(begin[1],end[1])),
                            (random.uniform(begin[0], end[0]), random.uniform(begin[1],end[1])) )

    @staticmethod
    def union(r1, r2):
        """
        Smallest rectangle enclosing r1 and r2
        :param r1:
        :param r2:
        :return: Union of r1, r2
        """
        low = np.minimum.reduce([r1.bounds[0], r2.bounds[0]])
        high = np.maximum.reduce([r1.bounds[1], r2.bounds[1]])
        return Rectangle(low, high, check=False)

    @staticmethod
    def from_vertices(vertices, check=False):
        """
        Smallest rectangle enclosing a bunch of points

        :param vertices: List of numpy coordinates
        :param check: Check for invalid dimensions
        :return: Minimum bounding rectangle
        """
        low = np.minimum.reduce(vertices)
        high = np.maximum.reduce(vertices)
        return Rectangle(low, high, check=check)

    @staticmethod
    def null():
        """
        Create a rectangle guaranteed to enclose nothing

        :return:
        """
        r = Rectangle((0,0),(1,1))
        r.bounds[0] = np.ones(2) * float('inf')
        r.bounds[1] = np.ones(2) * -float('inf')
        return r

    EPSILON = 0.000001    #Floating point fun

    #Init from 2 coordinates v1=[x1,y1],v2=[x2,y2] not colinear along any axis OR
    # 1 coordinate (v1) and the size
    def __init__(self,v1,v2=None,size=None,occupied=None,check=True):
        assert v2 is not None or size is not None,"Only one vertex given"
        v1 = np.array([v1[0],v1[1]]).astype(float) # Could be a tuple
        if v2 is not None:
            assert size is None,"Specify the other vertex or the size, not both"
            vert_list = [v1,np.array([v2[0],v2[1]])]
        else:
            vert_list = [v1,v1 + np.array([size[0],size[1]])]
        self.bounds = [np.minimum.reduce(vert_list),np.maximum.reduce(vert_list)]
        if check:
            self.check()
        self.occupied = occupied

    def __str__(self):
        s = ""
        for v in self.bounds:
                # s += "(%.2f %.2f) " % (v[0],v[1])
                s += "(%.5f, %.5f), " % (v[0],v[1])
        return s[:-2]

    def __repr__(self):
        return "Rectangle( " + str(self) + ")"

    def __eq__(self,other):
        return all( map(np.allclose,self.bounds,other.bounds) )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.bounds_tuple)

    # Move the rectangle by the specified vector
    def move(self,vector):
        for b in self.bounds:
            b += vector
        return self

    # Change the center of the rectangle the specified point
    def move_to(self, point):
        vec = point - self.center()
        return self.move(vec)

    # Left X coordinate of rectangle
    def left(self):
        return self.bounds[0][0]

    #Return the center coordinates resulting from randomly placing rect into self
    #Range limits how far rect can move from its current position
    def random_rec_place(self, rect, range = 1.0, rotate = False):
        if rotate:
            rect_size = rect.size()[::-1]
        else:
            rect_size = rect.size()
        start = rect_size/2.0
        end = self.size() - rect_size/2.0
        new_center = np.array([random.uniform(start[0],end[0]), random.uniform(start[1],end[1])])
        new_center += self.bounds[0]
        return (new_center - rect.center())*range + rect.center()

    def right(self):
        return self.bounds[1][0]

    def rotate(self, angle_degrees, around_origin=True):
        return RotatedRectangle(self, angle_degrees, around_origin)

    def rotate_resize(self,angle_degrees,around_origin=True,origin=None):
        """
        The bounding box resulting from rotating self
        Result will always have non-decreasing area
        The default is rotating it around (0,0)
        :param angle_degrees:
        :param around_origin:
        :return:
        """
        angle = math.radians(angle_degrees)
        rmatrix = Rectangle.rotation_matrix(angle)
        if origin is not None:
            c = origin
        elif around_origin:
            c = np.array([0.0,0.0])
        else:
            c = self.center()
        new = list([rmatrix.dot(v-c)+c for v in self.vertices()])
        self.bounds[0] = np.minimum.reduce(new)
        self.bounds[1] = np.maximum.reduce(new)
        return self

    #Bottom Y coordinate
    def bot(self):
        return self.bounds[0][1]

    @property
    def bounds_tuple(self):
        return (self.bounds[0][0], self.bounds[0][1], self.bounds[1][0], self.bounds[1][1])

    def top(self):
        return self.bounds[1][1]

    def center(self):
        return (self.bounds[0] + self.bounds[1]) / 2.0

    def copy(self):
        return Rectangle(self.bounds[0].copy(),self.bounds[1].copy(), occupied = self.occupied)

    @property
    def height(self):
        return self.size(1)

    #Minimum coordinate along axis
    #low(0) is left side, low(1) is bottom
    def low(self,axis):
        return self.bounds[0][axis]

    #Max coordinate on axis
    #high(1) is top, high(0) is right
    def high(self,axis):
        return self.bounds[1][axis]

    #The rectangle resulting from intersecting self with other (if any)
    #TODO: 0 enclosed vertices case, sharing 2 sides case (CGAL would be nice...)
    def intersect(self,other):
        if not self.overlaps(other):
            return None
        if self.encloses(other):
            return other
        if other.encloses(self):
            return self
        outside,inside = self,other
        in_verts = list(outside.enclosed_vertices(inside))
        out_verts = list(inside.enclosed_vertices(outside))
        assert (len(in_verts) + len(out_verts))==2
        if len(in_verts)==1:
            return Rectangle(in_verts[0],out_verts[0])
        else:
            if len(in_verts)==0:
                outside,inside = inside,outside
                in_verts,out_verts=out_verts,in_verts
            axis = np.argmin(abs(in_verts[0] - in_verts[1]))
            v2 = outside.chord_toward(inside.center(), in_verts[1], axis)
            return Rectangle(in_verts[0], v2)


    #Join two rectangles sharing a common side
    def join(self,other):
        assert (self.bounds[0] == other.bounds[0]).any(),"Must be aligned on a side to join"
        assert (abs(self.size() - other.size()) < Rectangle.EPSILON).any(),"Must have common dimension to join"
        joined = Rectangle(np.minimum(self.bounds[0],other.bounds[0]),
                           np.maximum(self.bounds[1],other.bounds[1]))
        return joined


    #Max side length
    def max_side(self):
        return max(self.bounds[1] - self.bounds[0])

    #Flip the rectangle around the specified axis
    def mirror(self, axis):
        change = 1 - axis
        self.bounds[0][change] *= -1    #Negate
        self.bounds[1][change] *= -1
        #..and swap
        self.bounds[0][change],self.bounds[1][change] = self.bounds[1][change],self.bounds[0][change]

    #Test if two rectangles share a side
    #Sharing just a point doesn't count
    def shares_side(self, other):
        #Get the maximum distance between sides on both axes
        max_lens = abs(self.bounds[1] - other.bounds[0])
        max_lens = np.maximum(max_lens, abs(self.bounds[0] - other.bounds[1]))

        #Compare that to just summing the side lengths
        #For a valid touch: one axis is equal to the back-to-back length
        #The other max length is less
        diff = max_lens - (self.size() + other.size())
        if (diff > Rectangle.EPSILON).any():        #Apart from each other on an axis, not touching
            return False

        return (abs(diff) < Rectangle.EPSILON).sum()==1   #Only 1 axis can be equal; 2 and they share just a point


    def size(self,axis=None):
        if axis is not None:
            return self.bounds[1][axis] - self.bounds[0][axis]
        else:
            return self.bounds[1] - self.bounds[0]

    def area(self):
        return np.multiply.reduce(self.size())

    #Area that two overlapping rectangles have in common
    def overlap_area(self, other):
        def split_area(a,b):
            area = 0.0
            for r in a.split(b):
                area += r.area()
            return area

        if not self.overlaps(other):
            return 0.0

        area = self.area() + other.area()
        area -= split_area(self, other)
        area -= split_area(other, self)
        return area / 2.0   # Intersecting area counted twice

    #Check if this rectangle overlaps other
    #Sharing sides does not count, it must overlap inside the epsilon
    def overlaps(self, other):
        if isinstance(other, LineSegment):
            if self.enclose_vertex(other.p1) or self.enclose_vertex(other.p2):
                return True
            for edge in self.edges():
                if edge.overlaps(other):
                    return True
            return False
        elif isinstance(other, Rectangle):
            for axis in range(2):
                if not (self.low(axis) < other.high(axis) - Rectangle.EPSILON and
                                self.high(axis) > other.low(axis) + Rectangle.EPSILON):
                    return False
            return True
        elif isinstance(other, RotatedRectangle):
            return other.overlaps(self)
        else:
            raise TypeError("Cannot test overlap between {0} and {1}".format(self.__class__, other.__class__))

    #Add a constant padding to everything around the rectangle
    def pad(self,padding):
        vec = np.array([padding, padding])
        self.bounds[0] -= vec
        self.bounds[1] += vec
        return self

    #Traverse vertices clockwise starting from top left
    #If vertices are xy XY then it comes out in this order: xY XY Xy xy
    def vertices(self):
        lo = self.bounds[0]
        hi = self.bounds[1]
        yield np.array([lo[0],hi[1]])
        yield np.array([hi[0],hi[1]])
        yield np.array([hi[0],lo[1]])
        yield np.array([lo[0],lo[1]])

    def vertices_ccw(self):
        """
        CGAL polygons want their vertices in CCW order
        :return: Iterator
        """
        return reversed(list(self.vertices()))


    @property
    def width(self):
        return self.size(0)

    #Get the other vertex of a chord starting at start_vertex 
    #Direction: 0=left/down 1=up/right
    #Does not necessarily have to be enclosed
    def chord_vertex(self,start_vertex,axis,direction):
        cv = np.array([0.0,0.0])
        cv[axis] = self.bounds[direction][axis]
        cv[axis ^ 1] = start_vertex[axis ^ 1]
        return cv

    #Sanity checking...
    def check(self):
        assert ((self.bounds[1] - self.bounds[0]) > Rectangle.EPSILON).all(),"Negative or zero rectangle dimensions"

    #Draw chord away from avoid_vertex starting at start_vertex
    def chord_away_from(self,avoid_vertex,start_vertex,axis):
        assert start_vertex[axis] != avoid_vertex[axis]
        direction = 0
        if start_vertex[axis] > avoid_vertex[axis]:
            direction = 1
        return self.chord_vertex(start_vertex,axis,direction)

    #Similar to chord_away_from
    def chord_toward(self,toward_vertex,start_vertex,axis):
        assert start_vertex[axis] != toward_vertex[axis]
        direction = 1 if start_vertex[axis] < toward_vertex[axis] else 0
        return self.chord_vertex(start_vertex,axis,direction)

    def enclosed_vertices(self,other):
        for v in other.vertices():
            if self.enclose_vertex(v):
                yield v

    def num_enclosed_vertices(self,other):
        return sum(1 for _ in self.enclosed_vertices(other))

    def edges(self):
        """
        Yield all edges clockwise starting from top left
        Like a toilet bowl in Australia
        :return:
        """
        verts = list(self.vertices())
        for i in range(4):
            yield LineSegment(verts[i], verts[(i+1)%4])


    def eagle_code(self):
        """
        Format this rectangle so you can paste it into Eagle
        :return: String
        """
        return "rect ({0} {1}) ({2} {3})".format(*self.bounds_tuple)

    #Does this rectangle enclose the vertex?
    #This is strict, must be inside by at least EPSILON
    def enclose_vertex(self,vertex):
        return  (self.left() + Rectangle.EPSILON < vertex[0] < self.right() - Rectangle.EPSILON and
            self.bot() + Rectangle.EPSILON < vertex[1] < self.top() - Rectangle.EPSILON)

    #Strict less-than enclosure, no lining up of vertices
    #By this definition a rectangle does not enclose itself
    def encloses_strict(self,rect):
        return self.num_enclosed_vertices(rect)==4


    #Test enclosure on the dimensions only, not absolute position
    def encloses_size(self, rect, allow_rotate = False):
        if allow_rotate:
            return (self.size() >= rect.size()).all() or self.fit_after_rotate(rect)
        else:
            return (self.size() >= rect.size()).all()

    #By this definition a rectangle encloses itself
    def encloses(self,rect):
        for axis in range(2):
            if not (self.low(axis) - Rectangle.EPSILON <= rect.low(axis) and
                            self.high(axis) + Rectangle.EPSILON >= rect.high(axis)):
                return False
        return True

    #Will rect fit in self after a rotation?
    def fit_after_rotate(self, rect):
        return (self.size() >= rect.size()[::-1]).all()

    #Like enclose, but on only 1 axis
    def axis_encloses(self,coord,axis):
        return coord + Rectangle.EPSILON < self.high(axis) and coord - Rectangle.EPSILON > self.low(axis)

    #Let another rectangle take a chunk out of this one and split the remainder into rectangles
    #Other is splitting self
    #Welcome to rectangle hell
    def split(self,other,split_axis=None):
        assert self.overlaps(other),"You can only split if the rectangles overlap"

        if self==other:
            return  # NOTHING TO DO YAYYYY
        if other.encloses(self):
            return  # other is bigger, it eats the entire self

        #3 cases: 0. no enclosed vertices, 1. 1 enclosed, 2. 2 enclosed
        #Case 0: split either (top or bottom) or (left or right)
        #Case 1: split along 2 sides
        #Case 2: 3 sides
        enclosed = list(self.enclosed_vertices(other))
        assert len(enclosed) != 3
        if len(enclosed)==0:
            splits = [0]    #start with the edge that we have
            #Figure out the split axis
            for axis in range(2):
                if len(splits) > 1: break   #Can only split on one axis
                split_axis = axis
                if self.axis_encloses(other.low(axis),axis):
                    splits.append(other.low(axis))
                    skip_idx = 1
                if self.axis_encloses(other.high(axis),axis):
                    splits.append(other.high(axis))
                    skip_idx = 1 if len(splits)==3 else 0
            assert len(splits) > 1,"Should've split something"
            splits[0] = self.low(split_axis)
            #Axis==0: splitting vertical, 1==splitting horizontal
            splits.append(self.high(split_axis))
            #Size on the other (not splitting) axis
            not_split_size = self.high(1 - split_axis) - self.low(1 - split_axis)
            size = [0,0]
            size[1 - split_axis] = not_split_size   #This stays the same            
            origin = self.bounds[0].copy()
            for i in range(len(splits)-1):
                new_dim = splits[i+1] - splits[i]
                size[split_axis] = new_dim
                if i != skip_idx:      #If we didn't skip this we'd duplicate the rectangle doing the splitting
                    yield Rectangle(origin.copy(),size=size)
                origin[split_axis] += new_dim
        elif len(enclosed)==1:
            #Not so straightforward, we have a choice between 2 chords to draw
            #For now, just choose randomly
            #Exactly 2 new rectangles come out of this
            v_in = enclosed[0]     #inside vertex

            direction_to_corner = [1,1]
            for i in range(2):
                if v_in[i] > other.low(i):
                    direction_to_corner[i] = 0
            v_in_corner = self.chord_vertex(v_in,0,direction_to_corner[0])    #Draw x
            v_in_corner = self.chord_vertex(v_in_corner,1,direction_to_corner[1]) #Draw y to the corner

            if split_axis is None:
                split_axis = random.randint(0,1)            
            #Draw chords going away from the splitter rectangle
            v_side = self.chord_away_from(v_in_corner,v_in,split_axis)
            splitter = Rectangle(v_in_corner,v_side)
            for r in self.split(splitter):
                yield r     #Should split off the other side, preserving either width/height of self
            v_short_corner = self.chord_toward(v_in,v_in_corner,split_axis)
            #Now return the little one (both dimensions cut)
            yield Rectangle(v_short_corner,v_in)
        elif len(enclosed)==2:
            for v in other.vertices():
                if self.enclose_vertex(v): continue
                not_enclosed_v = v
                break
            if split_axis is None:
                split_axis = random.randint(0,1)
                other_split_axis = random.randint(0,1)
            else:
                other_split_axis = 1 - split_axis
            if ((enclosed[0] - enclosed[1]) > 0).any():
                enclosed = list(reversed(enclosed))
            verts_axis = 1 if enclosed[0][0]==enclosed[1][0] else 0
            if split_axis==verts_axis:
                #Draw a chord to the edge, and this reduces to the 1-enclosed vertex split
                v_side = self.chord_vertex(enclosed[0],split_axis,0)
                v_corner = self.chord_toward(not_enclosed_v,v_side,1 - split_axis)
                yield Rectangle(v_corner,enclosed[0])
                splitter = Rectangle(v_corner,enclosed[1])
                for r in self.split(splitter,other_split_axis):
                    yield r
            else:
                #This case is a pain
                #Chord to opposite side
                v = self.chord_away_from(not_enclosed_v,enclosed[0],1 - verts_axis)
                v1 = self.chord_away_from(enclosed[1],v,verts_axis)     #To a corner of self
                v2 = self.chord_toward(not_enclosed_v,enclosed[0],1 - verts_axis)
                yield Rectangle(v1,v2)    #This should preserve a whole dimension
                #Now go the other vertex and chop up what's left
                #Use other_split_axis to be different
                v_side = self.chord_away_from(enclosed[0],enclosed[1],verts_axis)
                v_corner = self.chord_toward(not_enclosed_v,v_side,1 - verts_axis)
                v_corner_other = self.chord_away_from(not_enclosed_v,v_side,1 - verts_axis)
                if other_split_axis==verts_axis:
                    yield Rectangle(v_corner,enclosed[1])
                    yield Rectangle(v_corner_other,enclosed[0])
                else:
                    v_side = self.chord_away_from(not_enclosed_v,enclosed[1],1 - verts_axis)
                    yield Rectangle(v_corner,v_side)
                    yield Rectangle(v_side,enclosed[0])
        elif len(enclosed)==4:
            #other is totally inside self

            all_possible = [None]*8
            center = other.center()
            other_vs = list(other.vertices())
            for i,(o,v) in enumerate(zip(self.vertices(),other.vertices())):
                all_possible[i*2] = Rectangle(o,v)
                c = self.chord_away_from(center, other_vs[(i+1)%4], (i+1)%2)
                all_possible[2*i+1] = Rectangle(v,c)

            for i in range(4):
                if split_axis is None:
                    join_to = (random.choice([-1,1]) + 2*i + 8)%8
                else:
                    join_to = (2*i+1)%8
                new = all_possible[i*2].join(all_possible[join_to])
                all_possible[i*2] = new
                all_possible[join_to] = new
            for i in range(4):
                yield all_possible[2*i+1]


