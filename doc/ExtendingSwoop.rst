Extending Swoop
===============

.. currentmodule:: Swoop

Swoop is extensible via two mechanisms.  Both of them modify the set of classes
that Swoop creates as it parses a file and creates new :class:`EagleFilePart`
objects.


Mixins
------

The second mechanism is mixins.  A mixin is as class that provides some
additional functionality for each :class:`EagleFilePart` that Swoop creates.
When you extend Swoop using a mixin, you create a new subclass of each
:class:`EagleFilePart` class that Swoop uses (e.g., :class:`Library`,
:class:`Attribute`, and :class:`Symbol`).  The new subclass inherits both from
original class and the mixin in class.

The :meth:`Swoop.Mixin` function generates all theses classes automatically.

For instance, to a set of arbitrary attributes to each object, you could do this:

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

This create a bunch of new classes including :class:`AttrPackage`,
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

The Class Map
-------------

You can take finer-grain control over which classes Swoop uses by modifying the
:code:`class_map` member of :class:`EagleFile` (or a derived class returned by
:function:`Swoop.Mixin`).

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

Functions
---------

.. autofunction:: Swoop.Mixin
   
