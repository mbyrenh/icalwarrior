from typing import List
import pytest

from icalwarrior.todo import Todo
from icalwarrior.view.tabular import TabularToDoView
from icalwarrior.view.formatter import StringFormatter

class DummyConfiguration:

    def __init__(self):
        self.config = {}

    def set_config(self, opt : List[str], value : str) -> None:

        sub_config = self.config

        for elem in opt[0:-1]:

            if elem not in sub_config:
                sub_config[elem] = {}

            sub_config = sub_config[elem]

        sub_config[opt[len(opt)-1]] = value

    def get_config(self, opt : List[str]) -> object:

        sub_config = self.config

        for elem in opt[0:-1]:

            sub_config = sub_config[elem]

        return sub_config[opt[len(opt)-1]]

    def get_date_format(self) -> str:
        result = self.dateformat
        return result

    def get_datetime_format(self) -> str:
        result = self.datetimeformat
        return result


def test_tabular_todo_view(capsys):

    config = DummyConfiguration()
    config.set_config(['info_columns'],"uid,summary,due,description")
    config.dateformat = "%Y-%m-%d"
    config.datetimeformat = "%Y-%m-%dT%H:%M:%S"
    formatter = StringFormatter(config)

    todo = Todo.create("todo1234")
    Todo.set_properties(todo, config, ['summary:Test ToDo', 'status:needs-action'])
    todo['context'] = {'calendar' : 'test', 'id' : 1}

    test_view = TabularToDoView(config, todo, formatter)
    test_view.show()

    out = capsys.readouterr()
    assert "todo1234" in out.out
