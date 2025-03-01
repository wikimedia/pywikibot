"""A window with a textfield where the user can edit.

Useful for editing the contents of an article.

.. note:: idlelib, tkinter and pillow modules are required.

.. warning::
   With Pillow 10.0, 10.1 no wheels for 32-bit Python on Windows are
   supported. Pillow 10.2 supports it again. Either you have to update
   your Python using a 64-bit version or you have to
   :command:`pip install "pillow>8.1.1,!=10.0,!=10.1"`.

.. seealso:: :mod:`editor`
"""
#
# (C) Pywikibot team, 2003-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import pywikibot


# Some Python distributions have tkinter but the underlying _tkinter
# implementation is missing. Thus just import tkinter does not raise
# the exception. Therefore try to import _tkinter.
# Note: idlelib also needs tkinter.
try:
    import _tkinter  # noqa: F401
except ImportError as e:
    idlelib = tkinter = e
    Frame = simpledialog = ScrolledText = object
    ConfigDialog = ReplaceDialog = SearchDialog = object
    idleConf = MultiCallCreator = object  # noqa:  N816
else:
    import idlelib
    import tkinter
    from idlelib import replace as ReplaceDialog  # noqa: N812
    from idlelib import search as SearchDialog  # noqa: N812
    from idlelib.config import idleConf
    from idlelib.configdialog import ConfigDialog
    from idlelib.multicall import MultiCallCreator
    from tkinter import Frame, simpledialog
    from tkinter.scrolledtext import ScrolledText


__all__ = ('EditBoxWindow', 'TextEditor', 'Tkdialog')


class TextEditor(ScrolledText):

    """A text widget with some editing enhancements.

    A lot of code here is copied or adapted from the
    idlelib/EditorWindow.py file in the standard Python distribution.
    """

    def __init__(self, master=None, **kwargs) -> None:
        """Initializer.

        Get default settings from user's IDLE configuration.
        """
        for module in (idlelib, tkinter):
            if isinstance(module, ImportError):
                raise module

        textcf = self._initialize_config(idleConf.CurrentTheme())

        if idleConf.GetOption('main', 'EditorWindow', 'font-bold',
                              type='bool'):
            font_weight = 'bold'
        else:
            font_weight = 'normal'
        textcf['font'] = (
            idleConf.GetOption('main', 'EditorWindow', 'font'),
            idleConf.GetOption('main', 'EditorWindow', 'font-size'),
            font_weight)

        # override defaults with any user-specified settings
        textcf.update(kwargs)
        super().__init__(master, **textcf)

    @staticmethod
    def _initialize_config(theme):
        """Fix idleConf.GetHighlight method for different Python releases."""
        config = {
            'padx': 5,
            'wrap': 'word',
            'undo': 'True',
            'width': idleConf.GetOption('main', 'EditorWindow', 'width'),
            'height': idleConf.GetOption('main', 'EditorWindow', 'height'),
        }

        config['foreground'] = idleConf.GetHighlight(
            theme, 'normal')['foreground']
        config['background'] = idleConf.GetHighlight(
            theme, 'normal')['background']
        config['highlightcolor'] = idleConf.GetHighlight(
            theme, 'hilite')['foreground']
        config['highlightbackground'] = idleConf.GetHighlight(
            theme, 'hilite')['background']
        config['insertbackground'] = idleConf.GetHighlight(
            theme, 'cursor')['foreground']
        return config

    def add_bindings(self) -> None:
        """Assign key and events bindings to methods."""
        # due to IDLE dependencies, this can't be called from __init__
        # add key and event bindings
        self.bind('<<cut>>', self.cut)
        self.bind('<<copy>>', self.copy)
        self.bind('<<paste>>', self.paste)
        self.bind('<<select-all>>', self.select_all)
        self.bind('<<remove-selection>>', self.remove_selection)
        self.bind('<<find>>', self.find_event)
        self.bind('<<find-again>>', self.find_again_event)
        self.bind('<<find-selection>>', self.find_selection_event)
        self.bind('<<replace>>', self.replace_event)
        self.bind('<<goto-line>>', self.goto_line_event)
        self.bind('<<del-word-left>>', self.del_word_left)
        self.bind('<<del-word-right>>', self.del_word_right)
        keydefs = {'<<copy>>': ['<Control-Key-c>', '<Control-Key-C>'],
                   '<<cut>>': ['<Control-Key-x>', '<Control-Key-X>'],
                   '<<del-word-left>>': ['<Control-Key-BackSpace>'],
                   '<<del-word-right>>': ['<Control-Key-Delete>'],
                   '<<end-of-file>>': ['<Control-Key-d>', '<Control-Key-D>'],
                   '<<find-again>>': ['<Control-Key-g>', '<Key-F3>'],
                   '<<find-selection>>': ['<Control-Key-F3>'],
                   '<<find>>': ['<Control-Key-f>', '<Control-Key-F>'],
                   '<<goto-line>>': ['<Alt-Key-g>', '<Meta-Key-g>'],
                   '<<paste>>': ['<Control-Key-v>', '<Control-Key-V>'],
                   '<<redo>>': ['<Control-Shift-Key-Z>'],
                   '<<remove-selection>>': ['<Key-Escape>'],
                   '<<replace>>': ['<Control-Key-h>', '<Control-Key-H>'],
                   '<<select-all>>': ['<Control-Key-a>'],
                   '<<undo>>': ['<Control-Key-z>', '<Control-Key-Z>'],
                   }

        for event, keylist in keydefs.items():
            if keylist:
                self.event_add(event, *keylist)

    def cut(self, event) -> str:
        """Perform cut operation."""
        if self.tag_ranges('sel'):
            self.event_generate('<<Cut>>')
        return 'break'

    def copy(self, event) -> str:
        """Perform copy operation."""
        if self.tag_ranges('sel'):
            self.event_generate('<<Copy>>')
        return 'break'

    def paste(self, event) -> str:
        """Perform paste operation."""
        self.event_generate('<<Paste>>')
        return 'break'

    def select_all(self, event=None) -> str:
        """Perform select all operation."""
        self.tag_add('sel', '1.0', 'end-1c')
        self.mark_set('insert', '1.0')
        self.see('insert')
        return 'break'

    def remove_selection(self, event=None) -> None:
        """Perform remove operation."""
        self.tag_remove('sel', '1.0', 'end')
        self.see('insert')

    def del_word_left(self, event) -> str:
        """Perform delete word (left) operation."""
        self.event_generate('<Meta-Delete>')
        return 'break'

    def del_word_right(self, event=None) -> str:
        """Perform delete word (right) operation."""
        self.event_generate('<Meta-d>')
        return 'break'

    def find_event(self, event=None) -> str:
        """Perform find operation."""
        if not self.tag_ranges('sel'):
            found = self.tag_ranges('found')
            if found:
                self.tag_add('sel', found[0], found[1])
            else:
                self.tag_add('sel', '1.0', '1.0+1c')
        SearchDialog.find(self)
        return 'break'

    def find_again_event(self, event=None) -> str:
        """Perform find again operation."""
        SearchDialog.find_again(self)
        return 'break'

    def find_selection_event(self, event=None) -> str:
        """Perform find selection operation."""
        SearchDialog.find_selection(self)
        return 'break'

    def replace_event(self, event=None) -> str:
        """Perform replace operation."""
        ReplaceDialog.replace(self)
        return 'break'

    def find_all(self, s):
        """Highlight all occurrences of string s, and select the first one.

        If the string has already been highlighted, jump to the next occurrence
        after the current selection. (You cannot go backwards using the
        button, but you can manually place the cursor anywhere in the
        document to start searching from that point.)

        """
        if hasattr(self, '_highlight') and self._highlight == s:
            try:
                if self.get(tkinter.SEL_FIRST, tkinter.SEL_LAST) == s:
                    return self.find_selection_event(None)
                # user must have changed the selection
                found = self.tag_nextrange('found', tkinter.SEL_LAST)
            except tkinter.TclError:
                # user must have unset the selection
                found = self.tag_nextrange('found', tkinter.INSERT)
            if not found:
                # at last occurrence, scroll back to the top
                found = self.tag_nextrange('found', 1.0)
            if found:
                self.do_highlight(found[0], found[1])
        else:
            # find all occurrences of string s;
            # adapted from O'Reilly's Python in a Nutshell
            # remove previous uses of tag 'found', if any
            self.tag_remove('found', '1.0', tkinter.END)
            if s:
                self._highlight = s
                # start from the beginning (and when we come to the end, stop)
                idx = '1.0'
                while True:
                    # find next occurrence, exit loop if no more
                    idx = self.search(s, idx, nocase=1, stopindex=tkinter.END)
                    if not idx:
                        break
                    # index right after the end of the occurrence
                    lastidx = f'{idx}+{len(s)}c'
                    # tag the whole occurrence (start included, stop excluded)
                    self.tag_add('found', idx, lastidx)
                    # prepare to search for next occurrence
                    idx = lastidx
                # use a red foreground for all the tagged occurrences
                self.tag_config('found', foreground='red')
                found = self.tag_nextrange('found', 1.0)
                if found:
                    self.do_highlight(found[0], found[1])
        return None

    def do_highlight(self, start, end) -> None:
        """Select and show the text from index start to index end."""
        self.see(start)
        self.tag_remove(tkinter.SEL, '1.0', tkinter.END)
        self.tag_add(tkinter.SEL, start, end)
        self.focus_set()

    def goto_line_event(self, event):
        """Perform goto line operation."""
        lineno = simpledialog.askinteger('Goto', 'Go to line number:',
                                         parent=self)
        if lineno is None:
            return 'break'
        if lineno <= 0:
            self.bell()
            return 'break'
        self.mark_set('insert', f'{lineno}.0')
        self.see('insert')
        return None


class EditBoxWindow(Frame):

    """Edit box window."""

    def __init__(self, parent=None, **kwargs) -> None:
        """Initializer."""
        for module in (idlelib, tkinter):
            if isinstance(module, ImportError):
                raise module

        if parent is None:
            # create a new window
            parent = tkinter.Tk()
        self.parent = parent
        super().__init__(parent)
        self.editbox = MultiCallCreator(TextEditor)(self, **kwargs)
        self.editbox.pack(side=tkinter.TOP)
        self.editbox.add_bindings()
        self.bind('<<open-config-dialog>>', self.config_dialog)

        bottom = tkinter.Frame(parent)
        # lower left subframe with a textfield and a Search button
        bottom_left_frame = tkinter.Frame(bottom)
        self.textfield = tkinter.Entry(bottom_left_frame)
        self.textfield.pack(side=tkinter.LEFT, fill=tkinter.X, expand=1)

        button_search = tkinter.Button(bottom_left_frame, text='Find next',
                                       command=self.find)
        button_search.pack(side=tkinter.RIGHT)
        bottom_left_frame.pack(side=tkinter.LEFT, expand=1)

        # lower right subframe which will contain OK and Cancel buttons
        bottom_right_frame = tkinter.Frame(bottom)

        button_ok = tkinter.Button(bottom_right_frame, text='OK',
                                   command=self.pressedOK)
        button_cancel = tkinter.Button(bottom_right_frame, text='Cancel',
                                       command=parent.destroy)
        button_ok.pack(side=tkinter.LEFT, fill=tkinter.X)
        button_cancel.pack(side=tkinter.RIGHT, fill=tkinter.X)
        bottom_right_frame.pack(side=tkinter.RIGHT, expand=1)

        bottom.pack(side=tkinter.TOP)

        # create a toplevel menu
        menubar = tkinter.Menu(self.parent)

        findmenu = tkinter.Menu(menubar)
        findmenu.add_command(label='Find',
                             command=self.editbox.find_event,
                             accelerator='Ctrl+F',
                             underline=0)
        findmenu.add_command(label='Find again',
                             command=self.editbox.find_again_event,
                             accelerator='Ctrl+G',
                             underline=6)
        findmenu.add_command(label='Find all',
                             command=self.find_all,
                             underline=5)
        findmenu.add_command(label='Find selection',
                             command=self.editbox.find_selection_event,
                             accelerator='Ctrl+F3',
                             underline=5)
        findmenu.add_command(label='Replace',
                             command=self.editbox.replace_event,
                             accelerator='Ctrl+H',
                             underline=0)
        menubar.add_cascade(label='Find', menu=findmenu, underline=0)

        editmenu = tkinter.Menu(menubar)
        editmenu.add_command(label='Cut',
                             command=self.editbox.cut,
                             accelerator='Ctrl+X',
                             underline=2)
        editmenu.add_command(label='Copy',
                             command=self.editbox.copy,
                             accelerator='Ctrl+C',
                             underline=0)
        editmenu.add_command(label='Paste',
                             command=self.editbox.paste,
                             accelerator='Ctrl+V',
                             underline=0)
        editmenu.add_separator()
        editmenu.add_command(label='Select all',
                             command=self.editbox.select_all,
                             accelerator='Ctrl+A',
                             underline=7)
        editmenu.add_command(label='Clear selection',
                             command=self.editbox.remove_selection,
                             accelerator='Esc')
        menubar.add_cascade(label='Edit', menu=editmenu, underline=0)

        optmenu = tkinter.Menu(menubar)
        optmenu.add_command(label='Settings...',
                            command=self.config_dialog,
                            underline=0)
        menubar.add_cascade(label='Options', menu=optmenu, underline=0)

        # display the menu
        self.parent.config(menu=menubar)
        self.pack()

    def edit(self, text: str, jumpIndex: int | None = None,  # noqa: N803
             highlight: str | None = None) -> str | None:
        """Provide user with editor to modify text.

        :param text: the text to be edited
        :param jumpIndex: position at which to put the caret
        :param highlight: each occurrence of this substring will be highlighted
        :return: the modified text, or None if the user didn't save the text
            file in his text editor
        """
        self.text = None
        # put given text into our textarea
        self.editbox.insert(tkinter.END, text)
        # wait for user to push a button which will destroy (close) the window
        # enable word wrap
        self.editbox.tag_add('all', '1.0', tkinter.END)
        self.editbox.tag_config('all', wrap=tkinter.WORD)
        # start search if required
        if highlight:
            self.find_all(highlight)
        if jumpIndex:
            # lines are indexed starting at 1
            line = text[:jumpIndex].count('\n') + 1
            column = jumpIndex - (text[:jumpIndex].rfind('\n') + 1)
            # don't know how to place the caret, but scrolling to the right
            # line should already be helpful.
            self.editbox.see(f'{line}.{column}')
        # wait for user to push a button which will destroy (close) the window
        self.parent.mainloop()
        return self.text

    def find_all(self, target) -> None:
        """Perform find all operation."""
        self.textfield.insert(tkinter.END, target)
        self.editbox.find_all(target)

    def find(self) -> None:
        """Perform find operation."""
        # get text to search for
        s = self.textfield.get()
        if s:
            self.editbox.find_all(s)

    def config_dialog(self, event=None) -> None:
        """Show config dialog."""
        ConfigDialog(self, 'Settings')

    def pressedOK(self) -> None:  # noqa: N802
        """Perform OK operation.

        Called when user pushes the OK button.
        Saves the buffer into a variable, and closes the window.
        """
        self.text = self.editbox.get('1.0', tkinter.END)
        self.parent.destroy()

    def debug(self, event=None) -> str:
        """Call quit() and return 'break'."""
        self.quit()
        return 'break'


class Tkdialog:

    """The dialog window for image info."""

    def __init__(self, photo_description, photo, filename) -> None:
        """Initializer."""
        for module in (idlelib, tkinter):
            if isinstance(module, ImportError):
                raise module

        self.root = tkinter.Tk()
        # "%dx%d%+d%+d" % (width, height, xoffset, yoffset)
        self.root.geometry(f'{int(pywikibot.config.tkhorsize)}x'
                           f'{int(pywikibot.config.tkvertsize)}+10-10')

        self.root.title(filename)
        self.photo_description = photo_description
        self.filename = filename
        self.photo = photo
        self.skip = False
        self.exit = False

        # --Init of the widgets
        # The image
        self.image = self.get_image(self.photo, 800, 600)
        self.image_panel = tkinter.Label(self.root, image=self.image)

        self.image_panel.image = self.image

        # The filename
        self.filename_label = tkinter.Label(self.root,
                                            text='Suggested filename')
        self.filename_field = tkinter.Entry(self.root, width=100)
        self.filename_field.insert(tkinter.END, filename)

        # The description
        self.description_label = tkinter.Label(self.root,
                                               text='Suggested description')
        self.description_scrollbar = tkinter.Scrollbar(self.root,
                                                       orient=tkinter.VERTICAL)
        self.description_field = tkinter.Text(self.root)
        self.description_field.insert(tkinter.END, photo_description)
        self.description_field.config(
            state=tkinter.NORMAL, height=12, width=100, padx=0, pady=0,
            wrap=tkinter.WORD, yscrollcommand=self.description_scrollbar.set)
        self.description_scrollbar.config(command=self.description_field.yview)

        # The buttons
        self.ok_button = tkinter.Button(self.root, text='OK',
                                        command=self.ok_file)
        self.skip_button = tkinter.Button(self.root, text='Skip',
                                          command=self.skip_file)

        # --Start grid

        # The image
        self.image_panel.grid(row=0, column=0, rowspan=11, columnspan=4)

        # The buttons
        self.ok_button.grid(row=11, column=1, rowspan=2)
        self.skip_button.grid(row=11, column=2, rowspan=2)

        # The filename
        self.filename_label.grid(row=13, column=0)
        self.filename_field.grid(row=13, column=1, columnspan=3)

        # The description
        self.description_label.grid(row=14, column=0)
        self.description_field.grid(row=14, column=1, columnspan=3)
        self.description_scrollbar.grid(row=14, column=5)

    @staticmethod
    def get_image(photo, width, height):
        """Take the BytesIO object and build an imageTK thumbnail."""
        try:
            from PIL import Image, ImageTk
        except ImportError:
            pywikibot.warning('This script requires ImageTk from the'
                              'Python Imaging Library (PIL).')
            raise

        image = Image.open(photo)
        image.thumbnail((width, height))
        return ImageTk.PhotoImage(image)

    def ok_file(self) -> None:
        """The user pressed the OK button."""
        self.filename = self.filename_field.get()
        self.photo_description = self.description_field.get(0.0, tkinter.END)
        self.root.destroy()

    def skip_file(self) -> None:
        """The user pressed the Skip button."""
        self.skip = True
        self.root.destroy()

    def show_dialog(self) -> tuple[str, str, bool]:
        """Activate the dialog.

        :return: new description, name, and if the image is skipped
        """
        self.root.mainloop()
        return self.photo_description, self.filename, self.skip
