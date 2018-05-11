"""Copyright (C) 2018 Robert Ancell

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version. See http://www.gnu.org/copyleft/gpl.html the full text of the
license."""

# ＰｒＩＤＥ

import curses
import selectors
import unicodedata

from pride import ui

class PythonLogo (ui.Widget):
    def __init__ (self, background = '#FFFFFF'):
        ui.Widget.__init__ (self)
        self.background = background

    def get_size (self):
        return (23, 6)

    def render (self, frame):
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

class HelpWindow (ui.Box):
    def __init__ (self):
        ui.Box.__init__ (self, style = ui.BoxStyle.WIDE, foreground = '#0000FF', background = '#FFFFFF')
        python_logo = PythonLogo ()
        self.set_child (python_logo)

class Editor (ui.Grid):
    def __init__ (self):
        ui.Grid.__init__ (self)
        self.buffer = ui.TextBuffer ()
        self.view = ui.TextView (self.buffer)
        self.append_column (self.view)
        self.scroll = ui.Scroll ()
        self.append_column (self.scroll)
        self.focus (self.view)

    def render (self, frame):
        # FIXME: Do this not every frame but only when the view changes
        # FIXME: Hide scrollbar when less than one page
        n_lines = len (self.buffer.lines)
        start = self.view.start_line / n_lines
        end = (self.view.start_line + frame.height) / n_lines
        self.scroll.set_position (start, end)
        ui.Grid.render (self, frame)

class PrideDisplay (ui.Display):
    def __init__ (self, app, selector, screen):
        ui.Display.__init__ (self, selector, screen)
        self.app = app

    def handle_event (self, event):
        open ('debug.log', 'a').write ('EVENT {}\n'.format (event))
        if isinstance (event, ui.KeyInputEvent):
            if event.key == ui.Key.F1:
                self.app.help_window.visible = not self.app.help_window.visible
                if self.app.help_window.visible:
                    self.app.stack.raise_child (self.app.help_window)
                return
            elif event.key == ui.Key.F4: # FIXME: Handle in self.app.main_list.handle_event
                if self.app.main_list.focus_child == self.app.editor:
                    self.app.main_list.focus (self.app.console)
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
        self.selector = selectors.DefaultSelector ()
        self.display = PrideDisplay (self, self.selector, screen)
        self.fullscreen = False

        self.stack = ui.Stack ()
        self.display.set_child (self.stack)

        self.main_list = ui.Grid ()
        self.stack.add_child (self.main_list)

        self.editor_tabs = ui.Tabs ()
        self.editor_tabs.add_child (unicodedata.lookup ('PAGE FACING UP') + ' ')
        self.editor_tabs.add_child ('main.py')
        self.editor_tabs.add_child ('README.md')
        self.editor_tabs.add_child ('code.txt')
        self.main_list.append_row (self.editor_tabs)

        self.editor = Editor ()
        self.main_list.append_row (self.editor)

        self.console_bar = ui.Bar (unicodedata.lookup ('SNAKE') + ' Python')
        self.console = ui.Console (self.selector)
        self.main_list.append_row (self.console_bar)
        self.main_list.append_row (self.console)

        self.main_list.focus (self.editor)

        self.help_window = HelpWindow ()
        self.help_window.visible = False
        self.stack.add_child (self.help_window)

        self.emoji_dialog = ui.EmojiDialog ()
        self.emoji_dialog.visible = False
        self.emoji_dialog.select_character = self.select_emoji
        self.stack.add_child (self.emoji_dialog)

    def select_emoji (self, character):
        self.editor.view.insert (character)
        self.emoji_dialog.visible = False

    def run (self):
        try:
            for line in open ('main.py').read ().split ('\n'):
                self.editor.buffer.lines.append (line)
        except:
            pass
        self.console.run (['python3', '-q'])
        self.display.refresh ()

        while True:
            events = self.selector.select ()
            for key, mask in events:
                self.display.handle_selector_event (key, mask)
                self.console.handle_selector_event (key, mask)
            self.display.refresh ()

    def run_program (self):
        f = open ('main.py', 'w')
        f.write ('\n'.join (self.editor.buffer.lines))
        f.close ()
        self.console.run (['python3', 'main.py'])

    def update_visibility (self):
        focus_child = self.main_list.focus_child
        self.editor_tabs.visible = not self.fullscreen or focus_child is self.editor
        self.editor.visible = not self.fullscreen or focus_child is self.editor
        self.console_bar.visible = not self.fullscreen or focus_child is self.console
        self.console.visible = not self.fullscreen or focus_child is self.console
