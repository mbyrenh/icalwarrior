# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Dict, Optional
import os
import os.path
import uuid
import datetime
import dateutil.tz as tz

import icalendar

from icalwarrior import __author__,__productname__,__version__
from icalwarrior.todo import TodoPropertyHandler
from icalwarrior.configuration import Configuration
from icalwarrior.filter import Constraint
from icalwarrior.util import expand_prefix
import icalwarrior.constants as constants

class DuplicateCalendarNameError(Exception):

    def __init__(self, calendarName : str, firstCalDir : str, secondCalDir : str) -> None:
        self.calendarName = calendarName
        self.firstCalDir = firstCalDir
        self.secondCalDir = secondCalDir

    def __str__(self) -> str:
        return ("Duplicate name '" + self.calendarName + "' found in " + self.firstCalDir + " and " + self.secondCalDir)

class InvalidConstraintFormatError(Exception):

    def __init__(self, constraint : str) -> None:
        self.constraint = constraint

    def __str__(self) -> str:
        return "Invalid constraint \"" + self.constraint + "\". Constraint format is NAME[.OPERATOR]:VALUE"

class InvalidFilterExpressionError(Exception):

    def __init__(self, expression : str) -> None:
        self.expression = expression

    def __str__(self) -> str:
        return "Invalid filter expression \"" + self.expression + "\"."

class Calendars:

    def __init__(self, config : Configuration) -> None:
        self.config = config
        self.calendars = self.__scan_calendars()

        self.todos : List[TodoPropertyHandler] = []
        self.__read_todos()

    def __scan_calendars(self) -> Dict[str, str]:
        result : Dict[str, str] = {}
        calDir = self.config.get_calendar_dir()
        calNames = os.listdir(calDir)
        for name in calNames:
            calPath = calDir + "/" + name
            if name in result:
                raise DuplicateCalendarNameError(name, result[name], calPath)
            else:
                result[name] = calPath
        return result

    DEFAULT_PROPERTY_VALUES = {
        'status' : 'needs-action'
    }

    @staticmethod
    def __set_default_values(todo : icalendar.Todo) -> None:
        for prop_name, prop_val in Calendars.DEFAULT_PROPERTY_VALUES.items():

            if not prop_name in todo:
                factory = icalendar.prop.TypesFactory().for_property(prop_name)
                parsed_val = factory(factory.from_ical(prop_val))
                todo.add(prop_name, parsed_val, encode=False)

    def __read_todos(self) -> None:

        todo_id = 1
        for current_calendar in self.calendars:

            cal_files = os.listdir(self.calendars[current_calendar])
            for cal_file in cal_files:
                ical_file = open(self.calendars[current_calendar] + '/' + cal_file, 'r')
                cal = icalendar.Calendar.from_ical(ical_file.read())

                for todo in cal.walk('vtodo'):

                    # Add context information to be used for filtering etc.
                    todo['context'] = {'calendar' : current_calendar, 'id' : todo_id}
                    todo_id += 1

                    # Add default values for properties that are missing, so that we do not
                    # need to handle absent values during filtering etc.
                    Calendars.__set_default_values(todo)

                    self.todos.append(TodoPropertyHandler(self.config, todo))
                ical_file.close()

    def calendar_exists(self, calendar : str) -> bool:
        return calendar in self.calendars

    def get_calendars(self) -> List[str]:
        return list(self.calendars.keys())

    def get_unused_uid(self) -> str:
        uid = str(uuid.uuid4())
        while not self.is_unique_uid(uid):
            uid = str(uuid.uuid4())
        return uid

    def is_unique_uid(self, uid : str) -> bool:

        result = True
        todos = self.get_todos()

        for todo in todos:
            if todo.get_string('uid') == uid:
                result = False
                break

        return result

    def write_todo(self, calendar : str, todo : icalendar.Todo) -> None:

        assert self.calendar_exists(calendar)

        # Remove context information if necessary.
        # Todo has no context if it was just added.
        if 'context' in todo:
           del todo['context']

        # Since we assume that each todo is stored in a separate calendar,
        # create a calendar as wrapper for the todo item
        todo_cal = icalendar.Calendar()
        todo_cal.add('version', "2.0")
        todo_cal.add('prodid', '-//' + __author__ + '//' + __productname__ + ' ' + __version__ + '//EN')
        todo_cal.add_component(todo)

        path = os.path.join(self.config.get_calendar_dir(),calendar,todo['uid'] + ".ics")
        file_handle = open(path, "wb")
        file_handle.write(todo_cal.to_ical())
        file_handle.close()

    def create_todo(self) -> icalendar.Todo:
        todo = icalendar.Todo()

        uid = self.get_unused_uid()
        todo.add('uid', uid)
        now = datetime.datetime.now(tz.gettz())
        todo.add('dtstamp', now, encode=True)
        todo.add('created', now, encode=True)

        return todo

    def move_todo(self, uid : str, source : str, destination : str) -> None:

        src_path = os.path.join(self.config.get_calendar_dir(),source,uid + ".ics")
        dst_path = os.path.join(self.config.get_calendar_dir(),destination,uid + ".ics")
        os.rename(src_path, dst_path)


    def delete_todo(self, todo : icalendar.Todo) -> None:

        cal_name = todo['context']['calendar']
        path = os.path.join(self.config.get_calendar_dir(),cal_name,todo['uid'] + ".ics")
        os.remove(path)

    def get_todos(self, constraints : Optional[List[str]] = None) -> List[TodoPropertyHandler]:

        result = []

        if constraints is None or len(constraints) == 0:
            result = self.todos

        else:

            for todo in self.todos:

                previous_constraint_type = "NONE"

                buf = ""
                for constraint in constraints:

                    if constraint in ("and", "or"):

                        if (previous_constraint_type != "PROPERTY_VALUE"):
                            raise InvalidFilterExpressionError(constraint)

                        buf += " " + constraint + " "
                        previous_constraint_type = "LOGIC_RELATION"

                    else:

                        if previous_constraint_type == "PROPERTY_VALUE":
                            buf += " and "

                        if constraint.startswith(constants.CATEGORY_INCLUDE_PREFIX) or constraint.startswith(constants.CATEGORY_EXCLUDE_PREFIX):

                            prop_name = "categories"

                            if constraint.startswith(constants.CATEGORY_INCLUDE_PREFIX):
                                prop_val = constraint[len(constants.CATEGORY_INCLUDE_PREFIX):]
                                operator = "contains"
                            else:
                                prop_val = constraint[len(constants.CATEGORY_EXCLUDE_PREFIX):]
                                operator = "not_contains"

                            if Constraint.evaluate(self.config, todo, prop_name, operator, prop_val):
                                buf += "True"
                            else:
                                buf += "False"

                        else:

                            col_pos = constraint.find(":")
                            if col_pos == -1:
                                raise InvalidConstraintFormatError(constraint)

                            dot_pos = constraint[0:col_pos].find(".")
                            if dot_pos != -1:
                                operator = constraint[dot_pos+1:col_pos]
                                prop_name = expand_prefix(constraint[0:dot_pos], TodoPropertyHandler.supported_filter_properties())
                            else:
                                operator = "equals"
                                prop_name = expand_prefix(constraint[0:col_pos], TodoPropertyHandler.supported_filter_properties())

                            prop_val = constraint[col_pos+1:]

                            if Constraint.evaluate(self.config, todo, prop_name, operator, prop_val):
                                buf += "True"
                            else:
                                buf += "False"

                        previous_constraint_type = "PROPERTY_VALUE"

                if previous_constraint_type == "PROPERTY_VALUE":

                    if eval(buf):
                        result.append(todo)

                else:
                    raise InvalidFilterExpressionError(constraint)

        return result
