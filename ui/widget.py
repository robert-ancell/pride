# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .characterinputevent import CharacterInputEvent
from .keyinputevent import KeyInputEvent

class Widget:
    def __init__ (self):
        self.visible = True

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

    def render (self, frame):
        pass
