#!/usr/bin/env python

import Swoop
import argparse
import shutil
import Swoop.tools
import logging as log

# class RelayerV(SwoopTools.EagleFilePartVisitor):
#     def __init__(self, root=None):
#         SwoopTools.EagleFilePartVisitor.__init__(self,root)
#         self.old_layer = old_layer
#         self.new_layer = new_layer

#     def default_pre(self, efp):
#         if hasattr(self, get_layer()):
#             if self.get_layer() == self.old_layer:
#                 self.set_layer(self.new_layer)


def main():
    parser = argparse.ArgumentParser(description="Update layer numbers.")
    parser.add_argument("--file", required=True,  type=str, nargs='+', dest='file', help="Files with layer numbers you want to change")
    parser.add_argument("--layers", required=True, type=str, dest='layers', help="File with layer numbers you want")
    parser.add_argument("-v", required=False, action='store_true', dest='verbose', help="Be verbose")
    parser.add_argument("-n", required=False, action='store_true', dest='dry_run', help="Don't overwrite anything")

    args = parser.parse_args()

    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.info("Verbose output.")
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

    layers = Swoop.LibraryFile.from_file(args.layers)
    new_layers = Swoop.From(layers).get_layers()

    for f in args.file:
        ef = Swoop.EagleFile.from_file(f)

        for newl in new_layers:
            try:
                oldl = ef.get_layer(newl.get_name())
            except:
                continue
            if oldl.get_number() != newl.get_number():
                try:
                    t = ef.get_layer(int(newl.get_number()))
                except:
                    t = None
                if t is not None:
                    log.error("Layer number conflict on {} in {}".format(newl.get_number(), f))
                    raise Exception

                log.info("Changed layer '{}' from {} to {} in {}".format(oldl.get_name(), oldl.get_number(), newl.get_number(), f))
                oldl.set_number(newl.get_number())

        if not args.dry_run:
            ef.write(f)

if __name__ == "__main__":
    main()

