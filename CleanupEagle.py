#!/usr/bin/env python

import Swoop
import argparse
import shutil
import SwoopTools
import sys

def removeDeadEFPs(ef):
    """
    Remove all the unused items (symbols, packages, devices, and devicesets) from an eagle file.

    Depending on the file type "unused" means different things:
    
    * For schematics:  Any symbols, devices, packages, or devicesets that are not used in the schematic will be removed.
    
    * For boards: Any packages not used in the board will be removed.

    * For libraries:  Any symbols or packages not mentioned in any deviceset or device will be removed.
    
    :param efp: :class:`EagleFile` to cleanse
    :returns: :code:`self`
    :rtype: :class:`EagleFile`

    """
    deletedSomething = True;
    while deletedSomething:
        deletedSomething = False
        packages = set()
        symbols = set()
        devices = set()
        devicesets = set()
        libraries = set()

        if isinstance(ef, Swoop.LibraryFile):
            libs = [ef.get_library()]
        else:
            libs = ef.get_libraries()
                        
        for l in libs:
            libraries.add(l)

            for s in Swoop.From(l).get_symbols():
                symbols.add(s)

            for p in Swoop.From(l).get_packages():
                packages.add(p)
            
            for ds in Swoop.From(l).get_devicesets():
                devicesets.add(ds)

                for d in ds.get_devices():
                    devices.add(d)

                for g in ds.get_gates():
                    symbols.discard(g.find_symbol())

                for d in ds.get_devices():
                    if d.get_package() is not None:
                        packages.discard(d.find_package())
                        
        if isinstance(ef, Swoop.SchematicFile):
            for p in Swoop.From(ef).get_parts():
                lib = p.find_library()
                libraries.discard(lib)
                devicesets.discard(p.find_deviceset())
                devices.discard(p.find_device())
        elif isinstance(ef, Swoop.BoardFile):
            for p in Swoop.From(ef).get_elements():
                lib = p.find_library()
                libraries.discard(lib)
                packages.discard(p.find_package())
        elif isinstance(ef, Swoop.LibraryFile):
            lib = ef.get_library();
            libraries.discard(lib)
            for s in Swoop.From(lib).get_devicesets().get_gates().get_symbol():
                symbols.discard(lib.get_symbol(s))
            for p in Swoop.From(lib).get_devicesets().get_devices().get_package():
                packages.discard(lib.get_package(p))
            for p in Swoop.From(lib).get_devicesets().get_devices():
                devices.discard(p)
            for ds in Swoop.From(lib).get_devicesets():
                devicesets.discard(ds)
            
        for efp in packages | symbols | devices | devicesets | libraries:
            deletedSomething = True
            efp.detach()
            #print ". " + str(efp),
        #print "|"
    return ef
        
