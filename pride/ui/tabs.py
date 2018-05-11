# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .widget import Widget

class Tabs (Widget):
    def __init__ (self):
        Widget.__init__ (self)
        self.tabs = []
        self.set_scale (1.0, 0.0)

    def add_child (self, label):
        self.tabs.append (label)

    def get_size (self):
        return (0, 1)

    def render (self, frame):
        frame.clear ("#0000FF")
        row = 0
        for label in self.tabs:
            text = label + '│'
            frame.render_text (row, 0, text, background = "#0000FF")
            row += len (text)
