Swoop Utilities
===============

Swoop provides a collection of utility classes and functions for working with
Eagle files built on Swoop that we have built for our own use.  They also serve
as longer examples of how to use Swoop to do useful things to Eagle files.

LibraryCache
------------
.. autoclass:: Swoop.LibraryCache
   
ScanLayerVisitor
----------------
.. autoclass:: Swoop.tools.ScanLayersVisitor
   :no-inherited-members:
   
ScanLibraryReferences
----------------------
.. autoclass:: Swoop.tools.ScanLibraryReferences
   :no-inherited-members:

mergeLayers
-----------
.. autofunction:: Swoop.tools.mergeLayers
	      
normalizeLayers
----------------
.. autofunction:: Swoop.tools.normalizeLayers
	      
rebuildBoardConnections
-----------------------
.. autofunction:: Swoop.tools.rebuildBoardConnections

propagatePartToBoard
--------------------
.. autofunction:: Swoop.tools.propagatePartToBoard

removeDeadEFPs
--------------
.. autofunction:: Swoop.tools.CleanupEagle.removeDeadEFPs

