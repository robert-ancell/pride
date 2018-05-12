# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .characterinputevent import CharacterInputEvent
from .frame import Frame
from .keyinputevent import KeyInputEvent

class Widget:
    def __init__ (self):
        self.visible = True
        self.x_align = 0.5
        self.x_scale = 0.0
        self.y_align = 0.5
        self.y_scale = 0.0
        self._child_frame = None

    def set_align (self, x_align, y_align):
        self.x_align = x_align
        self.y_align = y_align

    def set_scale (self, x_scale, y_scale):
        self.x_scale = x_scale
        self.y_scale = y_scale

    def get_size (self):
        return (0, 0)

    def handle_event (self, event):
        if isinstance (event, CharacterInputEvent):
            self.handle_character_event (event)
        elif isinstance (event, KeyInputEvent):
            self.handle_key_event (event)

    def handle_character_event (self, event):
        pass

    def handle_key_event (self, event):
        pass

    def render (self, frame, theme):
        pass

    def render_aligned (self, frame, theme):
        (width, height) = self.get_size ()
        width = min (width, frame.width)
        height = min (height, frame.height)
        used_width = width + int ((frame.width - width) * self.x_scale)
        used_height = height + int ((frame.height - height) * self.y_scale)
        x_offset = int ((frame.width - used_width) * self.x_align)
        y_offset = int ((frame.height - used_height) * self.y_align)

        if (used_width, used_height) == (frame.width, frame.height):
            self.render (frame, theme)
            return

        if self._child_frame is None or (self._child_frame.width, self._child_frame.height) != (used_width, used_height):
            self._child_frame = Frame (used_width, used_height)
        self.render (self._child_frame, theme)
        frame.composite (x_offset, y_offset, self._child_frame)
        if self._child_frame.cursor is not None:
            frame.cursor = (self._child_frame.cursor[0] + x_offset, self._child_frame.cursor[1] + y_offset)
