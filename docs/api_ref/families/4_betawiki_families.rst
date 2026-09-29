********************************************
:mod:`families` --- Beta Family Config Files
********************************************

Family configuration files for the Wikimedia Beta Cluster hosted at
``beta.wmcloud.org``.

The Beta Cluster is a testing environment. See the `Beta Meta-Wiki
<https://meta.wikimedia.beta.wmcloud.org/wiki/Main_Page>`_
for further information about the Beta Cluster.

The name of a Beta family is formed by prefixing the regular Wikimedia family
name with ``beta``. For example, the family ``wikipedia`` becomes
``betawikipedia`` and ``wikisource becomes ``betawikisource``.

A Beta wiki can be selected by specifying the family and language code:

.. code-block:: python

   site = pywikibot.Site('de', 'betawikipedia')

Alternatively, the ``family:code`` notation, as used for the
:attr:`BaseSite.sitename`, can be used:

.. code-block:: python

   site = pywikibot.Site('betawikipedia:de')

.. note::
   Not all Wikimedia Beta wikis have a separate Beta family. Some Beta sites
   are available through their regular family using the ``beta`` code, for
   example :attr:`commons:beta<families.commons_family.Family.test_codes>`,
   :attr:`meta:beta<families.meta_family.Family.test_codes>`, and
   :attr:`wikidata:beta<families.wikidata_family.Family.test_codes>`.

   For projects with a separate Beta family, the Beta family should be used
   instead of the ``beta`` code of the regular family if they refer to the
   same URI. For example, use :mod:`betawikisource:en<betawikisource_family>`
   instead of :attr:`wikisource:beta
   <families.wikisource_family.Family.test_codes>`.

   Some sites have the same code in the regular and Beta families but refer
   to different wikis. For example, :attr:`wikipedia:test
   <families.wikipedia_family.Family.test_codes>` and :mod:`betawikipedia:test
   <families.betawikipedia_family>` refer to https://test.wikipedia.org and
   https://test.wikipedia.beta.wmcloud.org, respectively. The same applies to
   ``wikipedia:test2`` and ``betawikipedia:test2``.

   :mod:`Wikiversity<families.wikiversity_family>` provides different testing
   environments under the beta code and their Beta family. ``wikiversity:beta``
   refers to https://beta.wikiversity.org, while :mod:`betawikiversity:en
   <families.betawikiversity_family>` refers
   to https://en.wikiversity.beta.wmcloud.org. These are separate wikis.

   Beta :mod:`Wikinews<families.wikinews_familiy>` is not supported because all
   Wikinews sites are marked as closed since version 11.3. See :phab:`T421796`.

:mod:`families.betawikibooks\_family` --- Beta Wikibooks
========================================================

.. automodule:: families.betawikibooks_family
   :synopsis: Family module for Beta Wikibooks

:mod:`families.betawikipedia\_family` --- Beta Wikipedia
========================================================

.. automodule:: families.betawikipedia_family
   :synopsis: Family module for Beta Wikipedia

:mod:`families.betawikiquotes\_family` --- Beta Wikiquotes
==========================================================

.. automodule:: families.betawikiquotes_family
   :synopsis: Family module for Beta Wikiquotes

:mod:`families.betawikisource\_family` --- Beta Wikisource
==========================================================

.. automodule:: families.betawikisource_family
   :synopsis: Family module for Beta Wikisource

:mod:`families.betawikiversity\_family` --- Beta Wikiversity
============================================================

.. automodule:: families.betawikiversity_family
   :synopsis: Family module for Beta Wikiversity

:mod:`families.betawikivoyage\_family` --- Beta Wikivoyage
==========================================================

.. automodule:: families.betawikivoyage_family
   :synopsis: Family module for Beta Wikivoyage

:mod:`families.betawiktionary\_family` --- Beta Wiktionary
==========================================================

.. automodule:: families.betawiktionary_family
   :synopsis: Family module for Beta Wiktionary
