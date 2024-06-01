*******************************
:mod:`site` --- MediaWiki sites
*******************************

.. py:module:: site
   :synopsis: Library module representing MediaWiki sites (wikis)

.. automodule:: pywikibot.site
   :no-members:
   :noindex:

:mod:`BaseSite<pywikibot.site._basesite>` --- Base Class for Sites
==================================================================

.. py:module:: site._basesite
   :synopsis: Objects with site methods independent of the communication interface

.. automodule:: pywikibot.site._basesite

   .. autoclass:: BaseSite

      .. method:: linktrail()

         Return regex for trailing chars displayed as part of a link.

         .. note: Returns a string, not a compiled regular expression object.
         .. seealso:: :meth:`family.Family.linktrail`
         .. deprecated:: 7.3
            Only supported as :class:`APISite<pywikibot.site._apisite.APISite>`
            method. Use :meth:`APISite.linktrail
            <pywikibot.site._apisite.APISite.linktrail>`

         :rtype: str

      .. method:: category_redirects(fallback: str = '_default')

         Return list of category redirect templates.

         .. seealso:: :meth:`family.Family.category_redirects`

         :rtype: list[str]


      .. method:: get_edit_restricted_templates()

         Return tuple of edit restricted templates.

         .. versionadded:: 3.0
         .. seealso:: :meth:`family.Family.get_edit_restricted_templates`

         :rtype: tuple[str, ...]


      .. method:: get_archived_page_templates()

         Return tuple of edit restricted templates.

         .. versionadded:: 3.0
         .. seealso:: :meth:`family.Family.get_archived_page_templates`

         :rtype: tuple[str, ...]


      .. method:: disambig(fallback = '_default')

         Return list of disambiguation templates.

         .. seealso:: :meth:`family.Family.disambig`

         :param str | None fallback:
         :rtype: list[str]


      .. method:: protocol()

         The protocol to use to connect to the site.

         May be overridden to return 'http'. Other protocols are not
         supported.

         .. versionchanged:: 8.2
            ``https`` is returned instead of ``http``.
         .. seealso:: :meth:`family.Family.protocol`

         :return: protocol that this family uses


.. py:module:: site._apisite
   :synopsis: Objects representing API interface to MediaWiki site

:mod:`APISite<pywikibot.site.\_apisite>` --- API Interface for Sites
====================================================================

.. automodule:: pywikibot.site._apisite

.. automodule:: pywikibot.site._extensions
   :synopsis: Objects representing API interface to MediaWiki site extenstions

.. automodule:: pywikibot.site._generators
   :synopsis: Objects representing API generators to MediaWiki site

:mod:`DataSite<pywikibot.site.\_datasite>` --- API Interface for Wikibase
=========================================================================

.. py:module:: site._datasite
   :synopsis: Objects representing API interface to Wikibase site

.. automodule:: pywikibot.site._datasite

:mod:`Obsolete Sites<pywikibot.site._obsoletesites>` --- Outdated Sites
=======================================================================

.. py:module:: site._obsoletesites
   :synopsis: Objects representing obsolete MediaWiki sites

.. automodule:: pywikibot.site._obsoletesites

:mod:`Siteinfo<pywikibot.site._siteinfo>` --- Site Info Container
=================================================================

.. py:module:: site._siteinfo
   :synopsis: Objects representing site info data contents

.. automodule:: pywikibot.site._siteinfo

:mod:`Namespace<pywikibot.site._namespace>` --- Namespace Object
================================================================

.. py:module:: site._namespace
   :synopsis: Objects representing Namespaces of MediaWiki site

.. automodule:: pywikibot.site._namespace

:mod:`TokenWallet<pywikibot.site._tokenwallet>` --- Token Wallet
================================================================

.. py:module:: site._tokenwallet
   :synopsis: Objects representing api tokens

.. automodule:: pywikibot.site._tokenwallet

:mod:`Uploader<pywikibot.site._upload>` --- Uploader Interface
==============================================================

.. py:module:: site._upload
   :synopsis: Objects representing API upload to MediaWiki site

.. automodule:: pywikibot.site._upload
