************************
Provide your own scripts
************************

You may provide your own scripts as a **Pywikibot** plugin. All you have
to do is to bind your package and define an entry point for pywikibot.

.. caution:: ``pywikibot >= 9.4.0`` is required for this possibility.

For example having package files like this::

  my_pwb_scripts/
  ├── LICENSE
  ├── pyproject.toml
  ├── README.md
  ├── src/
  │   └── wikidata_scripts/
  │       ├── __init__.py
  │       ├── drop_entities.py
  │       └── show_entities.py
  └── tests/


Add the following code in your ``wikidata_scripts.__init__.py``:

.. code-block:: python

   from pathlib import Path
   base_dir = Path(__file__).parent

Add *Pywikibot* dependency and register the entry point, which is the
``base_dir`` above, within your preferred config file:

.. tabs::
   .. tab:: pyproject.toml

      .. code-block:: toml

         [project]
         dependencies = [
             "pywikibot >= 9.4.0",
         ]

         [project.entry-points."pywikibot"]
         scriptspath = "wikidata_scripts:base_dir"


   .. tab:: setup.cfg

      .. code-block:: ini

         [options]
         install_requires =
             pywikibot >= 9.4.0

         [options.entry_points]
         pywikibot =
             scriptspath = wikidata_scripts:base_dir

   .. tab:: setup.py

      .. code-block:: python

         from setuptools import setup

         setup(
             install_requires=[
                 'pywikibot >= 9.4.0',
             ],
             entry_points={
                 'pywikibot': [
                     'scriptspath = wikidata_scripts:base_dir',
                 ]
             }
         )

After installing your package scripts are available via :mod:`pwb` wrapper and
can be invoked like this:

.. tabs::

   .. tab:: Unix/macOS

      .. code-block:: shell

         $ pwb <global options> show_entities <scripts options>

   .. tab:: Windows

      .. code-block:: shell

         pwb <global options> show_entities <scripts options>

.. note:: If you have several Pywikibot scripts installed, there script names
   must be different; otherwise the started script might not that you have
   expected.
.. warning:: This guide is not tested. Test it locally before uploading to pypi.
