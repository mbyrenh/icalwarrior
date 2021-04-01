from typing import Tuple, List
from abc import abstractmethod

from colorama import Fore
import icalendar
import datetime
import dateutil.tz as tz
import tableformatter

from icalwarrior.util import adapt_datetype

class Tagger:

    @abstractmethod
    def tag(self, row : Tuple) -> dict:
        pass

class DueDateBasedTagger(Tagger):

    def __init__(self,
                 todos : List[icalendar.Todo],
                 past_threshold : datetime.timedelta,
                 future_threshold : datetime.timedelta) -> None:

        self.todos = {}
        for todo in todos:
            self.todos[todo["context"]["id"]] = todo

        self.past_threshold = past_threshold
        self.future_threshold = future_threshold
        self.date = datetime.datetime.now(tz.gettz())

    def tag(self, row : Tuple) -> dict:
        opts = {}

        todo = self.todos[row[0]]

        if "due" in todo:
            due_date = icalendar.prop.vDDDTypes.from_ical(todo["due"])
            now = adapt_datetype(self.date, due_date)

            if due_date > now and due_date - now > self.future_threshold:
                opts[tableformatter.TableFormatter.ROW_OPT_TEXT_COLOR] = Fore.GREEN
            elif now > due_date and now - due_date > self.past_threshold:
                opts[tableformatter.TableFormatter.ROW_OPT_TEXT_COLOR] = Fore.RED
            else:
                opts[tableformatter.TableFormatter.ROW_OPT_TEXT_COLOR] = Fore.YELLOW

        return opts
