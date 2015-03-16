from Swoop import EagleFile
import Swoop


class ScanLayersVisitor(Swoop.EagleFilePartVisitor):
    """A visitor to scan the file for all :class:`EagleFilePart` objects a
    :code:`layer` attribute and collected the names of all layers that are used
    somewhere in the file.

    """
    def __init__(self, efp):
        Swoop.EagleFilePartVisitor.__init__(self,efp)
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


class ScanLibraryReferences(Swoop.EagleFilePartVisitor):
    """A visitor to scan an :class:`EagleFile` object and identify all the library components (Libraries,
    Symbols, Packages, Devicesets, and Devices) that are referenced in the
    file.

    """
    
    def __init__(self, efp):
        Swoop.EagleFilePartVisitor.__init__(self,efp)
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
        

class DumpVisitor(Swoop.EagleFilePartVisitor):

    def __init__(self, efp):
        Swoop.EagleFilePartVisitor.__init__(self,efp)

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
    for name in Swoop.From(sch).get_sheets().get_nets().get_name():
        sig =  brd.get_signal(name)
        if sig is None:
            brd.add_signal(Swoop.Signal().
                           set_name(name).
                           set_airwireshidden(False).
                           set_class("0")) # We need to do something smarter here.
        else:
            sig.clear_contactrefs()

        for pinref in (Swoop.From(sch).
                       get_sheets().
                       get_nets().
                       with_name(name).
                       get_segments().
                       get_pinrefs()):

            if sch.get_part(pinref.part).find_device().get_package() is None:
                continue

            pad = (Swoop.From(sch).
                   get_parts().
                   with_name(pinref.get_part()).
                   find_device().
                   get_connects().
                   with_gate(pinref.gate).
                   with_pin(pinref.pin).
                   get_pad().first())

            assert pad is not None

            brd.get_signal(name).add_contactref(Swoop.Contactref().
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

    for a in part.find_technology().get_attributes():
        n.add_attribute(a.clone().
                        set_display("off").
                        set_layer("Document").
                        set_in_library(False))

    for a in part.get_attributes():
        n.add_attribute(a.clone().
                        set_display("off").
                        set_layer("Document"))                                        
    brd.add_element(n)

