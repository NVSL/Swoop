Extending Swoop
===============

.. currentmodule:: Swoop

Swoop is extensible via three mechanisms.  Both of them modify the set of classes
that Swoop creates as it parses a file and creates new :class:`EagleFilePart`
objects.

Targeted Mixins
----------------

The first mechanism is targeted mixins. A mixin is as class that provides some
additional functionality to another class by creating a new class that inherits
from both the mixin class and the original class.  Swoop's targetd mixin
mechanism allows you to selectively add mixins to the :class:`EagleFilePart`
classes that Swoop uses to represent Eagle files.


To use targeted mixins, you provide a python module that contains a mixin class
for each Swoop class you'd like to modify.  The mixin class should have the
same name as the Swoop class it is meant to modify.  For instance, in this
example, we use :meth:`Swoop.Mixin` to add an :code:`get_area()` method to
:class:`Rectangle` and :class:`Circle`.

Here's the module (in Area.py):

.. code-block:: python

    class Rectangle:
	def __init__(self):
            pass
	def get_area(self):
            return abs((self.get_x2()-self.get_x1()) * (self.get_y1()-self.get_y2()))

    class Circle:
	def __init__(self):
            pass
	def get_area(self):
            return math.pi * (self.get_radius()**2)

and how to use it to print out the sum of the areas of all the rectangle and circles in all the packages in a libray:

.. code-block:: python

    import Area
    
    AreaEagleFile = Swoop.Mixin(Area, "Area")
    
    lbr = AreaEagleFile.open("test.lbr")
    print (From(test.lbr).
           get_library().
           get_packages().
           get_drawing_elements().
           with_type(Rectangle).
           get_area().
           reduce(lambda x,y:x+y, init=0.0))

    print (From(test.lbr).
           get_library().
           get_packages().
           get_drawing_elements().
           with_type(Circle).
           get_area().
           reduce(lambda x,y:x+y, init=0.0))


.. autofunction:: Swoop.Mixin

Universal Mixins
----------------

You can also call :meth:`Swoop.Mixin` with a single class and have it mixed
into all of the :class:`EagleFilePart` sub classes.

For instance, to add a set of arbitrary attributes to each object, you could do this:

.. code-block:: python

    class AttrMixin(object):
        def __init__(self):
            self.attrs = {}
        def set_attr(self, n, v):
            self.attrs[n] = v
            return self
        def get_attr(self, n):
            return self.attrs.get(n)

    AttrEagleFile = Swoop.Mixin(AttrMixin, "Attr")
    
    sch = AttrEagleFile.open("test.sch")
    sch.get_library("A_LIBARRY").get_symbol("GOOD_SYMBOL").set_attr("good?", "yes!")

This creates a bunch of new classes including :class:`AttrPackage`,
:class:`AttrLibraryFile`, and :class:`AttrWire`.  The :class:`AttrEagleFile`
object that :meth:`AttrEagleFile.open()` returns is made of solely of these new
:class:`Attr*` objects.

You can compose extensions as well:

.. code-block:: python

    class Walker(object):
        def do_it(self):
            return "walk"

    WalkerAttrEagleFile = Swoop.Mixin(Walker, "Walker",base=AttrEagleFile)
    
    sch2 = WalkerAttrEagleFile.open("test.sch")
    sch2.get_library("A_LIBARRY").get_symbol("GOOD_SYMBOL").do_it()
    sch2.get_library("A_LIBARRY").get_symbol("GOOD_SYMBOL").set_attr("good?", "yes!")

   

The Class Map
-------------

:bold:`Don't do this.  It's deprecated because it's messy`

You can take finer-grain control over which classes Swoop uses by modifying the
:code:`class_map` member of :class:`EagleFile` (or a derived class returned by
:func:`Swoop.Mixin`).

The :code:`class_map` defines the mapping between tag names (as they appear in
Eagle file) and :class:`EagleFilePart` subclasses.

For instance if you wanted to add a :code:`set_location()` method to
:class:`Element` you could write the following:

.. code-block:: python

    from Swoop import *
    class MyElement(Element):
        def __init__(self):
            Element.__init__(self)

        def set_location(x,y):
            self.set_x(x)
            self.set_y(y)

     EagleFile.class_map["element"] = MyElement

If you later extend :class:`EagleFile` using :meth:`Swoop.Mixin`, the mixin will be applied to :class:`MyElement`.

