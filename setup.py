import sys

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

if sys.version_info[0] != 2:
    raise RuntimeError("ERROR: Pywikipediabot only runs under Python 2")
if sys.version_info[1] < 5:
    raise RuntimeError("ERROR: Pywikipediabot only runs under Python 2.5 or higher")
elif sys.version_info[1] == 5:
    depend = ['simplejson', 'httplib2>=0.6.0']
else:
    depend = ['httplib2>=0.6.0']

setup(name='Pywikipediabot',
      version ='2.0alpha',
      description ='Python Wikipedia Bot Framework',
      license = 'MIT',
      packages = find_packages(),
      install_requires = depend
     )

# automatically launch generate_user_files.py

import subprocess
python = sys.executable
python = python.replace("pythonw.exe", "python.exe") # for Windows
ignore = subprocess.call([python, "generate_user_files.py"])