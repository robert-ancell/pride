# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .box import Box
from .box import BoxStyle
from .focusevent import FocusEvent
from .grid import Grid
from .keyinputevent import Key
from .keyinputevent import KeyInputEvent
from .label import Label

class Button (Box):
    def __init__ (self, text, shortcut_text = '', background = None, clicked_callback = None):
        Box.__init__ (self, foreground = '#000000', background = background, style = BoxStyle.CURVED)
        self.clicked_callback = clicked_callback
        self.grid = Grid ()
        self.set_child (self.grid)
        label = Label (text, foreground = '#000000')
        self.grid.append_column (label)
        if shortcut_text != '':
            label = Label (' ' + shortcut_text, foreground = '#C0C0C0')
            self.grid.append_column (label)

    def handle_event (self, event):
        open ('debug.log', 'a').write ('button event {}\n'.format (event))
        if isinstance (event, FocusEvent):
            if event.has_focus:
                self.set_style (BoxStyle.BOLD)
                self.set_foreground ('#FF0000')
            else:
                self.set_style (BoxStyle.CURVED)
                self.set_foreground ('#000000')
            return True
        elif isinstance (event, KeyInputEvent):
            if event.key == Key.ENTER:
                if self.clicked_callback is not None:
                    self.clicked_callback ()
                return True
            else:
                return False
        else:
            return False
