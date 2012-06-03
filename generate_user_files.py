# -*- coding: utf-8  -*-
""" Script to create user files (user-config.py, user-fixes.py) """
#
# (C) Pywikipedia team, 2010-2012
#
__version__ = '$Id$'
#
# Distributed under the terms of the MIT license.
#

import codecs, os, re, sys
import platform

def get_base_dir():
    """Return the directory in which user-specific information is stored.

    This is determined in the following order -
    1.  If the script was called with a -dir: argument, use the directory
        provided in this argument
    2.  If the user has a PYWIKIBOT2_DIR environment variable, use the value
        of it
    3.  Use (and if necessary create) a 'pywikibot' folder (Windows) or
        '.pywikibot' directory (Unix and similar) under the user's home
        directory.

    """
    # copied from config2.py, without the lines that check whether the
    # directory already contains a user-config.py file
    # this code duplication is nasty, should fix
    NAME = "pywikibot"
    for arg in sys.argv[1:]:
        if arg.startswith("-dir:"):
            base_dir = arg[5:]
            sys.argv.remove(arg)
            break
    else:
        if "PYWIKIBOT2_DIR" in os.environ:
            base_dir = os.environ["PYWIKIBOT2_DIR"]
        else:
            is_windows = sys.platform == 'win32'
            home = os.path.expanduser("~")
            if is_windows:
                _win_version = int(platform.version()[0])
                if _win_version == 5:
                    base_dir = os.path.join(home, "Application Data", NAME)
                elif _win_version == 6:
                    base_dir = os.path.join(home, "AppData\\Roaming", NAME)
            else:
                base_dir = os.path.join(home, "."+NAME)
            if not os.path.isdir(base_dir):
                os.makedirs(base_dir, mode=0700)
    if not os.path.isabs(base_dir):
        base_dir = os.path.normpath(os.path.join(os.getcwd(), base_dir))
    return base_dir

base_dir = get_base_dir()
console_encoding = sys.stdout.encoding
# the directory in which generate_user_files.py is located
pywikibot_dir = sys.path[0]

if console_encoding is None or sys.platform == 'cygwin':
    console_encoding = "iso-8859-1"

def listchoice(clist = [], message = None, default = None):

    if not message:
        message = "Select"

    if default:
        message += " (default: %s)" % default

    message += ": "

    for n, i in enumerate(clist):
        print ("%d: %s" % (n + 1, i))

    while True:
        choice = raw_input(message)

        if choice == '' and default:
            return default

        try:
            return clist[int(choice) - 1]
        except:
            print("Invalid response")
    return response

def change_base_dir():
    """Create a new user directory."""
    global base_dir
    while True:
        new_base = raw_input("New user directory? ")
        new_base = os.path.abspath(new_base)
        if os.path.exists(new_base):
            if os.path.isfile(new_base):
                print("ERROR: there is an existing file with that name.")
                continue
            # make sure user can read and write this directory
            if not os.access(new_base, os.R_OK|os.W_OK):
                print("ERROR: directory access restricted")
                continue
            print("OK: using existing directory")
            break
        else:
            try:
                os.mkdir(new_base, 0700)
            except Exception:
                print("ERROR: directory creation failed")
                continue
            print("OK: Created new directory.")
            break

    from textwrap import wrap
    msg = wrap("""WARNING: Your user files will be created in the directory
'%(new_base)s' you have chosen. To access these files, you will either have
to use the argument "-dir:%(new_base)s" every time you run the bot, or set
the environment variable "PYWIKIBOT2_DIR" equal to this directory name in
your operating system. See your operating system documentation for how to
set environment variables.""" % locals(), width=76)
    for line in msg:
        print line
    ok = raw_input("Is this OK? ([yes], [N]o) ")
    if ok in ["Y", "y"]:
        base_dir = new_base
        return True
    print "Aborting changes."
    return False

def file_exists(filename):
    if os.path.exists(filename):
        print("'%s' already exists." % filename)
        return True
    return False

def create_user_config():
    _fnc = os.path.join(base_dir, "user-config.py")
    if not file_exists(_fnc):
        known_families = re.findall(r'(.+)_family.py\b',
                                   '\n'.join(os.listdir(
                                       os.path.join(pywikibot_dir,
                                                    "pywikibot",
                                                    "families"))))
        fam = listchoice(known_families,
                         "Select family of sites we are working on",
                         default='wikipedia')
        mylang = raw_input(
"The language code of the site we're working on (default: 'en'): ") or 'en'
        username = raw_input("Username (%s %s): "
                             % (mylang, fam)) or 'UnnamedBot'
        username = unicode(username, console_encoding)
        while True:
            choice = raw_input(
"Which variant of user_config.py:\n[S]mall or [E]xtended (with further information)? "
                               ).upper()
            if choice in "SE":
                break

        #
        # I don't like this solution. Temporary for me.
        #
        # determine what directory this script (generate_user_files.py) lives in
        install = os.path.dirname(os.path.abspath(sys.argv[0]))
        # config2.py will be in the pywikibot/ directory
        f = codecs.open(os.path.join(install, "pywikibot", "config2.py"),
                        "r", "utf-8")
        cpy = f.read()
        f.close()

        res = re.findall("^(############## (?:LOGFILE|"
                                            "INTERWIKI|"
                                            "SOLVE_DISAMBIGUATION|"
                                            "IMAGE RELATED|"
                                            "TABLE CONVERSION BOT|"
                                            "WEBLINK CHECKER|"
                                            "DATABASE|"
                                            "SEARCH ENGINE|"
                                            "COPYRIGHT|"
                                            "FURTHER) SETTINGS .*?)^(?=#####|# =====)",
                         cpy, re.MULTILINE | re.DOTALL)
        config_text = '\n'.join(res)

        f = codecs.open(_fnc, "w", "utf-8")
        if choice == 'E':
            f.write("""# -*- coding: utf-8  -*-

# This is an automatically generated file. You can find more configuration
# parameters in 'config.py' file.

# The family of sites we are working on. wikipedia.py will import
# families/xxx_family.py so if you want to change this variable,
# you need to write such a file.
family = '%s'

# The language code of the site we're working on.
mylang = '%s'

# The dictionary usernames should contain a username for each site where you
# have a bot account.
usernames['%s']['%s'] = u'%s'


%s""" % (fam, mylang, fam, mylang, username, config_text))
        else:
            f.write("""# -*- coding: utf-8  -*-
family = '%s'
mylang = '%s'
usernames['%s']['%s'] = u'%s'
""" % (fam, mylang, fam, mylang, username))
        f.close()
        print("'%s' written." % _fnc)

def create_user_fixes():
    _fnf = os.path.join(base_dir, "user-fixes.py")
    if not file_exists(_fnf):
        f = codecs.open(_fnf, "w", "utf-8")
        f.write(r"""# -*- coding: utf-8  -*-

#
# This is only an example. Don't use it.
#

fixes['example'] = {
    'regex': True,
    'msg': {
        '_default':u'no summary specified',
    },
    'replacements': [
        (ur'\bword\b', u'two words'),
    ]
}

""")
        f.close()
        print("'%s' written." % _fnf)

if __name__ == "__main__":
    while True:
        print('\nYour default user directory is "%s"' % base_dir)
        ok = raw_input("How to proceed? ([K]eep [c]hange) ").upper().strip()
        if (not ok) or "KEEP".startswith(ok):
            break
        if "CHANGE".startswith(ok):
            if change_base_dir():
                break
    while True:
        if os.path.exists(os.path.join(base_dir, "user-config.py")):
            break
        do_copy = raw_input(
"Do you want to copy user files from an existing pywikipedia installation? "
                            ).upper().strip()
        if do_copy and "YES".startswith(do_copy):
            oldpath = raw_input("Path to existing wikipedia.py? ")
            if not os.path.exists(oldpath):
                print("ERROR: Not a valid path")
                continue
            if os.path.isfile(oldpath):
                # User probably typed /wikipedia.py at the end, so strip it
                oldpath = os.path.dirname(oldpath)
            if not os.path.isfile(os.path.join(oldpath, "user-config.py")):
                print("ERROR: no user_config.py found in that directory")
                continue
            newf = file(os.path.join(base_dir, "user-config.py"), "wb")
            oldf = file(os.path.join(oldpath, "user-config.py"), "rb")
            newf.write(oldf.read())
            newf.close(); oldf.close()
            if os.path.isfile(os.path.join(oldpath, "user-fixes.py")):
                newfix = file(os.path.join(base_dir, "user-fixes.py"), "wb")
                oldfix = file(os.path.join(oldpath, "user-fixes.py"), "rb")
                newfix.write(oldfix.read())
                newfix.close() ; oldfix.close()
        elif do_copy and "NO".startswith(do_copy):
            break
    if not os.path.isfile(os.path.join(base_dir, "user-config.py")):
        a = raw_input("Create user-config.py file? ([y]es, [N]o) ")
        if a[:1] in ["Y", "y"]:
            create_user_config()
    else:
        print("NOTE: user-config.py already exists in the directory")
    if not os.path.isfile(os.path.join(base_dir, "user-fixes.py")):
        a = raw_input("Create user-fixes.py file? ([y]es, [N]o) ")
        if a[:1] in ["Y", "y"]:
            create_user_fixes()
    else:
        print("NOTE: user-fixes.py already exists in the directory")
