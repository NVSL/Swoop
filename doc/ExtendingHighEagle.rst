Extending the HighEagle IR
==========================

The HighEagle IR is meant to be extensible.  To build an extentsion, you can
create subclass of any of the classes that HighEagle IR defines and then
configure HighEagle to use that class in place of the default class.

HighEagle IR determines which type of object to build for each tag in the Eagle
file by consulting the :code:`HighEagle.classMap` variable.  This map defines the mapping
between tag names and :class:`EagleFilePart` subclasses.

For instance if you wanted to add a :code:`set_location()` method to
:class:`Element` you could write the following:

.. code-block:: python

    import HighEagle as HE
    class MyElement(HE.Element):
        def __init__(self):
            HE.Element.__init__(self)

        def set_location(x,y):
            self.set_x(x)
            self.set_y(y)

    HE.classMap["element"] MyElement


