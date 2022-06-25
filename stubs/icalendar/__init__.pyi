# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Any, Union, Tuple, List, Dict, Optional
from collections import OrderedDict
from icalendar.prop import vText, vInt, vCategory, vDDDTypes

class CaselessDict(OrderedDict[str, Any]):
    pass

class Component(CaselessDict):
    @classmethod
    def from_ical(cls, st : str, multiple: bool = False) -> Component: ...

    def to_ical(self, sorted: bool = True) -> bytes: ...

    def walk(self, name : Optional[str] = None) -> List[Any]: ...

    def add(self, name : str, value : Any, parameters : Optional[Dict[str, str]] = None, encode : bool = True) -> None: ...

    def add_component(self, component : Component) -> None: ...

class Todo(Component):
    singletons : Tuple[str]

class Calendar(Component):
    pass
