from typing import List, Union, Dict
import datetime
import dateutil.tz as tz
import icalendar

from icalwarrior.util import decode_date, expand_prefix, adapt_datetype
from icalwarrior.configuration import Configuration
import icalwarrior.constants as constants

class UnknownPropertyError(Exception):
    def __init__(self, prop : str, supported : List[str]) -> None:
        self.prop = prop
        self.supported = supported

    def __str__(self) -> str:
        return "Unknown property \"" + self.prop + "\". Supported properties are " + ", ".join(self.supported)

class TodoPropertyHandler:

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
        'uid',
        'calendar'
    ]

    INT_FILTER_PROPERTIES = [
        'id'
    ]

    @staticmethod
    def supported_properties() -> List[str]:
        return TodoPropertyHandler.DATE_PROPERTIES + TodoPropertyHandler.TEXT_PROPERTIES + TodoPropertyHandler.ENUM_PROPERTIES + TodoPropertyHandler.INT_PROPERTIES

    @staticmethod
    def supported_filter_properties() -> List[str]:
        return TodoPropertyHandler.DATE_PROPERTIES + TodoPropertyHandler.TEXT_PROPERTIES + TodoPropertyHandler.ENUM_PROPERTIES + TodoPropertyHandler.INT_PROPERTIES + TodoPropertyHandler.TEXT_FILTER_PROPERTIES + TodoPropertyHandler.INT_FILTER_PROPERTIES

    def __init__(self, configuration : Configuration, todo : icalendar.Todo):
        self.todo = todo

    def get_property_names(self) -> List[str]:
        result = [k for k in list(self.todo.keys()) if k.lower() != "context"]
        return result

    def set_properties(self, property_dict : Dict[str, Union[str, int, datetime.datetime, datetime.date, List[str]]]) -> None:
        # Collect categories in list and add it once to the todo
        # as otherwise, icalendar will add a separate CATEGORIES-line
        # for each category.
        modified = False

        categories = []
        # Make sure we consider existing categories
        if self.has_property('categories'):

            existing_categories = self.get_categories()
            categories = [str(c) for c in existing_categories]

        for prop_name, prop_value in property_dict.items():

            if prop_name == "categories":
                assert isinstance(prop_value, list)
                assert all(isinstance(x, str) for x in prop_value)
                for cat in prop_value:
                    if cat[0] == constants.CATEGORY_INCLUDE_PREFIX:
                        categories.append(cat[1:])
                    elif cat[0] == constants.CATEGORY_EXCLUDE_PREFIX:
                        categories.remove(cat[1:])

            else:

                if prop_name.upper() in icalendar.Todo.singletons and prop_name in self.todo:
                    del self.todo[prop_name]

                # If the value is an empty string,
                # we just delete it.
                if prop_value != "":
                    self.todo.add(prop_name, prop_value, encode=True)

                modified = True

        if 'categories' in self.todo:
            del self.todo['categories']

        if len(categories) > 0:
            self.todo.add("categories", categories)
            modified = True

        if modified:
            self.__update_modification_timestamps()

    def __update_modification_timestamps(self) -> None:
        if 'last-modified' in self.todo:
            del self.todo['last-modified']
        self.todo.add('last-modified', datetime.datetime.now(tz.gettz()))

        del self.todo['dtstamp']
        self.todo.add('dtstamp', datetime.datetime.now(tz.gettz()))

    def get_ical_todo(self) -> icalendar.Todo:
        return self.todo

    def get_context(self) -> Dict[str, Union[str, int]]:

        result = self.todo["context"]
        if isinstance(result, dict):
            return result

        raise Exception("Object of non-dict type " + type(result).__name__ + " given.")

    def get_datetime(self, prop_name : str) -> datetime.datetime:

        result = icalendar.prop.vDDDTypes.from_ical(self.todo[prop_name])
        if isinstance(result, (datetime.datetime, datetime.date)):
            result = adapt_datetype(result, icalendar.prop.vDDDTypes(datetime.datetime.now()))
            # Additional check for datetime.datetime instance to make mypy happy
            if isinstance(result, datetime.datetime):
                return result

        raise Exception("Object of non-datetime type " + type(result).__name__ + " given.")

    def get_date_or_datetime(self, prop_name : str) -> datetime.datetime | datetime.date:

        result = icalendar.prop.vDDDTypes.from_ical(self.todo[prop_name])
        if isinstance(result, (datetime.datetime, datetime.date)):
            return result

        raise Exception("Object of non-datetime  or date type " + type(result).__name__ + " given.")

    def get_categories(self) -> List[str]:

        categories = self.todo['categories']
        if isinstance(categories, icalendar.prop.vCategory):
            result = categories.cats
            if isinstance(result, list) and (len(result) == 0 or isinstance(result[0], str)):
                return result

        raise Exception("Object of non-list type " + type(result).__name__ + " given.")

    def get_int(self, prop_name : str) -> int:

        result = icalendar.prop.vInt.from_ical(self.todo[prop_name])
        if isinstance(result, int):
            return result

        raise Exception("Object of non-int type " + type(result).__name__ + " given.")

    def get_string(self, prop_name : str) -> str:

        result = icalendar.prop.vText.from_ical(self.todo[prop_name])
        if isinstance(result, str):
            return result

        raise Exception("Object of non-string type " + type(result).__name__ + " given.")

    def has_property(self, prop_name : str) -> bool:
        return prop_name in self.todo

    def unset_property(self, prop_name : str) -> None:
        del self.todo[prop_name]
