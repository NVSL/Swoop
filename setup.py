from setuptools import setup
from setuptools.command.build_py import build_py
import os
from codecs import open
import sys

#import argparse
#parser = argparse.ArgumentParser(description="Fix eagle files to make them dtd conforming")
#parser.add_argument("--dtd", required=True,  type=str, nargs=1, dest='dtd', help="Eagle dtd to use.")

class BuildSwoop(build_py):

    def run(self):
        import Swoop.GenerateSwoop
        dtd = open("Swoop/eagleDTD.py", "w")
        os.system("patch Swoop/eagle-7.2.0.dtd Swoop/eagle.dtd.diff -o Swoop/eagle-swoop.dtd")
        dtd.write('DTD="""')
        dtd.write(open("Swoop/eagle-swoop.dtd").read())
        dtd.write('"""')
        dtd.close()
        Swoop.GenerateSwoop.main("Swoop/Swoop.py")
        build_py.run(self)

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
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7",
          "Topic :: Scientific/Engineering",
          "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
          "Topic :: System",
          "Topic :: System :: Hardware",
      ],
      author="NVSL, University of California San Diego",
      author_email="swanson@cs.ucsd.edu",
      url="http://nvsl.ucsd.edu/Swoop/",
      test_suite="test",
      packages = ["Swoop", "Swoop.ext", "Swoop.tools"],
      package_dir={
          'Swoop' : 'Swoop',
      },
      package_data={
          "" : ["*.rst"],
          "Swoop" : ["Swoop/Swoop.py.jinja", "Swoop/eagle.dtd.diff", "Swoop/eagle.dtd"]
      },
      install_requires=["lxml>=3.4.2",  "Sphinx>=1.3.1"],
      setup_requires=["Jinja2>=2.7.3"],
      include_package_data=True,
      entry_points={
        'console_scripts': [
            'cleanupEagle = Swoop.tools.CleanupEagle:main',
            'checkEagle = Swoop.tools.CheckEagle:main',
            'mergeLibrary = Swoop.tools.MergeLibrary:main',
            'fixEagle = Swoop.tools.FixEagle:main'
            ]
        },
      keywords = "PCB Eagle CAD printed circuit boards schematic electronics CadSoft",
      cmdclass={'build_py': BuildSwoop}
      )


