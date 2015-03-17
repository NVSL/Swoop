Core Classes
===============

These are the core base classes of Swoop.  :class:`EagleFile` is the base class
for the three Eagle file types.  :class:`EagleFilePart` is the base class for
all the types that, together, represent an Eagle file.

You should not create instances of :class:`EagleFilePart` subclasses directly.
Instead, you should use the factory fuctions provided in :class:`EagleFile`.
This ensure that Swoop extensions will work correctly.


.. currentmodule:: Swoop

Classes
-------
.. autoclass:: EagleFile
   :members:

.. autoclass:: EagleFilePart
   :members:
