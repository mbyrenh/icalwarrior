from typing import List, Dict
import os
import os.path
import _pickle as pickle

import icalendar

from icalwarrior import __author__,__productname__,__version__
from icalwarrior.todo import Todo
from icalwarrior.configuration import Configuration

class DuplicateCalendarNameError(Exception):

    def __init__(self, calendarName : str, firstCalDir : str, secondCalDir : str) -> None:
        self.calendarName = calendarName
        self.firstCalDir = firstCalDir
        self.secondCalDir = secondCalDir

    def __str__(self):
        return ("Duplicate name '" + self.calendarName + "' found in " + self.firstCalDir + " and " + self.secondCalDir)

class Calendars:

    def __init__(self, config : Configuration) -> None:
        self.config = config
        self.calendars = self.__scan_calendars()

        self.todos = {}
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

        for current_calendar in self.calendars:

            self.todos[current_calendar] = []

            cal_files = os.listdir(self.calendars[current_calendar])
            for cal_file in cal_files:
                ical_file = open(self.calendars[current_calendar] + '/' + cal_file, 'r')
                cal = icalendar.Calendar.from_ical(ical_file.read())

                for todo in cal.walk('vtodo'):
                    self.todos[current_calendar].append(todo)
                ical_file.close()


    def calendarExists(self, calendar : str) -> bool:
        if calendar in self.calendars:
            return True
        else:
            return False

    def get_calendars(self) -> List[str]:
        return self.calendars.keys()

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

        cal_name = self.get_calendar(todo)
        path = os.path.join(self.config.get_calendar_dir(),cal_name,todo['uid'] + ".ics")
        os.remove(path)

    def get_calendar(self, todo : icalendar.Todo) -> str:

        result = ""
        for cal in self.calendars:
            todos = self.get_todos(cal)

            for cal_todo in todos:

                if cal_todo['uid'] == todo['uid']:
                    result = cal
                    break

        return result

    def get_todos(self, calendar = None) -> List[icalendar.Todo]:

        assert calendar is None or self.calendarExists(calendar)

        result = []

        relevant_calendars = self.calendars.keys()
        if calendar is not None:
            relevant_calendars = [calendar]

        for current_calendar in relevant_calendars:
            result += self.todos[current_calendar]

        result.sort(key=lambda todo : todo['uid'])
        return result
