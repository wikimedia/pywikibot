
__version__ = '$Id$'

import sys; sys.path.append('..')

import re
import terminal_interface
import wx

app = wx.App()

class UI(terminal_interface.UI):
    def __init__(self):
        pass
    
    def input(self, question, password = False):
        """
        Works like raw_input(), but returns a unicode string instead of ASCII.

        Unlike raw_input, this function automatically adds a space after the
        question.
        """
        # TODO: hide input if password = True
        
        self.output(question)
        if password:
            answer = wx.PasswordEntryDialog( None, question, '','')
        else:
            answer = wx.TextEntryDialog( None, question, '', '' )
        answer.ShowModal()
        self.output(answer+'\n')
        #tkSimpleDialog.askstring('title', question)
        return answer.GetValue() or ''

    def inputChoice(self, question, options, hotkeys, default = None):
        for i in range(len(options)):
            option = options[i]
            hotkey = hotkeys[i]
            m = re.search('[%s%s]' % (hotkey.lower(), hotkey.upper()), option)
            if m:
                pos = m.start()
                options[i] = '%s[%s]%s' % (option[:pos], option[pos], option[pos+1:])
            else:
                options[i] = '%s [%s]' % (option, hotkey)
        
        while True:
            prompt = '%s\n(%s)' % (question, ', '.join(options))
            self.output('%s (%s)' % (question, ', '.join(options)))
            answer = wx.TextEntryDialog(None, prompt, question, '')
            answer.ShowModal()
            answer = answer.GetValue()
            self.output(answer+'\n')
            
            if answer.lower() in hotkeys or answer.upper() in hotkeys:
                return answer
            elif default and answer=='':# empty string entered
                return default

if __name__ == '__main__':
    ui = UI()
    print ui.input('Test?')

app.MainLoop()

