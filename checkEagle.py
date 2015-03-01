#!/usr/bin/env python

import HighEagle as HE
import argparse
import shutil
from lxml import etree as ET
import sys
import logging as log
import sys, traceback

def countParts(et, tags, attrs):
    if et.tag in tags:
        tags[et.tag] = tags[et.tag] + 1
    else:
        tags[et.tag] =  1
        
    for i in et.attrib:
        if i in attrs:
            attrs[i] = attrs[i] + 1
        else:
            attrs[i] =  1

    for s in et:
        countParts(s,tags, attrs)

def compareEagleElementTrees(orig, new):
    origAttrs = {}
    origTags = {}
    countParts(orig,origTags, origAttrs)
    newAttrs = {}
    newTags = {}
    countParts(new,newTags, newAttrs)

    for i in origAttrs:
        if i not in newAttrs:
            newAttrs[i] = 0

    for i in origTags:
        if i not in newTags:
            newTags[i] = 0
                
    for i in origAttrs:
        if newAttrs[i] != origAttrs[i]:
            log.warning("Attribute count mismatch for '" + i + "': orig=" + str(origAttrs[i]) + "; new=" + str(newAttrs[i]))
    for i in origTags:
        if newTags[i] != origTags[i]:
            log.warning("Tag count mismatch for '" + i + "': orig=" + str(origTags[i]) + "; new=" + str(newTags[i]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check whether eagle files are dtd conforming")
    parser.add_argument("--file", required=True,  type=str, nargs='+', dest='file', help="files to process")
    parser.add_argument("-v", required=False, action='store_true', dest='verbose', help="Be verbose")
    parser.add_argument("-q", required=False, action='store_true', dest='quiet', help="Be silent")
    parser.add_argument("--internal-check", required=False, action='store_true', dest='internalCheck', help="Do checks on HighEagle internals")
    parser.add_argument("--stop-on-error", required=False, action='store_true', dest='stopOnError', help="Stop on first error.")
    parser.add_argument("--crash-on-error", required=False, action='store_true', dest='crashOnError', help="Don't catch exceptions.")

    args = parser.parse_args()
    
    if args.verbose:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
        log.info("Verbose output.")
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

    success = 0
    failed = 0
    internalError = 0

    for i in args.file:

        if not args.quiet:
            print "Validating " + i + "...",

        try:
            f = HE.EagleFile.from_file(i)
            f.write(i+".xml")
            if f.validate():
                success += 1
                if not args.quiet:
                    print("valid.")
                if args.internalCheck:
                    compareEagleElementTrees(f.root,
                                             f.get_et())
            else:
                failed += 1
                if not args.quiet:
                    print("invalid.")
        except Exception as e:
            internalError += 1
            if args.crashOnError:
                ex_type, ex, tb = sys.exc_info()
                traceback.print_tb(tb)
                raise e
            if not args.quiet:
                print "HighEagle error: " + str(e)
                
        if args.stopOnError and failed + internalError != 0:
            break
        
    if not args.quiet:
        print "Valid: " + str(success)
        print "Invalid: " + str(failed) 
        print "Error: " + str(internalError)
            
    if failed + internalError == 0:
        sys.exit(0)
    else:
        sys.exit(1)
