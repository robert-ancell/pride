# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .box import Box
from .box import BoxStyle
from .grid import Grid
from .label import Label

class Button (Box):
    def __init__ (self, text, shortcut_text = '', background = None):
        Box.__init__ (self, background = background)
        self.grid = Grid ()
        self.set_child (self.grid)
        label = Label (text, foreground = '#000000')
        self.grid.append_column (label)
        if shortcut_text != '':
            label = Label (' ' + shortcut_text, foreground = '#C0C0C0')
            self.grid.append_column (label)
        self.set_selected (False)

    def set_selected (self, is_selected):
        if is_selected:
            self.set_style (BoxStyle.BOLD)
            self.set_foreground ('#FF0000')
        else:
            self.set_style (BoxStyle.CURVED)
            self.set_foreground ('#000000')
