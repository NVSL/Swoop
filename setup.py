from distutils.core import setup
from setuptools.command.install import install
import GenerateSwoop
import os
import sys

import argparse
#parser = argparse.ArgumentParser(description="Fix eagle files to make them dtd conforming")
#parser.add_argument("--dtd", required=True,  type=str, nargs=1, dest='dtd', help="Eagle dtd to use.")

class BuildSwoop(install):

    def run(self):
        dtd = open("eagleDTD.py", "w")
        if os.environ.get("EAGLE_DTD") is not None:
            os.system("patch " + os.environ["EAGLE_DTD"] + " eagle.dtd.diff -o eagle-swoop.dtd")
            dtd.write('DTD="""')
            dtd.write(open("eagle-swoop.dtd").read())
            dtd.write('"""')
        else:
            sys.stderr.write("Missing eagle DTD.  Validation will not take place.")
            dtd.write("DTD=None")

        dtd.close()
        GenerateSwoop.main("Swoop.py")
        install.run(self)


setup(name='Swoop',
      version='0.2',
      description="Swoop is a Python library for working with CadSoft Eagle files.",
      long_description="""Swoop is a library of Python objects for representing and manipulating
Cadsoft Eagle board, schematic, and library files used in designing printed
circuit boards (PCBs).  It parses an input Eagle file, creates a internal
representation data structure that represents the file's contents,
provides accessors and mutators to query, read, and modify those contents, and
generates valid Eagle files as output.

Swoop was created by the `NVSL <http://nvsl.ucsd.edu/>`_ at  `UCSD <http://www.ucsd.edu/>`_ as part of the  `Gadgetron project <http://nvsl.ucsd.edu/index.php?path=projects/gadget>`_. 
      """,
      author="NVSL, University of California San Diego",
      author_email="swanson@cs.ucsd.edu",
      url="http://nvsl.ucsd.edu/Swoop/",
      py_modules=["CleanupEagle", "eagleDTD", "GenerateSwoop", "Swoop", "SwoopTools"],
      requires=["lxml (>=3.4.2)", "jinja2 (>=2.7.3)", "Sphinx (>=1.3.1)"],
      scripts=["bin/checkEagle.py", "bin/fixEagle.py", "bin/cleanupEagle.py", "bin/mergeLibrary.py"],
      cmdclass={'install': BuildSwoop}
      )


