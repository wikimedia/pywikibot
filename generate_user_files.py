# -*- coding: utf-8  -*-
""" Script to create user files (user-config.py, user-fixes.py) """
__version__ = '$Id$'

import os, sys, codecs, re

base_dir = ''
console_encoding = sys.stdout.encoding

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

def file_exists(filename):
    if os.path.exists(filename):
        print("'%s' already exists." % filename)
        return True
    return False

def create_user_config():
    _fnc = os.path.join(base_dir, "user-config.py")
    if not file_exists(_fnc):
        know_families = re.findall(r'(.+)_family.py\b', '\n'.join(os.listdir(os.path.join(base_dir, "families"))))
        fam = listchoice(know_families, "Select family of sites we are working on", default = 'wikipedia')
        mylang = raw_input("The language code of the site we're working on (default: 'en'): ") or 'en'
        username = raw_input("Username (%s %s): " % (mylang, fam)) or 'UnnamedBot'
        username = unicode(username, console_encoding)
        while True:
            choice = raw_input("Which variant of user_config.py:\n[S]mall or [E]xtended (with further informations)? ").upper()
            if choice in ['S','E']:
                break

        #
        # I don't like this solution. Temporary for me.
        f = codecs.open("config.py", "r", "utf-8") ; cpy = f.read() ; f.close()

        res = re.findall("^(############## (?:LOGFILE|"
                                            "INTERWIKI|"
                                            "SOLVE_DISAMBIGUATION|"
                                            "IMAGE RELATED|"
                                            "TABLE CONVERSION BOT|"
                                            "WEBLINK CHECKER|"
                                            "DATABASE|"
                                            "SEARCH ENGINE|"
                                            "COPYRIGHT|"
                                            "FURTHER) SETTINGS .*?)^(?=#####|# =====)", cpy, re.MULTILINE | re.DOTALL)
        config_text = '\n'.join(res)

        f = codecs.open(_fnc, "w", "utf-8")
        if choice == 'E':
            f.write("""# -*- coding: utf-8  -*-

# This is an automatically generated file. You can find more configuration parameters in 'config.py' file.

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
    print("1: Create user_config.py file")
    print("2: Create user_fixes.py file")
    print("3: The two files")
    choice = raw_input("What do you do? ")
    if choice == "1":
        create_user_config()
    if choice == "2":
        create_user_fixes()
    if choice == "3":
        create_user_config()
        create_user_fixes()
    if not choice in ["1", "2", "3"]:
        print("Nothing to do")
