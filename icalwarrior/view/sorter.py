from typing import List

import icalendar
import datetime

class UnsupportedSortKeyError(Exception):

    def __init__(self, key_name : str) -> None:
        self.key_name = key_name

    def __str__(self):
        return "Property \"" + self.key_name + "\" cannot be used for sorting of todos"

class ToDoSorter:

    def __init__(self, todos : List[icalendar.Todo], sort_key : str) -> None:
        self.todos = todos
        self.sort_key = sort_key

    def vDDD_to_timestamp(self, todo : icalendar.Todo, prop_name : str) -> float:
        result = 0
        if prop_name in todo:
            date_val = icalendar.prop.vDDDTypes.from_ical(todo["due"])
            if isinstance(date_val, datetime.date):
                result = datetime.datetime(date_val.year, date_val.month, date_val.day).timestamp()
            if isinstance(date_val, datetime.datetime):
                result = date_val.timestamp()
        return result

    def vText_to_str(self, todo : icalendar.Todo, prop_name : str) -> str:
        result = ""
        if prop_name in todo:
            result = str(todo[prop_name])
        return result

    def vInt_to_int(self, todo : icalendar.Todo, prop_name : str) -> int:
        result = 0
        if prop_name in todo:
            result = int(todo[prop_name])
        return result

    def get_sorted(self) -> List[icalendar.Todo]:

        result = None
        # Determine type of sort element
        key_type = icalendar.prop.TypesFactory().for_property(self.sort_key)

        if key_type is icalendar.prop.vDDDTypes:
            result = sorted(self.todos, key=lambda todo: self.vDDD_to_timestamp(todo, self.sort_key))
        elif key_type is icalendar.prop.vText:
            result = sorted(self.todos, key=lambda todo: self.vText_to_str(todo, self.sort_key))
        elif key_type is icalendar.prop.vInt:
            result = sorted(self.todos, key=lambda todo: self.vInt_to_int(todo, self.sort_key))
        else:
            raise UnsupportedSortKeyError(self.sort_key)

        return result

