EagleFile Base Class
====================

Swoop provides one class for each of the three Eagle file types:
:class:`EagleBoard`, :class:`EagleSchematic`, and :class:`EagleLibrary`.  Each
of them are subclasses of the :class:`EagleFile` base class.  The base class
provides functions for parsing, verifying, and writing Eagle files.

Swoop and the Eagle File Format
-------------------------------

Swoop has two goals in terms of conformance to the Eagle file format.  The
first is that Swoop should be able to read any Eagle file produced by a version
of Eagle it supports (currently 6.5-7.3), by Swoop, or by a combination of the
two.

Second, Swoop should only output files that conform to a modified version of
the DTD.  This modified DTD is provided with the Swoop distribution.  It is
based on the DTD that ships with Eagle, but it includes changes to accomodate
files that we observe Eagle to produce in practice.  You can see the changes we
have made by looking at :code:`eagle.dtd.diff` in the source distribution of Swoop.

Swoop also aspires to produce output that specifies a valid Eagle schematic,
library, or board.  This is challenging, since CadSoft doesn't publish a
detailed specification of the file format's semantics (the DTD just specifies
its syntax).  By default, :code:`EagleFile` performs a set of sanity checks
before writing out the file.  If you find that a file produced by Swoop (with
the sanity checks enabled) produces error when loaded by Eagle, please consider
filing a bug report.


EagleFile
---------
.. autoclass:: Swoop.EagleFile

