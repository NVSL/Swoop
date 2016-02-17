Design Rule Parameters
======================

Design rule file specify a variety of parameters that control the design rule
checks that Eagle performs and the geometry of vias, restrings, etc.  Swoop
includes :class:`Swoop.DRUFile` to parse DRU files and expose their contents
via a object interface.

An :class:`EagleFile` object has an associated :class:`DRUFile` object.  If non
is specified during construction, Swoop uses defaults based on the defaults
provided with Swoop.


The DRUFile Class
-----------------

.. autoclass:: Swoop.DRUFile
   :members:
