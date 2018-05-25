"""Copyright (C) 2018 Robert Ancell

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version. See http://www.gnu.org/copyleft/gpl.html the full text of the
license."""

# ＰｒＩＤＥ

import asyncio
import curses
import unicodedata
import pathlib

from pride import ui

class PythonLogo (ui.Widget):
    def __init__ (self, background = '#FFFFFF'):
        ui.Widget.__init__ (self)
        self.background = background

    def get_size (self):
        return (23, 6)

    def render (self, frame, theme):
        lines  = [ '▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄',
                   '   ▟•█▙       ╷╷       ',
                   ' ▟█▇▇█▛█▙ ╭╮╷╷┼├╮╭╮┌╮™ ',
                   ' ▜█▟█▁▁█▛ ├╯╰┤╵╵╵╰╯╵╵  ',
                   '   ▜█•▛   ╵ ╶╯         ',
                   '▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀' ]
        colors = [ '=======================',
                   '---BEBB----------------',
                   '-BBBBBbYY--------------',
                   '-BByYxxYY--------------',
                   '---YYeY----------------',
                   '=======================' ]
        color_codes = {'=': ('#FFFFFF', self.background),
                       '-': ('#000000', '#FFFFFF'),
                       'B': ('#0000FF', '#FFFFFF'),
                       'b': ('#0000FF', '#FFFF00'),
                       'E': ('#FFFFFF', '#0000FF'),
                       'Y': ('#FFFF00', '#FFFFFF'),
                       'y': ('#FFFF00', '#0000FF'),
                       'x': ('#FFFFFF', '#FFFF00'),
                       'e': ('#FFFFFF', '#FFFF00')}

        frame.render_image (0, 0, lines, colors, color_codes)

class HelpDialog (ui.Box):
    def __init__ (self):
        ui.Box.__init__ (self, style = ui.BoxStyle.WIDE, background = '#FFFFFF')

        grid = ui.Grid ()
        self.set_child (grid)

        label = ui.Label ('PRIDE - The Python Remote IDE\n', '#000000')
        grid.append_row (label)

        label = ui.Label ('F1 - Help screen', '#000000')
        grid.append_row (label)
        label = ui.Label ('F2 - Menu', '#000000')
        grid.append_row (label)
        label = ui.Label ('F3 - Next file', '#000000')
        grid.append_row (label)
        label = ui.Label ('F4 - Switch between editor and Python', '#000000')
        grid.append_row (label)
        label = ui.Label ('F5 - Run file', '#000000')
        grid.append_row (label)
        label = ui.Label ('Insert - Insert Emoji', '#000000')
        grid.append_row (label)

        python_logo = PythonLogo ()
        grid.append_row (python_logo)

class FileDialog (ui.Box):
    def __init__ (self, callback = None):
        ui.Box.__init__ (self, style = ui.BoxStyle.WIDE, background = '#FFFFFF')
        self.callback = callback

        grid = ui.Grid ()
        self.set_child (grid)

        label = ui.Label ('Select file to open', '#000000')
        grid.append_row (label)

        model = ui.FileModel ()
        files = ui.TreeView (model, self._file_selected, text_color = '#000000')
        grid.append_row (files)
        grid.focus (files)

    def _file_selected (self, item):
        self.callback (item)

class FileView (ui.Grid):
    def __init__ (self, path):
        ui.Grid.__init__ (self)

        self.path = path

        self.buffer = ui.TextBuffer (changed_callback = self._file_changed)
        self.save_handle = None
        self.view = ui.TextView (self.buffer)
        self.append_column (self.view)
        self.scroll = ui.Scroll ()
        self.append_column (self.scroll)

        self.focus (self.view)

        try:
            for line in open (path).read ().split ('\n'):
                self.buffer.lines.append (line)
        except:
            pass

    def save (self):
        f = open (self.path, 'w')
        f.write ('\n'.join (self.buffer.lines))
        f.close ()

    def _file_changed (self):
        loop = asyncio.get_event_loop ()
        if self.save_handle is not None:
            self.save_handle.cancel ()
        self.save_handle = loop.call_later (1.0, self._save_file)

    def _save_file (self):
        self.save_handle = None
        self.save ()

    def render (self, frame, theme):
        # FIXME: Do this not every frame but only when the view changes
        # FIXME: Hide scrollbar when less than one page
        n_lines = len (self.buffer.lines)
        if n_lines > 0:
            start = self.view.start_line / n_lines
            end = (self.view.start_line + frame.height) / n_lines
        else:
            start = 0
            end = frame.height
        self.scroll.set_position (start, end)
        ui.Grid.render (self, frame, theme)

class Editor (ui.Grid):
    def __init__ (self):
        ui.Grid.__init__ (self)

        tab_grid = ui.Grid ()
        tab_grid.set_scale (1.0, 0.0)
        self.append_row (tab_grid)

        tab_grid.append_column (ui.Label (unicodedata.lookup ('PAGE FACING UP') + '  ', background = '#0000FF'))

        self.tabs = ui.Tabs ()
        tab_grid.append_column (self.tabs)

        self.file_stack = ui.Stack ()
        self.append_row (self.file_stack)

        self.file_views = []
        self.selected = 0
        self.focus (self.file_stack)

    def _find_file (self, path):
        for (i, file_view) in enumerate (self.file_views):
            if file_view.path == path:
                return (i, file_view)
        return (-1, None)

    def new_file (self):
        i = 0
        filename = 'untitled'
        while True:
            path = pathlib.Path (filename)
            if not path.exists ():
                path.touch ()
                self.load_file (filename)
                return filename
            i += 1
            filename = 'untitled{}'.format (i)

    def load_file (self, path):
        (_, file_view) = self._find_file (path)
        if file_view is not None:
            return
        file_view = FileView (path)
        self.file_stack.add_child (file_view)
        self.file_views.append (file_view)
        self.tabs.add_child (path)

    def select_file (self, path):
        (i, file_view) = self._find_file (path)
        if file_view is None:
            return
        self.selected = i
        self.tabs.set_selected (i)
        self.file_stack.raise_child (file_view)

    def insert (self, text):
        self.file_views[self.selected].view.insert (text)

    def next_file (self):
        self.selected += 1
        if self.selected >= len (self.file_views):
            self.selected = 0
        self.file_stack.raise_child (self.file_views[self.selected])
        self.tabs.set_selected (self.selected)

    def save_file (self):
        self.file_views[self.selected].save ()

    def get_path (self):
        return self.file_views[self.selected].path

class PythonConsole (ui.Grid):
    def __init__ (self, changed_callback = None):
        ui.Grid.__init__ (self)
        console_bar = ui.Bar (unicodedata.lookup ('SNAKE') + ' Python')
        self.append_row (console_bar)
        self.console = ui.Console (changed_callback = changed_callback)
        self.append_row (self.console)
        self.focus (self.console)

    def run (self, program = None):
        if program is None:
            self.console.run (['python3', '-q'])
        else:
            self.console.run (['python3', program])

class PrideDisplay (ui.Display):
    def __init__ (self, app, screen):
        ui.Display.__init__ (self, screen)
        self.app = app

    def handle_event (self, event):
        open ('debug.log', 'a').write ('EVENT {}\n'.format (event))
        if isinstance (event, ui.KeyInputEvent):
            if event.key == ui.Key.F1:
                self.app.help_dialog.visible = not self.app.help_dialog.visible
                if self.app.help_dialog.visible:
                    self.app.stack.raise_child (self.app.help_dialog)
                return
            elif event.key == ui.Key.CTRL_O:
                self.app.file_dialog.visible = not self.app.file_dialog.visible
                if self.app.file_dialog.visible:
                    self.app.stack.raise_child (self.app.file_dialog)
                return
            elif event.key == ui.Key.CTRL_N:
                path = self.app.editor.new_file ()
                self.app.editor.select_file (path)
                return
            elif event.key == ui.Key.F3:
                self.app.editor.next_file ()
                return
            elif event.key == ui.Key.F4: # FIXME: Handle in self.app.main_list.handle_event
                if self.app.main_list.focus_child == self.app.editor:
                    self.app.main_list.focus (self.app.python_console)
                else:
                    self.app.main_list.focus (self.app.editor)
                self.app.update_visibility ()
                return
            elif event.key == ui.Key.F5: # FIXME: Handle in self.app.main_list.handle_event
                self.app.run_program ()
                return
            elif event.key == ui.Key.F8: # F11?
                self.app.fullscreen = not self.app.fullscreen
                self.app.update_visibility ()
                return
            elif event.key == ui.Key.INSERT:
                self.app.emoji_dialog.visible = not self.app.emoji_dialog.visible
                self.app.stack.raise_child (self.app.emoji_dialog)
                return

        self.app.stack.handle_event (event)

class Pride:
    def __init__ (self, screen):
        self.display = PrideDisplay (self, screen)
        self.fullscreen = False

        self.stack = ui.Stack ()
        self.display.set_child (self.stack)

        self.main_list = ui.Grid ()
        self.stack.add_child (self.main_list)

        self.editor = Editor ()
        self.editor.load_file ('main.py')
        self.editor.load_file ('README.md')
        self.main_list.append_row (self.editor)

        def console_changed ():
            self.display.refresh ()
        self.python_console = PythonConsole (console_changed)
        self.main_list.append_row (self.python_console)

        self.main_list.focus (self.editor)

        self.help_dialog = HelpDialog ()
        self.help_dialog.visible = False
        self.stack.add_child (self.help_dialog)

        self.file_dialog = FileDialog (self._on_file_selected)
        self.file_dialog.visible = False
        self.file_dialog.set_scale (0.5, 0.5)
        self.stack.add_child (self.file_dialog)

        self.emoji_dialog = ui.EmojiDialog ()
        self.emoji_dialog.visible = False
        self.emoji_dialog.select_character = self.select_emoji
        self.emoji_dialog.set_scale (0.5, 0.5)
        self.stack.add_child (self.emoji_dialog)

    def _on_file_selected (self, path):
        self.file_dialog.visible = False
        self.editor.load_file (path)
        self.editor.select_file (path)

    def select_emoji (self, character):
        self.editor.insert (character)
        self.emoji_dialog.visible = False

    def run (self):
        self.python_console.run ()
        self.display.refresh ()

        loop = asyncio.get_event_loop ()
        try:
            loop.run_forever ()
        finally:
            loop.close ()

    def run_program (self):
        self.editor.save_file ()
        self.python_console.run (self.editor.get_path ())

    def update_visibility (self):
        focus_child = self.main_list.focus_child
        self.editor.visible = not self.fullscreen or focus_child is self.editor
        self.python_console.visible = not self.fullscreen or focus_child is self.python_console
