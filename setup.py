from setuptools import setup
from setuptools.command.install import install
import os
from codecs import open
import sys

#import argparse
#parser = argparse.ArgumentParser(description="Fix eagle files to make them dtd conforming")
#parser.add_argument("--dtd", required=True,  type=str, nargs=1, dest='dtd', help="Eagle dtd to use.")

class BuildSwoop(install):

    def run(self):
        import GenerateSwoop
        dtd = open("eagleDTD.py", "w")
        if os.environ.get("EAGLE_DTD") is not None:
            os.system("patch " + os.environ["EAGLE_DTD"] + " eagle.dtd.diff -o eagle-swoop.dtd")
            dtd.write('DTD="""')
            dtd.write(open("eagle-swoop.dtd").read())
            dtd.write('"""')
        else:
            sys.stderr.write("===========================================================")
            sys.stderr.write("=== Missing eagle DTD.  Validation will not take place. ===")
            sys.stderr.write("===========================================================")
            dtd.write("DTD=None")

        dtd.close()
        GenerateSwoop.main("Swoop.py")
        install.run(self)

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(os.path.join(here, 'VERSION.txt'), encoding='utf-8') as f:
    version = f.read()

setup(name='Swoop',
      version=version,
      description="Swoop is a Python library for working with CadSoft Eagle files.",
      long_description=long_description,
      classifiers=[
          "Development Status :: 4 - Beta",
          "Intended Audience :: Science/Research",
          "Operating System :: MacOS",
          "Operating System :: POSIX",
          "Operating System :: POSIX :: Linux",
          "Operating System :: Unix",
          "Programming Language :: Python",
          "Topic :: Scientific/Engineering",
          "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
          "Topic :: Software Development :: Embedded Systems",
          "Topic :: System",
          "Topic :: System :: Hardware",
      ],
      author="NVSL, University of California San Diego",
      author_email="swanson@cs.ucsd.edu",
      url="http://nvsl.ucsd.edu/Swoop/",
      py_modules=["CleanupEagle", "eagleDTD", "GenerateSwoop", "SwoopTools", "Swoop"],
      test_suite="test",
      #packages = ["Swoop"],
      #package_dir={'Swoop' : '.'},
      package_data={"Swoop" : ["Swoop.py.jinja", "eagle.dtd.diff"]},
#      requires=["lxml", "Jinja2", "Sphinx"],
      install_requires=["lxml>=3.4.2", "Jinja2>=2.7.3", "Sphinx>=1.3.1"],
#      install_requires=["Jinja2", "lxml"],
      include_package_data=True,
      scripts=["bin/checkEagle.py", "bin/fixEagle.py", "bin/cleanupEagle.py", "bin/mergeLibrary.py"],
      cmdclass={'install': BuildSwoop}
      )


