from typing import List, Set
from tabulate import tabulate
import icalendar
from icalwarrior.todo import Todo
from icalwarrior.configuration import Configuration

class InvalidColumnError(Exception):

    def __init__(self, reportName : str, invalidCol : str, allowedCols : Set[str]) -> None:
        self.reportName = reportName
        self.colName = invalidCol
        self.allowed = allowedCols

    def __str__(self) -> str:
        return ("Invalid column '" + self.colName + "' for report '" + self.reportName + "'. Allowed columns are " + ",".join([x for x in self.allowed]))

class TodoPrinter:

    def __init__(self, config : Configuration, todos : List[Todo], columns : List[str]) -> None:

        allowedCols = set(["id", "calendar"]).union(
            set([s.lower() for s in icalendar.Todo.required]),
            set([s.lower() for s in icalendar.Todo.singletons]),
            set([s.lower() for s in icalendar.Todo.multiple])
        )
        for column in columns:
            if not column in allowedCols:
                raise InvalidColumnError("list", column, allowedCols)

        self.config = config
        self.todos = todos
        self.columns = columns

    def print(self) -> None:

        dataTable = []

        for todo in self.todos:

            row = []
            for column in self.columns:

                if column == "id":
                    row += [todo.getID()]
                elif column == "calendar":
                    row += [todo.getCalendar()]
                else:
                    row += [todo.getIcalTodo().get(column)]

            dataTable += [row]

        print(tabulate(dataTable, [s.capitalize() for s in self.columns]))
