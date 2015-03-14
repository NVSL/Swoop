Flocks and Chains: Bulk Operations on :class:`EagleFilePart` Objects
====================================================================

.. currentmodule:: Swoop

Swoop provides `method chaining <http://en.wikipedia.org/wiki/Method_chaining>`-based interface for querying and iterating over
:class:`EagleFilePart` objects.  If you are familiar with JQuery or LINQ query
language, then you have some experience with method-chaining interfaces.

Mutators
--------
To support chaining modifications to :class:`EagleFilePart` objects, all the
mutators (or setter function) for :class:`EagleFilePart` subclasses return the object so you can set
the location all the geometry information for a wire with the following:

.. code-block:: python

   from Swoop import *
   w = Wire()
   w.set_x1(4).set_y1(3).set_x2(2).set_y2(1)

Likewise you can add multiple wires to a package:

.. code-block:: python

   from Swoop import *
   p = Package().
       set_name("MY_PACKAGE").
       add_wire(Wire().
		set_layer("Top").
		set_x1(4).
		set_y1(3).
		set_x2(2).
		set_y2(1)).
       add_wire(Wire().
		set_layer("tDocu").
		set_x1(1.1).
		set_y1(2.3).
		set_x2(2.4).
		set_y2(9))

Working with Groups of :class:`EagelFilePart` Objects
-----------------------------------------------------

Searching for and iterating over :class:`EagelFilePart` objects that meet some
criteria are common operations in Swoop.  The :class:`Flock` uses method
chaining to make this easier and more succint.

A :class:`Flock` object contains a list of objects (usually, but
not necessarily, :class:`EagelFilePart` objects).  Calling a method on a
:class:`Flock` object invokes the method on all the objects the :class:`Flock`
object contains and returns a new :class:`Flock` object containing the results.

If the method returns lists, the lists are concatenated.  If it return dicts,
the values of the dicts are concatenated.  Singleton values are appended into list.
If the method returns :code:`None`, the value is ignored.

:class:`Flock` defines several helper methods as well.  For instance,
:meth:`Flock.map` applies a function to item and returns a :class:`Flock` object
containing the results and :meth:`Flock.sorted` returns a sorted :class:`Flock`.

For instance, to print a list of all the packages in all the libraries of a file you could do:

.. code-block:: python

   from Swoop import *
   print "\n".join(Flock(EagleFile.from_file("foo.sch")).
                   get_libraries().
		   get_packages().
		   get_name().
		   sorted())

			     
In addition, :class:`EagleFilePart` and its subclasses provide several methods
built work with :class:`Flock` objects.  For example,
:meth:`EagleFilePart.filter_type` returns :code:`self` if :code:`self` is a
subclass of a give type.  And the :code:`filter_*` methods allow for filtering
based on attribute values.)

The resulting library is quite powerful.  For instance, to compute the total
length of all the airwires in board:

.. code-block:: python
   
   from Swoop import *
   from math import * 
   print "Total Airwire Length: " +  str(Flock(EagleFile.from_file("foo.brd")).
                                         get_signals().
                                         get_wires().
                                         filter_layer("Unrouted").
                                         map(lambda w: sqrt(((w.get_x1()-w.get_x2())**2 + (w.get_y1()-w.get_y2())**2))).
                                         reduce(lambda x,y:x + y)


.. autoclass:: Flock
   :members:
