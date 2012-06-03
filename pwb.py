import sys,os
sys.path.append('.')
sys.path.append('externals/httplib2')
sys.path.append('pywikibot/compat')

if "PYWIKIBOT2_DIR" not in os.environ:
    os.environ["PYWIKIBOT2_DIR"] = os.path.split(__file__)[0]

sys.argv.pop(0)
if len(sys.argv) > 0:
    if not os.path.exists(sys.argv[0]):
        testpath = os.path.join(os.path.split(__file__)[0], 'scripts', sys.argv[0])
        if os.path.exists(testpath):
            sys.argv[0] = testpath
        else:
            testpath = testpath + '.py'
            if os.path.exists(testpath):
                sys.argv[0] = testpath
            else:
                raise Exception("%s not found!" % sys.argv[0]) 
    sys.path.append(os.path.split(sys.argv[0])[0])
    execfile(sys.argv[0])
else:
    sys.argv.append('')
