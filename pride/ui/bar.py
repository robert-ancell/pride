# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .widget import Widget

class Bar (Widget):
    def __init__ (self, title = ''):
        Widget.__init__ (self)
        self.title = title
        self.set_scale (1.0, 0.0)

    def set_title (self, text):
        self.title = title

    def get_size (self):
        return (len (self.title), 1)

    def render (self, frame):
        frame.clear ("#0000FF")
        frame.render_text (0, 0, self.title, background = "#0000FF")
