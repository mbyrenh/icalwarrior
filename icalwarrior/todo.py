from typing import List
from datetime import datetime
import icalendar
import dateutil.tz as tz

from icalwarrior.args import arg_type, ArgType
from icalwarrior.util import decode_date, expand_prefix
from icalwarrior.configuration import Configuration
import icalwarrior.constants as constants

class InvalidEnumValueError(Exception):

    def __init__(self, prop : str, given : str, supported : List[str]) -> None:
        self.prop = prop
        self.given = given
        self.supported = supported

    def __str__(self) -> str:
        return "Invalid value \"" + self.given + "\" for property \"" + self.prop + "\". Supported values are " + ", ".join(self.supported)

class UnknownPropertyError(Exception):
    def __init__(self, prop : str, supported : List[str]) -> None:
        self.prop = prop
        self.supported = supported

    def __str__(self) -> str:
        return "Unknown property \"" + self.prop + "\". Supported properties are " + ", ".join(self.supported)

class Todo:

    DATE_PROPERTIES = [
        'due',
        'dtstart',
        'dtend',
        'completed'
    ]

    TEXT_PROPERTIES = [
        'summary',
        'description',
        'categories',
    ]

    INT_PROPERTIES = [
        'priority',
        'percent-complete'
    ]

    ENUM_PROPERTIES = [
        'status'
    ]

    ENUM_VALUES = {
        'status' : ["needs-action", "completed", "in-process", "cancelled"]
    }

    DATE_IMMUTABLE_PROPERTIES = [
        'created'
    ]

    TEXT_IMMUTABLE_PROPERTIES = [
        'uid'
    ]

    TEXT_FILTER_PROPERTIES = [
        'calendar'
    ]

    INT_FILTER_PROPERTIES = [
        'id'
    ]

    @staticmethod
    def supported_properties() -> List[str]:
        return Todo.DATE_PROPERTIES + Todo.TEXT_PROPERTIES + Todo.ENUM_PROPERTIES + Todo.INT_PROPERTIES

    @staticmethod
    def supported_filter_properties() -> List[str]:
        return Todo.DATE_PROPERTIES + Todo.TEXT_PROPERTIES + Todo.ENUM_PROPERTIES + Todo.INT_PROPERTIES + Todo.TEXT_FILTER_PROPERTIES + Todo.INT_FILTER_PROPERTIES

    @staticmethod
    def create(uid : str) -> icalendar.Todo:
        todo = icalendar.Todo()

        todo.add('uid', uid)
        now = datetime.now(tz.gettz())
        todo.add('dtstamp', now, encode=True)
        todo.add('created', now, encode=True)

        return todo

    @staticmethod
    def parse_property(config : Configuration, prop_name : str, raw_value : str) -> object:

        result = None
        if prop_name in Todo.DATE_PROPERTIES:
            result = decode_date(raw_value, config)

        elif prop_name in Todo.TEXT_PROPERTIES:
            result = raw_value

        elif prop_name in Todo.INT_PROPERTIES:
            # To check if the value is actually an int, try converting
            result = str(int(raw_value))

        elif prop_name in Todo.ENUM_PROPERTIES:

            if raw_value.lower() in Todo.ENUM_VALUES[prop_name]:
                    result = raw_value
            else:
                raise InvalidEnumValueError(prop_name, raw_value, Todo.ENUM_VALUES[prop_name])
        else:
            raise UnknownPropertyError(prop_name, Todo.supported_properties())


        return result

    @staticmethod
    def set_properties(todo : icalendar.Todo, config : Configuration, raw_properties : List[str]) -> None:
        # Collect categories in list and add it once to the todo
        # as otherwise, icalendar will add a separate CATEGORIES-line
        # for each category.
        modified = False

        categories = []
        # Make sure we consider existing categories
        if 'categories' in todo:
            categories = [str(c) for c in todo['categories'].cats]

        for arg in raw_properties:
            argtype = arg_type(arg, Todo.supported_properties())

            if argtype == ArgType.CATEGORY:

                if arg[0] == constants.CATEGORY_INCLUDE_PREFIX:
                    categories.append(arg[1:])
                elif arg[0] == constants.CATEGORY_EXCLUDE_PREFIX:
                    categories.remove(arg[1:])

            elif argtype == ArgType.PROPERTY:

                col_pos = arg.find(':')
                arg_name = arg[0:col_pos]
                arg_raw_value = arg[col_pos+1:]

                arg_name_full = expand_prefix(arg_name, Todo.supported_properties())

                if arg_name_full.upper() in icalendar.Todo.singletons and arg_name_full in todo:
                    del todo[arg_name_full]

                # If the value is an empty string,
                # we just delete it.
                if arg_raw_value != "":
                    arg_value = Todo.parse_property(config, arg_name_full, arg_raw_value)
                    todo.add(arg_name_full, arg_value, encode=True)

                modified = True

            elif argtype == ArgType.STRING:

                del todo['summary']
                todo.add('summary', arg)
                modified = True

        if 'categories' in todo:
            del todo['categories']
        if len(categories) > 0:
            todo.add("categories", categories)
            modified = True

        if modified:
            if 'last-modified' in todo:
                del todo['last-modified']
            todo.add('last-modified', datetime.now(tz.gettz()))

            del todo['dtstamp']
            todo.add('dtstamp', datetime.now(tz.gettz()))
