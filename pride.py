#!/usr/bin/python3

# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

# ＰｒＩＤＥ

import sys
import os
import curses
import selectors
import ui

class PythonLogo (ui.Widget):
    def get_size (self):
        return (6, 23)

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
        color_codes = {'=': ("#FFFFFF", "#000000"), # FIXME: Inherit from background
                       '-': ("#000000", "#FFFFFF"),
                       'B': ("#0000FF", "#FFFFFF"),
                       'b': ("#0000FF", "#FFFF00"),
                       'E': ("#FFFFFF", "#0000FF"),
                       'Y': ("#FFFF00", "#FFFFFF"),
                       'y': ("#FFFF00", "#0000FF"),
                       'x': ("#FFFFFF", "#FFFF00"),
                       'e': ("#FFFFFF", "#FFFF00")}

        frame.render_image (0, 0, lines, colors, color_codes)

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
                self.app.emoji_dialog.visible = True
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

        self.main_list = ui.List ()
        self.stack.add_child (self.main_list)

        self.editor_tabs = ui.Tabs ()
        self.editor_tabs.add_child ('main.py')
        self.editor_tabs.add_child ('README.md')
        self.editor_tabs.add_child ('code.txt')
        self.main_list.add_child (self.editor_tabs)

        self.buffer = ui.TextBuffer ()
        self.editor = ui.TextView (self.buffer)
        self.main_list.add_child (self.editor)

        self.console_bar = ui.Bar ('Python')
        self.console = ui.Console (self.selector)
        self.main_list.add_child (self.console_bar)
        self.main_list.add_child (self.console)

        self.main_list.focus (self.editor)

        self.help_window = ui.Box ()
        self.help_window.visible = False
        self.stack.add_child (self.help_window)

        python_logo = PythonLogo ()
        self.help_window.set_child (python_logo)

        self.emoji_dialog = ui.EmojiDialog ()
        self.emoji_dialog.visible = False
        self.stack.add_child (self.emoji_dialog)

    def run (self):
        try:
            for line in open ('main.py').read ().split ('\n'):
                self.buffer.lines.append (line)
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
        f.write ('\n'.join (self.buffer.lines))
        f.close ()
        self.console.run (['python3', 'main.py'])

    def update_visibility (self):
        focus_child = self.main_list.focus_child
        self.editor_tabs.visible = not self.fullscreen or focus_child is self.editor
        self.editor.visible = not self.fullscreen or focus_child is self.editor
        self.console_bar.visible = not self.fullscreen or focus_child is self.console
        self.console.visible = not self.fullscreen or focus_child is self.console

def main (screen):
    curses.start_color ()
    curses.use_default_colors ()
    pride = Pride (screen)
    pride.run ()

curses.wrapper (main)
