*******************
:mod:`login` module
*******************

Pywikibot supports several login methods to authenticate with
MediaWiki-based wikis. Here is an overview of Pywikibot login methods:

.. list-table::
   :header-rows: 1
   :align: left

   * - Method
     - Secure
     - Auto login
     - Use Cases / Notes
     - API References
   * - BotPassword
     - ✅✅
     - ✅
     - Preferred for most bots; safe, scoped credentials
     - :class:`login.ClientLoginManager` :class:`login.BotPassword`
   * - OAuth
     - ✅✅
     - ✅
     - For complex bots, shared apps, or broader API access
     - :class:`login.OauthLoginManager`
   * - 2FA Login
     - ✅✅
     - ❌
     - 2FA support e.g for interactive admin scripts
     - :class:`login.ClientLoginManager`
   * - Login with email token
     - ✅
     - ❌
     - Email token login e.g. for semi-automated bots or user supporting scripts
     - :class:`login.ClientLoginManager`
   * - Manual login
     - ❌
     - ❌
     - No longer supported on Wikimedia sites
     - :class:`login.ClientLoginManager`
   * - Cookie-based login
     - ➖
     - ✅
     - Session reuse ogin; not a standalone method
     - :class:`comms.http.PywikibotCookieJar`
   * - CentralAuth SUL login
     - ➖
     - ✅
     - Automatic across Wikimedia projects once logged in
     -

.. seealso::
   - :mod:`pywikibot.scripts.login`
   - :mod:`pywikibot.scripts.generate_user_files`
   - :manpage:`BotPasswords`
   - :api:`Login`


.. automodule:: login
   :synopsis: Library to log the bot in to a wiki account
