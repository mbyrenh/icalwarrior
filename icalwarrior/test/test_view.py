from typing import List
import pytest

from icalwarrior.todo import TodoPropertyHandler
from icalwarrior.calendars import Calendars
from icalwarrior.view.tabular import TabularToDoView
from icalwarrior.view.formatter import StringFormatter
from icalwarrior.configuration import Configuration

from icalwarrior.test.util import setup_dummy_calendars, remove_dummy_calendars

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

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])
    config = Configuration(config_file_path)
    cal_db = Calendars(config)

    todo = TodoPropertyHandler(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'Test ToDo',
        'status': 'needs-action'})
    todo.get_ical_todo()['context'] = {}
    todo.get_context()['calendar'] = 'test'
    todo.get_context()['id'] = 1234

    formatter = StringFormatter(config)
    test_view = TabularToDoView(config, todo, formatter)
    test_view.show()

    out = capsys.readouterr()
    assert "Test ToDo" in out.out
