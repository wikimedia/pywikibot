=========================================================================
**This is a package to build robots for MediaWiki wikis like Wikipedia.**
=========================================================================


Please do not play with this package.
-------------------------------------
These programs can actually modify the live wiki on the net, and proper
wiki-etiquette should be followed before running it on any wiki.

To get started on proper usage of the bot framework, please refer to:

    `Manual:Pywikibot <https://www.mediawiki.org/wiki/Manual:Pywikibot>`_

.. include:: CONTENT.rst

**External software can be used with Pywikibot:**
  * Pydot, Pyparsing and Graphviz for use with interwiki_graph.py
  * JSON for use with site.py, bot.py
  * MySQLdb to access MySQL database for use with pagegenerators.py
  * PyGoogle to access Google Web API and PySearch to access Yahoo! Search
    Web Services for use with pagegenerators.py


Pywikibot makes use of some modules that are part of python, but that
are not installed by default on some Linux distributions:

  * python-xml (required to parse XML via SaX2)
  * python-celementtree (recommended if you use XML dumps)
  * python-tkinter (optional, used by some experimental GUI stuff)


You need to have at least python version `2.6.5 <http://www.python.org/download/>`_
or newer installed on your computer to be able to run any of the code in this
package, but not 3.0-3.2. It works fine with 3.3-3.4 versions of python installed.
Support for older versions of python is not planned. Some scripts could run with
older python releases. Please refer the manual at mediawiki for further details
and restrictions.


You do not need to "install" this package to be able to make use of
it. You can actually just run it from the directory where you unpacked
it or where you have your copy of the SVN or git sources.


The first time you run a script, the package creates a file named user-config.py
in your current directory. It asks for the family and language code you are
working on and at least for the bot's user name; this will be used to identify
you when the robot is making changes, in case you are not logged in. You may
choose to create a small or extended version of the config file with further
informations. Other variables that can be set in the configuration file, please
check config.py for ideas.


After that, you are advised to create a username + password for the bot, and
run login.py. Anonymous editing is not possible.
