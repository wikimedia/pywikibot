.. # define a hard line break for HTML
.. |br| raw:: html

   <br />

*****************************
MediaWiki API cross reference
*****************************

See the table below for a cross reference between MediaWiki's API and Pywikibot's API.

.. list-table::
   :header-rows: 1
   :align: left

   * - action
     - APISite method
     - page method
     - other module method
   * - :api:`block<block>`
     - :meth:`blockuser()<pywikibot.site._apisite.APISite.blockuser>`
     - :meth:`User.block()<page.User.block>`
     -
   * - :api:`clientlogin<clientlogin>`
     - :meth:`login()<pywikibot.site._apisite.APISite.login>`
     -
     -
   * - :api:`compare<compare>`
     - :meth:`compare()<pywikibot.site._apisite.APISite.compare>`
     -
     -
   * - :api:`delete<delete>`
     - :meth:`delete()<pywikibot.site._apisite.APISite.delete>`
     - :meth:`BasePage.delete()<page.BasePage.delete>`
     -
   * - :api:`Deletedrevisions<Deletedrevisions>`
     - :meth:`delete()<pywikibot.site._apisite.APISite.delete>`
     - :meth:`BasePage.delete()<page.BasePage.delete>`
     -
   * - :api:`echomarkread<echomarkread>`
     - :meth:`notifications_mark_read()<pywikibot.site._extensions.EchoMixin.notifications_mark_read>`
     -
     - :meth:`echo.Notification.mark_as_read`
   * - :api:`edit<edit>`
     - :meth:`editpage()<pywikibot.site._apisite.APISite.editpage>`
     - :meth:`BasePage.save()<page.BasePage.save>`
       :meth:`BasePage.put()<page.BasePage.put>`
       :meth:`BasePage.touch()<page.BasePage.touch>`
       :meth:`Page.set_redirect_target()<page.Page.set_redirect_target>`
       :meth:`BasePage.change_category()<page.BasePage.change_category>`
     - :meth:`proofreadpage.ProofreadPage.save`
       :meth:`proofreadpage.IndexPage.save`
       :meth:`bot.BaseBot.userPut`
       :meth:`bot.CurrentPageBot.put_current`
       :meth:`BaseUnlinkBot.unlink()<specialbots.BaseUnlinkBot.unlink>`
   * - :api:`emailuser<emailuser>`
     -
     - :meth:`User.send_email()<page.User.send_email>`
     -
   * - :api:`expandtemplates<expandtemplates>`
     - :meth:`expand_text()<pywikibot.site._apisite.APISite.expand_text>`
     - :meth:`BasePage.expand_text()<page.BasePage.expand_text>`
     - :meth:`textlib.getCategoryLinks`
   * - :api:`login<login>`
     - :meth:`login()<pywikibot.site._apisite.APISite.login>`
     -
     -
   * - :api:`logout<logout>`
     - :meth:`logout()<pywikibot.site._apisite.APISite.logout>`
     -
     -
   * - :api:`mergehistory<mergehistory>`
     - :meth:`merge_history()<pywikibot.site._apisite.APISite.merge_history>`
     - :meth:`BasePage.merge_history()<page.BasePage.merge_history>`
     -
   * - :api:`move<move>`
     - :meth:`movepage()<pywikibot.site._apisite.APISite.movepage>`
     - :meth:`BasePage.move()<page.BasePage.move>`
     -
   * - :api:`parse<parse>`
     - :meth:`get_parsed_page()<pywikibot.site._apisite.APISite.get_parsed_page>`
     - :meth:`BasePage.get_parsed_page()<page.BasePage.get_parsed_page>`
     -
   * - :api:`patrol<patrol>`
     - :meth:`patrol()<pywikibot.site._generators.GeneratorsMixin.patrol>`
     -
     -
   * - :api:`protect<protect>`
     - :meth:`protect()<pywikibot.site._apisite.APISite.protect>`
     - :meth:`BasePage.protect()<page.BasePage.protect>`
     -
   * - :api:`purge<purge>`
     - :meth:`purgepages()<pywikibot.site._apisite.APISite.purgepages>`
     - :meth:`BasePage.purge()<page.BasePage.purge>`
     - :meth:`ProofreadPage.purge()<proofreadpage.ProofreadPage.purge>`
   * - :api:`query<query>`
     - *see separate table (not yet)*
     -
     -
   * - :api:`revisiondelete<revisiondelete>`
     - :meth:`deleterevs()<pywikibot.site._apisite.APISite.deleterevs>`
     -
     -
   * - :api:`rollback<rollback>`
     - :meth:`rollbackpage()<pywikibot.site._apisite.APISite.rollbackpage>`
     -
     -
   * - :api:`shortenurl<shortenurl>`
     - :meth:`create_short_link()<pywikibot.site._extensions.UrlShortenerMixin.create_short_link>`
     - :meth:`BasePage.create_short_link()<page.BasePage.create_short_link>`
     -
   * - :api:`sitematrix<sitematrix>`
     - :meth:`fromDBName()<pywikibot.site._apisite.APISite.fromDBName>`
     -
     -
   * - :api:`thank<thank>`
     - :meth:`thank_revision()<pywikibot.site._extensions.ThanksMixin.thank_revision>`
     -
     -
   * - :api:`unblock<unblock>`
     - :meth:`unblockuser()<pywikibot.site._apisite.APISite.unblockuser>`
     - :meth:`User.unblock()<page.User.unblock>`
     -
   * - :api:`undelete<undelete>`
     - :meth:`undelete()<pywikibot.site._apisite.APISite.undelete>`
     - :meth:`BasePage.undelete()<page.BasePage.undelete>`
     -
   * - :api:`upload<upload>`
     - :meth:`upload()<pywikibot.site._apisite.APISite.upload>`
       :meth:`site.Uploader.upload()<pywikibot.site._upload.Uploader.upload>`
     - :meth:`FilePage.upload()<page.FilePage.upload>`
     - :meth:`UploadRobot.upload_file()<specialbots.UploadRobot.upload_file>`
   * - :api:`watch<watch>`
     - :meth:`watch()<pywikibot.site._apisite.APISite.watch>`
     - :meth:`BasePage.watch()<page.BasePage.watch>`
     -
