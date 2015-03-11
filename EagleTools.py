from Swoop import EagleFile
import Swoop

class EaglePartVisitor(object):
    """A visitor utility class for :class:`EagleFile` objects.  

    The class traverses a subtree of :class:`EagleFilePart` objects in
    depth-first order.  Subclasses can define *vistor* methods of the form
    :code:`*X*_pre()` and :code:`*X*_post()` that will be called in pre-order
    and post-order during the traversal.  If a subclass doesn't define a
    particular an :class:`EagleFilePart` subclass, :meth:`default_pre` and
    :meth:`default_pre` will be used instead.

    Subclasses can also override :meth:`visitFilter` and
    :meth:`decendFilter` to control which :class:`EagleFilePart` the visitor
    invokes the visitor methods on and which :class:`EagleFilePart` the visitor
    decends into.  By default, both visitor methods are called on all
    :class:`EagleFilePart` objects and in the visitor always decends.

    The :meth:`go` method start execution.  It also returns :code:`self` so
    you can easily apply accessor functions after execution.  You can also call
    :meth:`visit` on an :class:`EagleFilePart` object to visit the subtree
    underneath it

    For example, here's a simple visitor that counts the total number of
    :class:`EagleFileParts` in a file and, separately, the number of
    :class:`Element` objects:
    
    .. code-block:: python

        class Counter(EaglePartVisitor):
            def __init__(self, root=None):
                EaglePartVisitor.__init__(self,root)
                self.count = 0;
                self.elementCount = 0
            def default_pre(self):
                self.count += 1
            def Element_pre(self):
                self.count += 1
                self.elementCount += 1
    
    And you can use it like so:

    .. code-block:: python

        from Swoop import *
        from EagleTools import *
        ef = EagleFile.from_file(my_file)
        c = Counter(ef)
        print "The file has this many parts: " + str(c.go().count)
        print "There are this many Elements: " + str(c.elementCount)

    """

    def __init__(self, root=None):
        self.root = root

    def go(self):
        """
        Start the visiting process.
        
        :rtype: :code:`self`
        """
        self.visit(self.root)
        return self
    
    def visitFilter(self, e):
        """Predicate that determines whether to call the visit functions on this
        :class:`EagleFilePart`.  The default implementation returns ``True``.
        
        :param e: The :class:`EagleFilePart` to be visited.
        :rtype:   ``Bool``

        """
        return True

    def decendFilter(self, e):
        """Predicate that determines whether to decend into the subtree rooted at ``e``.  The default implementation returns ``True``.
        
        :param e: The root :class:`EagleFilePart`.
        :rtype:   ``Bool``

        """
        return True


    def default_pre(self,e):
        """Default pre-order visitor function.

        This method can return a value that will be passed to the corresponding
        post-order visitor function, making it easy to pass state between the
        two.

        The default implementation does nothing and returns ``None``
        
        :param e: The  :class:`EagleFilePart` being visited.
        :rtype: Any

        """
        return None

    def default_post(self,e, context):
        """Default post-order visitor function.  The default implementation does nothing.
        
        :param e: The  :class:`EagleFilePart` being visited.
        :param context: The value returned by corresponding pre-order visitor.
        :rype: ``None``
        """
        pass

    def visit(self, efp):
        """ Run this visitor on the subtree rooted at ``efp``.
        
        :param efp: The :class:`EagleFilePart` at the root of the tree.
        :rtype:  ``self``
        """
        if self.visitFilter(efp):
            try:
                pre = getattr(self,type(efp).__name__ + "_pre")
                context = pre(efp)
            except AttributeError:
                context = self.default_pre(efp)

        if self.decendFilter(efp):
            for e in efp.get_children():        
                self.visit(e)
                
        if self.visitFilter(efp):
            try:
                post = getattr(self,type(efp).__name__ + "_post")
                post(efp,context)
            except AttributeError:
                self.default_post(efp,context)
        return self

class ScanLayersVisitor(EaglePartVisitor):
    """A visitor to scan the file for all :class:`EagleFilePart` objects a
    :code:`layer` attribute and collected the names of all layers that are used
    somewhere in the file.

    """
    def __init__(self, efp):
        EaglePartVisitor.__init__(self,efp)
        self.foundLayers = set()
        self.definedLayers = set()

    def default_pre(self, efp):
        if "layer" in efp.__dict__ and efp.layer is not None:
            assert type(efp.layer) == str
            self.foundLayers.add(efp.layer)

    def Layer_pre(self, efp):
        assert type(efp) == Swoop.Layer
        self.definedLayers.add(efp.name)
        
    def getUsedLayers(self):
        """
        Get a list of the names of layers used in the file.

        :rtype: List of :code:`str`
        """
        return list(self.foundLayers)

    def getUnusedLayers(self):
        """
        Get a list containing the names of unused layers.

        :rtype: List of :code:`str`

        """
        return list(self.definedLayers - self.foundLayers)

    def getDefinedLayers(self):
        """ 
        Get a list of all the layers defined in the file.

        :rtype: List of :code:`str`

        """
        return list(self.definedLayers)


class ScanLibraryReferences(EaglePartVisitor):
    """A visitor to scan an :class:`EagleFile` object and identify all the library components (Libraries,
    Symbols, Packages, Devicesets, and Devices) that are referenced in the
    file.

    """
    
    def __init__(self, efp):
        EaglePartVisitor.__init__(self,efp)
        self.usedEFPs = set()
        
    def Part_pre(self, efp):

        self.usedEFPs.add(efp.get_library())
        self.usedEFPs.add(efp.get_deviceset())
        self.usedEFPs.add(efp.get_device())

        if efp.get_device().get_package():
            self.usedEFPs.add(efp.get_device().get_package())
        
        for i in efp.get_deviceset().get_gates():
            self.usedEFPs.add(i.get_symbol())

    def Element_pre(self, efp):
        raise NotImplementedError("Support for scanning board files not implemented yet")

    def get_referenced_efps(self):
        """
        Return a list of all the library components that are used.
    
        :rtype: List of :class:`EagleFilePart`
        """
        return list(self.usedEFPs)
        

class DumpVisitor(EaglePartVisitor):

    def __init__(self, efp):
        EaglePartVisitor.__init__(self,efp)

    def default_pre(self, efp):
        print "pre " + type(efp).__name__

    def default_post(self, efp):
        print "pre " + type(efp).__name__

def mergeLayers(src, dst, force=False):
    """
    Merge layers from the :class:`EagleFile` :code:`src` into :class:`EagleFile` :code:`dst`.  If there is some conflict
    between the two (different names for the same layer number or vice versa),
    then raise an exception (unless :code:`force == True`)

    :param src: The :class:`EagleFile` to update.
    :param dst:  The :class:`EagleFile` to draw layers from.
    :param force:  If :code:`True` overwrite the layers.  Otherwise, throw an :class:`SwoopError` on conflict.

    """
    for srcLayer in src.get_layers().values():
        for dstLayer in dst.get_layers().values():
            if ((srcLayer.name == dstLayer.name and srcLayer.number != dstLayer.number) or 
                (srcLayer.name != dstLayer.name and srcLayer.number == dstLayer.number)):
                if force:
                    try:
                        src.remove_layer(dstLayer)
                    except:
                        pass
                else:
                    raise Swoop.SwoopError("Layer mismatch: " +
                                            str(src.filename) + " <" + str(srcLayer.number) + ", '" + str(srcLayer.name) +"'>; " +
                                            str(dst.filename) +" = <" + str(dstLayer.number) + ", '" + str(dstLayer.name) +"'>;")
        if srcLayer.name not in dst.get_layers():
            dst.add_layer(srcLayer.clone())
        
def normalizeLayers(ef, layers, force=False):
    """Clean up layers in a file.  First, remove all unused layers, then merge in
    the layers from :class:`EagleFile` object :code:`layers`.  If :code:`force
    == True`, overwrite layers in :code:`ef` with the layers even if there is a
    conflict.

    :param ef: The :class:`EagleFile` to update.
    :param layers:  The :class:`EagleFile` to draw layers from.
    :param force:  If :code:`True` overwrite the layers.  Otherwise, throw an :class:`SwoopError` on conflict.

    """

    for i in ScanLayersVisitor(ef).go().getUnusedLayers():
        #print "removed " + str(i)
        ef.remove_layer(i)
        
    mergeLayers(layers, ef, force)

def rebuildBoardConnections(sch, brd):
    """
    Update the signals in :code:`brd` to match the nets in :code:`sch`.  This will set up the connections, but won't draw the air wires.  You can use Eagle's :code:`ripup` command to rebuild those.

    :param sch: :class:`SchematicFile` object and source of the connection information.
    :param brd: :class:`BoardFile` destination for then connection information.
    :rtype: :code:`None`
    
    """
    #sheets/*/net.name:
    netnames = list(set(reduce(lambda x,y:x+y,[s.get_nets().keys() for s in sch.get_sheets()], [])))
    for name in netnames:
        sig =  brd.get_signal(name)
        if sig is None:
            brd.add_signal(Swoop.Signal().
                           set_name(name).
                           set_airwireshidden(False).
                           set_class("0")) # We need to do something smarter here.
        else:
            sig.clear_contactrefs()
        #for n in sheets/*/net[name=name]/segment/pinref:
        for sheet in sch.get_sheets():
            for net in sheet.get_nets().values():
                if net.name == name:
                    for segment in net.get_segments():
                        for pinref in segment.get_pinrefs():

                            if sch.get_part(pinref.part).find_device().get_package() is None:
                                continue
                            
                            for connect in sch.get_part(pinref.part).find_device().get_connects():
                                if connect.gate == pinref.gate and connect.pin==pinref.pin:
                                    pad = connect.get_pad()
                            # pad =(sch.
                            #       get_part(pinref.part).
                            #       find_device().
                            #       search_connects(gate=pinref.gate,pin=pinref.pin).
                            #       get_pad())
                            assert pad is not None
                            
                            brd.signals[name].add_contactref(Swoop.Contactref().
                                                             set_element(pinref.get_part()).
                                                             set_pad(pad))

def propagatePartToBoard(part, brd):
    """
    Copy :code:`part` to ``brd`` by creating a new :class:`Element` and populating it accordingly.
    If the part already exists, it will be replaced.
    
    .. Note::
       This function doesn't update the board's signals.  You can run :meth:`rebuildBoardConnections` to do that.

    :param part: :class:`Part` object that to propagate.
    :param brd: Destination :class`BoardFile`.
    :rtype: :code:`None`

    """
    n =(Swoop.Element().
        set_name(part.get_name()).
        set_library(part.get_library()).
        set_package(part.
                    find_package().
                    get_name()
                ).
        set_value(part.get_value()).
        set_x(0).
        set_y(0))

    for a in part.find_technology().get_attributes().values():
        n.add_attribute(a.clone().
                        set_display("off").
                        set_layer("Document").
                        set_in_library(False))

    for a in part.get_attributes().values():
        n.add_attribute(a.clone().
                        set_display("off").
                        set_layer("Document"))                                        
    brd.add_element(n)

