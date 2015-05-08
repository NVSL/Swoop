EagleFilePart and Its Subclasses
=========================================
.. currentmodule:: Swoop

:class:`EagleFilePart` is the core of Swoop.

Eagle files are stored as XML and are, therefore, tree-structured.  The
Swoop data structures are trees of :class:`EagleFilePart` objects that closely resemble the Eagle
file's structure.  However, the tree structure of the
file formats has been flattened to make them easier to use.  For instance, in
the Eagle file layer definitions live in :code:`eagle/drawing/layers` and
sheets live in :code:`eagle/drawing/schematic/sheets`.  Swoop flattens
this hierarchy so that a :class:`SchematicFile` object has a map of layers and
a list of sheets.


The :class:`EagleFilePart` base class provides some simple functions for
traversing and modifying the :class:`EagleFilePart` tree (i.e., getting the
parent and children and attaching and removing :class:`EagleFilePart` objects).

There are subclasses of :class:`EagleFilePart` that represent all the component
of an Eagle file, and each :class:`EagleFilePart` subclass corresponds to a XML
tag in the Eagle file.  There is
one subclass of :class:`EagleFilePart` for each different XML elements
that can exist in an Eagle file.  Each subclass contains members that
correspond to attributes of that element and the sub-elements the element contains
(subject to the flattening describe above).

There are four broad categories of :class:`EagleFilePart` subclasses:

 1. **The base class** :class:`EagleFilePart` is the baseclass for all other classes in the Swoop.

 2. **File classes** :class:`SchematicFile` , :class:`BoardFile` , and :class:`LibraryFile` represent the three file types.  They share a common baseclass: :class:`EagleFile`.

 3. **Container classes** These include :class:`Library`, :class:`Deviceset`, :class:`Sheet` , and many others classes that define high-level entities in an Eagle file.

 4. **Leaf classes** These inlude :class:`Wire`, :class:`Smd`, :class:`Note` and many others that represent the basic building blocks of the Eagle files.

The container subclasses contain multiple collections of sub-elements.  These
collections are stored either lists or maps.  The order of the sub-elements in
lists corresponds to their order in the Eagle file.  For maps, the key
is usually the sub-element's :code:`name` attribute.  Subclasses may also
contain singleton sub-elements and attributes (which correspond to attributes in
the Eagle file format).

The :class:`Symbol` class illustrates all of these possibilities.  It includes
a singleton :class:`Description` sub-element, a list of :class:`DrawingElement`
sub-elements, and a map matching pin names to 
:class:`Pin` sub-elements.  It also includes a single attribute called
:code:`name`.

Subclasses provide a variety of methods to access, modify, and query
sub-elements and attributes.  These methods follow a consistent naming
convention.  Attributes and can be accessed or modified the methods end with :code:`_<attr>`
where :code:`<attr>` is the attribute name.  Singletons accessors are similar.
For lists and maps, the methods end with :code:`_<subelement>s` or
:code:`_<subelement>` or where :code:`<subelement>` is the name of the list or
map in question.  For instance, :meth:`Symbol.get_drawing_elements()` returns
the drawing elements of the :class:`Symbol` object, and
:meth:`Symbol.get_pin()` finds the :class:`Pin` object given its name.

Each of the standard accessors and mutators is described below after the documentation for :class:`EagleFilePart` itself.  For details on specific subclasses, see the documentation for
those classes.

EagleFilePart
-------------
.. autoclass:: EagleFilePart
	       

Accessor Methods
----------------

.. py:method:: <subclass>.get_<sub-element/attr>()

   For attributes and singletons.

   :returns: The singleton object or attribute value.
   :rtype: :class:`EagleFilePart`
   
.. py:method:: <subclass>.find_<attr>()

   For some attributes.
   
   Find the object refered to by this attribute.  This is similar ot
   :meth:`get_<attr>`, except it returns the object instead of its name.

   For example, consider these ways to query the libary that at :class:`Element` refers to:

   .. code-block:: python
		   
	 # e = some element
	 libname = e.get_library()    # Gets the name of the library
	 lib = e.find_library()       # Gets the library object.
   
   :returns: The object
   :rtype: :class:`EagleFilePart`

.. py:method:: <subclass>.get_<sub-element>(key)

   For maps.
   
   Lookup and return the sub-element corresponding to :code:`key` from this object.
     
   :param key: A :code:`str` to use for the lookup.  
   :returns: The :class:`EagleFilePart` object corresponding to :code:`key` or :code:`None`, if there is no such item.
   :rtype: :class:`EagleFilePart`
	      
.. py:method:: <subclass>.get_<sub-elements>(attrs=None, type=None)

   For maps and lists.
   
   Return (and possibly filter) items in the the :code:`<sub-elements>` for
   this object.  The order of elements in maps in arbitrary.
     
   This functions provides a mechanism for filtering the items as well.  The
   keys in :code:`attrs` are taken as attributes names and the values are
   requested values.  If the attributes and values match for an sub-element, it
   will be included in the returned list.

   A if :code:`type` is not :code:`None`, the item will match if it is an
   instance of the type provided.

   For instance:

   .. code-block:: python

      # s = a symbol
      s.get_drawing_elements(type=Swoop.Wire, attrs={"width" : 0.1})

   Will return the wires in :code:`s` with a width of 0.1 mm.
   
   :param attrs: A set of key-value pairs that represent a filter to apply to the item's attributes.
   :param type:  A type to filter on.  Only items that are an instance of this type will be returned.
   :returns: The list of objects that match the query, if provided
   :rtype: List of objects

.. py:method:: <subclass>.EagleFilePart.get_children(efp)

   :returns: A list of all children of this object.
   :rtype: List of :class:`EagleFilePart` objects

Mutator Methods 
----------------
.. py:method:: <subclass>.set_<attr/singleton>(value)

   For attributes and singletons.
   
   Set the value of the :code:`attr` attribute of this object.
   
   For example, to set the size of a hole to 1mm:
   
   .. code-block:: python
		   
      hole.set_drill(1.0)
		   
   :param value: New value
   :returns: The object.
   :rtype: :class:`EagleFilePart`

.. py:method:: <subclass>.clear_<sub-element>()

   For maps and lists.
   
   Remove all the children in the map or list.
      
   :returns : :code:`self`
   :rtype :class:`EagleFilePart`

.. py:method:: <subclass>.remove_<sub-element>()

   For maps and lists.
   
   Remove a :class:`EagleFilePart` from this object.
        
   :param efp: The object to remove.
   :returns: :code:`self`
   :rtype: :class:`EagleFilePart`

.. py:method:: <subclass>.EagleFilePart.remove_child(efp)

   For maps and lists
		      
   Remove :code:`efp` as a child of this object, regardless of type.
   
   :returns: :code:`self`
   :rtype: :class:`EagleFilePart`

.. py:method:: <subclass>.add_<subelement>(new_child)

   For maps and lists.
   
   Add a :code:'<subelement>' to this object.
      
   :param s: The :class:`EagleFilePart` object to add.
   :returns: :code:`self`
   :rtype: :class:`EagleFilePart`

.. py:method:: <subclass>.get_nth_<subelement>(index)

   For maps and lists.

   Return the :code:`index` :code:`<subelement>` of this object.  For maps,
   the ordering of the items in the list is arbitrary, but will be consistent
   across calls if the contents of the map has not changed.
	       
   :param index: The index of the subelement to access.
   :returns: The :class:`EagleFilePart` object
   :rtype: :class:`EagleFilePart`
      

Query Methods
---------------

.. py:method:: <subclass>.with_<attr>(value)

   For attributes.
   
   Filter this :code:`EagleFilePart` object based on the value of the attribute.  For use in combination with :class:`From` objects.
               
   Return :code:`self` if one of the following is true:
      
   1.  :code:`<attr>` equals :code:`v`
   2.  :code:`v`is callable and :code:`v(self.get_<attr>())` is :code:`True`

   For example, get :class:`Element` objects from a board that come from the library named "KoalaBuild" or whose name starts with "Koala":
       
   .. code-block:: python

      From(brd).get_elements().with_library("KoalaBuild")
      From(brd).get_elements().with_library(lambda x: re.match(x,"Koala.*") is not None)
	 
   :param t: The value to check for or a callable object.
   :returns: :code:`self` if the criteria above are met and :code:`None` otherwise. 
   :rtype: :class:`EagelFilePart` or :code:`None`


	   
