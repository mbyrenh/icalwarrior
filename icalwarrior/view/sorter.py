# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List

import datetime
import icalendar
from icalwarrior.todo import TodoPropertyHandler

class UnsupportedSortKeyError(Exception):

    def __init__(self, key_name : str) -> None:
        self.key_name = key_name

    def __str__(self) -> str:
        return "Property \"" + self.key_name + "\" cannot be used for sorting of todos"

class ToDoSorter:

    def __init__(self, todos : List[TodoPropertyHandler], sort_key : str) -> None:
        self.todos = todos
        self.sort_key = sort_key

    def date_to_timestamp(self, todo : TodoPropertyHandler, prop_name : str) -> float:
        result = 0.0
        if todo.has_property(prop_name):
            date_val = todo.get_date_or_datetime(prop_name)
            if isinstance(date_val, datetime.date):
                result = datetime.datetime(date_val.year, date_val.month, date_val.day).timestamp()
            if isinstance(date_val, datetime.datetime):
                result = date_val.timestamp()
        return result

    def get_sorted(self) -> List[TodoPropertyHandler]:

        result = None
        # Determine type of sort element
        key_type = icalendar.prop.TypesFactory().for_property(self.sort_key)

        if key_type is icalendar.prop.vDDDTypes:
            result = sorted(self.todos, key=lambda todo: self.date_to_timestamp(todo, self.sort_key))
        elif key_type is icalendar.prop.vText:
            result = sorted(self.todos, key=lambda todo: todo.get_string(self.sort_key))
        elif key_type is icalendar.prop.vInt:
            result = sorted(self.todos, key=lambda todo: todo.get_int(self.sort_key))
        else:
            raise UnsupportedSortKeyError(self.sort_key)

        return result

