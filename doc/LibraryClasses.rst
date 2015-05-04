Classes for Library Files (.lbr)
================================

These classes are used only within Eagle library files (.lbr) and in the
libraries that are included in both .sch and .brd files.

If you are new to Swoop and trying to understand how these data structures map
onto items in Eagle, it is useful to know that :class:`DeviceSet` corresponds
to what the Eagle GUI calls a "Device" and :class:`Device` corresponds to what
the GUI calls a "Variant"

.. currentmodule:: Swoop

LibraryFile
----------------
.. autoclass:: Base_LibraryFile

Library
--------------
.. autoclass:: Library

Package
--------------
.. autoclass:: Package

Symbol
--------------
.. autoclass:: Symbol

Deviceset
--------------
.. autoclass:: Deviceset

Device
--------------
.. autoclass:: Device

Connect
--------------
.. autoclass:: Connect

Gate
--------------
.. autoclass:: Gate

Pad
--------------
.. autoclass:: Pad

Smd
--------------
.. autoclass:: Smd
