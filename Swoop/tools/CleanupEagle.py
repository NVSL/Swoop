#!/usr/bin/env python

import Swoop
import Swoop.tools
import argparse
import shutil
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
                #print "found " + p.get_name()
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
                # print p.get_name()
                # print p.get_library()
                # print lib.get_name()
                # print p.get_deviceset()
                # print Swoop.From(lib.get_devicesets()).get_name()
                # print p.find_deviceset().get_name()
                # print
                for g in Swoop.From(p.find_deviceset()).get_gates().get_symbol():
                    symbols.discard(lib.get_symbol(g))

        elif isinstance(ef, Swoop.BoardFile):
            for p in Swoop.From(ef).get_elements():
                lib = p.find_library()
                #print "keeping " + lib.get_name()
                libraries.discard(lib)
                #print "keeping " + p.get_package()
                #print "keeping " + p.find_package().get_name()
                packages.discard(p.find_package())
                #assert Swoop.From(libs).get_packages().with_name("ROTARY-ENCODER-W/BUTTON-ADAFRUIT377").count() > 0
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
        for l in [packages,symbols , devices , devicesets , libraries]:
            for efp in l:
                deletedSomething = True
                efp.detach()
    return ef
        
def main(argv = None):
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(description="Remove unused library items from a schematic or board.")
    parser.add_argument("--file", required=True,  type=str, nargs=1, dest='file', help="files to process")
    parser.add_argument("--out", required=True,  type=str, nargs=1, dest='out', help="output file")
    args = parser.parse_args(argv)
    
    ef = Swoop.EagleFile.from_file(args.file[0])

    removeDeadEFPs(ef)

    ef.write(args.out[0])


