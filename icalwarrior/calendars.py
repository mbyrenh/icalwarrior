from typing import List, Dict
import os
import os.path
import _pickle as pickle
import uuid

import icalendar

from icalwarrior import __author__,__productname__,__version__
from icalwarrior.todo import Todo
from icalwarrior.configuration import Configuration
from icalwarrior.filter import Constraint
from icalwarrior.util import expand_prefix

class DuplicateCalendarNameError(Exception):

    def __init__(self, calendarName : str, firstCalDir : str, secondCalDir : str) -> None:
        self.calendarName = calendarName
        self.firstCalDir = firstCalDir
        self.secondCalDir = secondCalDir

    def __str__(self):
        return ("Duplicate name '" + self.calendarName + "' found in " + self.firstCalDir + " and " + self.secondCalDir)

class InvalidConstraintFormatError(Exception):

    def __init__(self, constraint : str) -> None:
        self.constraint = constraint

    def __str__(self):
        return "Invalid constraint \"" + self.constraint + "\". Constraint format is NAME[.OPERATOR]:VALUE"

class Calendars:

    def __init__(self, config : Configuration) -> None:
        self.config = config
        self.calendars = self.__scan_calendars()

        self.todos = []
        self.__read_todos()

    def __scan_calendars(self) -> Dict[str, str]:
        result = {}
        calDir = self.config.get_calendar_dir()
        calNames = os.listdir(calDir)
        for name in calNames:
            calPath = calDir + "/" + name
            if name in result:
                raise DuplicateCalendarNameError(name, result[name], calPath)
            else:
                result[name] = calPath
        return result

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
                    self.todos.append(todo)
                ical_file.close()

    def calendarExists(self, calendar : str) -> bool:
        return calendar in self.calendars

    def get_calendars(self) -> List[str]:
        return self.calendars.keys()

    def get_unused_uid(self) -> str:
        uid = uuid.uuid4()
        while not self.is_unique_uid(uid):
            uid = uuid.uuid4()
        return uid

    def is_unique_uid(self, uid : str) -> bool:

        result = True
        todos = self.get_todos()

        for todo in todos:
            if todo['uid'] == uid:
                result = False
                break

        return result

    def write_todo(self, calendar : str, todo : icalendar.Todo) -> None:

        assert self.calendarExists(calendar)

        # Remove context information if necessary.
        # Todo has no context if it was just added.
        if 'context' in todo:
           del todo['context']

        # Since we assume that each todo is stored in a separate calendar,
        # create a calendar as wrapper for the todo item
        todo_cal = icalendar.Calendar()
        todo_cal.add('prodid', '-//' + __author__ + '//' + __productname__ + ' ' + __version__ + '//EN')
        todo_cal.add_component(todo)

        path = os.path.join(self.config.get_calendar_dir(),calendar,todo['uid'] + ".ics")
        file_handle = open(path, "wb")
        file_handle.write(todo_cal.to_ical())
        file_handle.close()

    def delete_todo(self, todo : icalendar.Todo) -> None:

        cal_name = todo['context']['calendar']
        path = os.path.join(self.config.get_calendar_dir(),cal_name,todo['uid'] + ".ics")
        os.remove(path)

    def get_todos(self, constraints = None) -> List[icalendar.Todo]:

        result = []

        if constraints == None or len(constraints) == 0:
            result = self.todos

        else:

            for todo in self.todos:

                buf = ""
                for constraint in constraints:

                    if constraint in ("and", "or"):
                        buf += " " + constraint + " "

                    elif constraint.startswith("+"):

                        prop_name = "categories"
                        prop_val = constraint[1:]
                        operator = "contains"

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
                            prop_name = expand_prefix(constraint[0:dot_pos], Todo.supported_filter_properties())
                        else:
                            operator = "equals"
                            prop_name = expand_prefix(constraint[0:col_pos], Todo.supported_filter_properties())

                        prop_val = constraint[col_pos+1:]

                        if Constraint.evaluate(self.config, todo, prop_name, operator, prop_val):
                            buf += "True"
                        else:
                            buf += "False"

                if eval(buf):
                    result.append(todo)

        return result
