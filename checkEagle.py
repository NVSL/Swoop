#!/usr/bin/env python

import HighEagle as HE
import argparse
import shutil
from lxml import etree as ET
import sys
import logging as log
import sys, traceback

def countParts(et, tags, attrs):
    for et in et.findall(".//*"):
        if et.tag in tags:
            tags[et.tag] = tags[et.tag] + 1
        else:
            tags[et.tag] =  1
        for i in et.attrib:
            if i in attrs:
                attrs[i] = attrs[i] + 1
            else:
                attrs[i] =  1

def compareEagleElementTrees(orig, new):
    origAttrs = {}
    origTags = {}
    countParts(orig,origTags, origAttrs)
    newAttrs = {}
    newTags = {}
    countParts(new,newTags, newAttrs)

    mismatches = 0
    for i in origAttrs:
        if i not in newAttrs:
            newAttrs[i] = 0

    for i in origTags:
        if i not in newTags:
            newTags[i] = 0
                
    for i in origAttrs:
        if newAttrs[i] != origAttrs[i]:
            log.warning("Attribute count mismatch for '" + i + "': orig=" + str(origAttrs[i]) + "; new=" + str(newAttrs[i]))
            mismatches = mismatches + 1
    for i in origTags:
        if newTags[i] != origTags[i]:
            log.warning("Tag count mismatch for '" + i + "': orig=" + str(origTags[i]) + "; new=" + str(newTags[i]))
            mismatches = mismatches + 1

    return mismatches


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check whether eagle files are dtd conforming")
    parser.add_argument("--file", required=True,  type=str, nargs='+', dest='file', help="files to process")
    parser.add_argument("--scrubbed-suffix", required=False,  type=str, nargs=1, dest='scrubSuffix', help="Suffix for scrubbed output files.  The empty string to overwrite input.")
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
    corruptInput = 0
    for i in args.file:

        if not args.quiet:
            print "Validating " + i + "...",

        try:
            # for the internal check, we compare the input and output.  With
            # bestEffort == True, we can successfully parse illegal input, but
            # since we always produce legal output, they won't match.
            f = HE.EagleFile.from_file(i, bestEffort=(not args.internalCheck))
            #f.write(i+".xml")
            if f.validate():
                goodSoFar = True
                if not args.quiet:
                    print("valid.")
                if args.internalCheck:
                    if compareEagleElementTrees(f.root, f.get_et()) > 0:
                        goodSoFar = False

                if goodSoFar:
                    success += 1
                    if args.scrubSuffix is not None:
                        parts = i.split(".")
                        n = ".".join(parts[0:-1]+args.scrubSuffix + [parts[-1]])
                        f.write(n)
                else:
                    failed += 1
                
            else:
                failed += 1
                if not args.quiet:
                    print("invalid.")
        except HE.EagleFormatError as e:
            corruptInput += 1
            print("corrupt.")
            print e
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
        print "Corrupt Input: " + str(corruptInput)
        print "Invalid: " + str(failed) 
        print "Error: " + str(internalError)
            
    if failed + internalError == 0:
        sys.exit(0)
    else:
        sys.exit(1)
