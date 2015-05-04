Quickly Querying Swoop Objects
==============================

.. currentmodule:: Swoop

Swoop provides `method chaining <http://en.wikipedia.org/wiki/Method_chaining>`_-based interface for querying and iterating over
:class:`EagleFilePart` objects.  If you are familiar with JQuery or LINQ query
language, then you have some experience with method-chaining interfaces.

Chained Mutators
----------------
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
   p = EagleFile.new_Package().                    # Create a package
       set_name("MY_PACKAGE").                     # Set its name 
       add_wire(EagleFile.new_Wire().              # Create a Wire to add
		set_layer("Top").                  # set its layer
		set_x1(4).                         # and it's start and end points
		set_y1(3).
		set_x2(2).
		set_y2(1)).
       add_wire(Wire().                            # Create another Wire to add
		set_layer("tDocu").
		set_x1(1.1).
		set_y1(2.3).
		set_x2(2.4).
		set_y2(9))

Working with Groups of EagelFilePart Objects
-----------------------------------------------------

Searching for and iterating over :class:`EagelFilePart` objects that meet some
criteria are common operations in Swoop.  The :class:`From` uses method
chaining to make this easier and more succint.

A :class:`From` object contains a list of objects (usually, but
not necessarily, :class:`EagelFilePart` objects).  Calling a method on a
:class:`From` object invokes the method on all the objects the :class:`From`
object contains and returns a new :class:`From` object containing the results.

If the method returns lists, the lists are concatenated.  If it return dicts,
the values of the dicts are concatenated.  Singleton values are appended into list.
If the method returns :code:`None`, the value is ignored.

:class:`From` defines several helper methods as well.  For instance,
:meth:`From.map` applies a function to item and returns a :class:`From` object
containing the results and :meth:`From.sorted` returns a sorted :class:`From`.

All this allows for some very short implementations of complex iteration and
searching.  For instance, to print a list of all the packages in all the
libraries of a file you could do:

.. code-block:: python

   from Swoop import *
   print "\n".join(From(EagleFile.from_file("foo.sch")).  # open the file, and create a From object for it
                   get_libraries().                       # Get all the libraries
		   get_packages().                        # Get all the packages from all the libraries
		   get_name().                            # Get the names of those packages
		   sorted())                              # Sort the result.

			     
In addition, :class:`EagleFilePart` and its subclasses provide several methods
built work with :class:`From` objects.  For example,
:meth:`EagleFilePart.with_type` returns :code:`self` if :code:`self` is a
subclass of a give type.  And the :code:`with_*` methods allow for filtering
based on attribute values.)

The resulting library is quite powerful.  For instance, to compute the total
length of all the airwires in board:

.. code-block:: python
   
   from Swoop import *
   from math import * 
   print "Total Airwire Length: "
   print str(From(EagleFile.from_file("foo.brd")).
             get_signals().
             get_wires().
             with_layer("Unrouted").
             map(lambda w: sqrt(((w.get_x1()-w.get_x2())**2 + (w.get_y1()-w.get_y2())**2))).
             reduce(lambda x,y:x + y))


The From Class
--------------

.. autoclass:: From
   :members:
