# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import Tuple, List, Dict
from abc import abstractmethod

from colorama import Fore
import icalendar
import datetime
import dateutil.tz as tz
import tableformatter

from icalwarrior.util import adapt_datetype
from icalwarrior.todo import TodoPropertyHandler

class Tagger:

    @abstractmethod
    def tag(self, row : List[str]) -> Dict[str, int]:
        pass

class DueDateBasedTagger(Tagger):

    def __init__(self,
                 todos : List[TodoPropertyHandler],
                 past_threshold : datetime.timedelta,
                 future_threshold : datetime.timedelta) -> None:

        self.todos: Dict[str, TodoPropertyHandler] = {}
        for todo in todos:
            todo_context = todo.get_context()
            self.todos[str(todo_context["id"])] = todo

        self.past_threshold = past_threshold
        self.future_threshold = future_threshold
        self.date = datetime.datetime.now(tz.gettz())

    def tag(self, row : List[str]) -> Dict[str, int]:
        opts : Dict[str, int] = {}

        todo = self.todos[row[0]]

        if todo.has_property("due"):
            due_date = todo.get_date_or_datetime("due")
            now = adapt_datetype(self.date, due_date)

            if due_date > now and due_date - now > self.future_threshold:
                opts[tableformatter.TableFormatter.ROW_OPT_TEXT_COLOR] = Fore.GREEN
            elif now > due_date and now - due_date > self.past_threshold:
                opts[tableformatter.TableFormatter.ROW_OPT_TEXT_COLOR] = Fore.RED
            else:
                opts[tableformatter.TableFormatter.ROW_OPT_TEXT_COLOR] = Fore.YELLOW

        return opts
