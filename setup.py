from distutils.core import setup
from setuptools.command.install import install
import GenerateSwoop

class BuildSwoop(install):

    def run(self):
        dtd = open("eagleDTD.py", "w")
        dtd.write('DTD="""')
        dtd.write(open("eagle-tweaked.dtd").read())
        dtd.write('"""')
        dtd.close()
        GenerateSwoop.main("Swoop.py")
        install.run(self)


setup(name='Swoop',
      version='0.2',
      description="Python Library for Working with CadSoft Eagle Files",
      long_description="""Swoop is a library of Python objects for representing and manipulating
Cadsoft Eagle board, schematic, and library files used in designing printed
circuit boards (PCBs).  It parses an input Eagle file, creates a internal
representation data structure that represents the file's contents,
provides accessors and mutators to query, read, and modify those contents, and
generates valid Eagle files as output.
      """,
      author="NVSL, University of California San Diego",
      author_email="swanson@cs.ucsd.edu",
      url="http://nvsl.ucsd.edu/Swoop/",
      py_modules=['Swoop'],
      requires=["lxml (>=3.4.2)", "jinja2 (>=2.7.3)", "Sphinx (>=1.3.1)"],
      scripts=["bin/checkEagle.py", "bin/fixEagle.py", "bin/cleanupEagle.py", "bin/mergeLibrary.py"],
      cmdclass={'install': BuildSwoop}
      )

