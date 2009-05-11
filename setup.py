import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(name='pywikibot',
      version ='0.1.0dev',
      description ='Python Wikipedia Bot Framework',
      packages = find_packages(),
      license = 'MIT',
      install_requites = ['simplejson', 'httplib2>=0.4.0']
     )

