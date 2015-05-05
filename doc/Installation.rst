Installing Swoop
================

Swoop is avalable via pip, and it depends on a few other packages -- namely
`lxml <http://lxml.de/>`_ (for XML parsing) and `Jinja2
<http://jinja.pocoo.org/docs/dev/>`_ (for generating :code:`Swoop.py`), and
`Sphinx <http://sphinx-doc.org/>`_ (for generating the documentation).

It also needs access to the Eagle DTD (document type
descriptor) that specifies the structure of the Eagle file formats.  That file
is the propery of CadSoft (the makers of Eagle) so we cannot distribute it with
Swoop.

Fortunately, CadSoft includes the DTD in the Eagle distribution (which you
should have acquired in accordance with CadSoft's licensing rules for Eagle)
and Swoop will copy that file for its use.  All you need to do is tell the
installer where to find the file by setting the :code:`EAGLE_DTD` environment
variable before installing::

  $ export EAGLE_DTD=<PATH TO YOUR EAGLE DTD>
  $ easy_install Swoop

or, if you need to use :code:`sudo` for installation (e.g., if you are on Mac), you can do::

  $ export EAGLE_DTD=<PATH TO YOUR EAGLE DTD>
  $ sudo -E easy_install Swoop

The :code:`-E` keeps :code:`sudo` from cleaning the environment.

The value you should use for :code:`EAGLE_DTD` will vary depending on the
platform on a Mac it will be something like
:code:`/Applications/EAGLE-7.2.0/doc/eagle.dtd`.  On Linux it will be something
like :code:`/opt/eagle-7.2.0/doc/eagle.dtd`.  If you don't have access to the
dtd, Swoop will still work, but it won't perform validation inputs and outputs.
   
Swoop make some small changes to the DTD before using it for verification.  The
changes reflect non-DTD-conforming Eagle files we see Eagle generate.

Dependencies
------------

Swoop depends on three packages: `lxml <http://lxml.de/>`_ (for XML parsing) and `Jinja2 <http://jinja.pocoo.org/docs/dev/>`_  (for
generating :code:`Swoop.py`), and `Sphinx <http://sphinx-doc.org/>`_ (for generating the documentation).  If you want to install them by hand with :code:`pip`::

  $ pip install lxml jinja2 Sphinx


