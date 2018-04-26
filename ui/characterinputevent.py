# Copyright (C) 2018 Robert Ancell
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. See http://www.gnu.org/copyleft/gpl.html the full text of the
# license.

from .inputevent import InputEvent

class CharacterInputEvent (InputEvent):
    def __init__ (self, character):
        self.character = character

    def __str__ (self):
        return 'CharacterInputEvent({})'.format (self.character)
