# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Dict, Optional
import os
import os.path
from shutil import rmtree
import uuid
import datetime
import dateutil.tz as tz

import icalendar

from icalwarrior import __author__,__productname__,__version__
from icalwarrior.model.items import TodoModel
from icalwarrior.configuration import Configuration
from icalwarrior.filtering.constraints import ConstraintEvaluator


class DuplicateCalendarNameError(Exception):

    def __init__(self, calendarName : str, firstCalDir : str, secondCalDir : str) -> None:
        self.calendarName = calendarName
        self.firstCalDir = firstCalDir
        self.secondCalDir = secondCalDir

    def __str__(self) -> str:
        return ("Duplicate name '" + self.calendarName + "' found in " + self.firstCalDir + " and " + self.secondCalDir)

class TodoDatabaseAccessError(Exception):

    def __init__(self, path : str) -> None:
        self.path = path

    def __str__(self) -> str:
        return "Error during access of todo lists dir " + self.path + ". Does the directory actually exist?"

class InvalidTodolistError(Exception):

    def __init__(self, path: str) -> None:
        self.path = path

    def __str__(self) -> str:
        return "Invalid todo list dir " + self.path + "."

class ListNotFoundError(Exception):

    def __init__(self, list_name : str) -> None:
        self.list_name = list_name

    def __str__(self) -> str:
        return "Todo list " + self.list_name + " not found."

class TodoNotFoundError(Exception):

    def __init__(self, list_name : str, uid : str) -> None:
        self.uid = uid
        self.list_name = list_name

    def __str__(self) -> str:
        return "Todo item with UID " + self.uid + " not found in list " + self.list_name

class TodoList:

    def __init__(self, config: Configuration, name: str, todos: List[TodoModel]) -> None:

        self.name = name
        self.todos = todos
        self.config = config

    def get_by_uid(self, uid : str) -> icalendar.Todo:

        for item in self.todos:

            if item.get_string("uid") == uid:

                return item.get_ical_todo()

        raise TodoNotFoundError(self.name, uid)

    def add(self, todo : icalendar.Todo) -> None:

        # Since we assume that each todo is stored in a separate calendar,
        # create a calendar as wrapper for the todo item
        todo_cal = icalendar.Calendar()
        todo_cal.add('version', "2.0")
        todo_cal.add('prodid', '-//' + __author__ + '//' + __productname__ + ' ' + __version__ + '//EN')
        todo_cal.add_component(todo)

        path = os.path.join(self.config.get_lists_dir(), self.name, todo['uid'] + ".ics")
        file_handle = open(path, "wb")
        file_handle.write(todo_cal.to_ical())
        file_handle.close()

    def delete(self, todo : icalendar.Todo) -> None:

        path = os.path.join(self.config.get_lists_dir(), self.name, todo['uid'] + ".ics")
        os.remove(path)

    def get_todos(self, constraint_evaluator : Optional[ConstraintEvaluator] = None) -> List[TodoModel]:

        result : List[TodoModel] = []
        for todo_item in self.todos:

            if constraint_evaluator is None or constraint_evaluator.satisfies_constraints(todo_item):
                result.append(todo_item)

        return result

class TodoDatabase:

    def __init__(self, config : Configuration) -> None:
        self.config = config
        self.lists = self.__read_todo_lists()

    def __read_todo_lists(self) -> Dict[str, TodoList]:

        try:
            result : Dict[str, TodoList] = {}
            list_names = os.listdir(self.config.get_lists_dir())
            todo_id = 1
            for current_list in list_names:

                todo_files = os.listdir(os.path.join(self.config.get_lists_dir(), current_list))
                todo_list : List[TodoModel] = []

                for todo_file in todo_files:
                    ical_file = open(os.path.join(self.config.get_lists_dir(), current_list, todo_file), 'r')
                    calendar = icalendar.Calendar.from_ical(ical_file.read())

                    for todo in calendar.walk('vtodo'):

                        wrapped_todo = TodoModel(self.config, todo)
                        # Add context information to be used for filtering etc.
                        wrapped_todo.set_context('list', current_list)
                        wrapped_todo.set_context('id', todo_id)
                        todo_id += 1

                        todo_list.append(wrapped_todo)

                    ical_file.close()

                result[current_list] = TodoList(self.config, current_list, todo_list)

        except FileNotFoundError as err:
            raise TodoDatabaseAccessError(self.config.get_lists_dir()) from err
        except OSError as err:
            raise TodoDatabaseAccessError(self.config.get_lists_dir()) from err

        return result

    def list_exists(self, calendar : str) -> bool:
        return calendar in self.lists

    def get_list_names(self) -> List[str]:
        return list(self.lists.keys())

    def add_list(self, name : str) -> None:

        list_path = os.path.join(self.config.get_lists_dir(), name)
        if not os.path.exists(list_path):
            os.mkdir(list_path)
        else:
            raise InvalidTodolistError(list_path)

    def delete_list(self, name: str) -> None:

        list_path = os.path.join(self.config.get_lists_dir(), name)
        if os.path.exists(list_path):
            rmtree(list_path)
        else:
            raise InvalidTodolistError(list_path)

    def get_list(self, name : str) -> TodoList:

        if not self.list_exists(name):
            raise ListNotFoundError(name)

        return self.lists[name]

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

    def create_todo(self) -> icalendar.Todo:
        todo = icalendar.Todo()

        uid = self.get_unused_uid()
        todo.add('uid', uid)
        now = datetime.datetime.now(tz.gettz())
        todo.add('dtstamp', now, encode=True)
        todo.add('created', now, encode=True)

        return todo

    def move_todo(self, uid : str, source : str, destination : str) -> None:

        src_path = os.path.join(self.config.get_lists_dir(),source,uid + ".ics")
        dst_path = os.path.join(self.config.get_lists_dir(),destination,uid + ".ics")
        os.rename(src_path, dst_path)

    def get_todos(self, constraint_evaluator : Optional[ConstraintEvaluator] = None) -> List[TodoModel]:

        result : List[TodoModel] = []

        for _, todo_list in self.lists.items():

            result = result + todo_list.get_todos(constraint_evaluator)

        return result