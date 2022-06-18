import pytest

from icalwarrior.calendars import Calendars, InvalidFilterExpressionError
from icalwarrior.todo import TodoPropertyHandler
from icalwarrior.configuration import Configuration
from icalwarrior.test.util import setup_dummy_calendars, remove_dummy_calendars

def test_get_todo_and_autoinsertion():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    config = Configuration(config_file_path)
    cal_db = Calendars(config)

    todo = TodoPropertyHandler(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_wrong',
        'status': 'needs-action'})
    cal_db.write_todo("test", todo.get_ical_todo())

    # Re-create Calendars instance to trigger reading of newly created todos
    cal_db = Calendars(config)
    todo = TodoPropertyHandler(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_wrong',
        'status': 'needs-action',
        'categories': ['+right']})
    cal_db.write_todo("test", todo.get_ical_todo())

    # Re-create Calendars instance to trigger reading of newly created todos
    cal_db = Calendars(config)
    todo = TodoPropertyHandler(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_right',
        'status': 'needs-action',
        'categories': ['+right']})
    cal_db.write_todo("test", todo.get_ical_todo())

    # Re-create Calendars instance to trigger reading of newly created todos
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 3

    todos = cal_db.get_todos(["summary.contains:right", "+right"])
    assert len(todos) == 1

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_get_todo_logic_operators():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    config = Configuration(config_file_path)
    cal_db = Calendars(config)

    todo = TodoPropertyHandler(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_wrong',
        'status': 'needs-action'})
    cal_db.write_todo("test", todo.get_ical_todo())

    todo = TodoPropertyHandler(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_wrong',
        'status': 'needs-action',
        'categories': ["+right"]})
    cal_db.write_todo("test", todo.get_ical_todo())

    todo = TodoPropertyHandler(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_right',
        'status': 'needs-action',
        'categories': ["+right"]})
    cal_db.write_todo("test", todo.get_ical_todo())

    # Re-create Calendars instance to trigger reading of newly created todos
    cal_db = Calendars(config)
    todos = cal_db.get_todos(["summary.contains:right", "or", "+right"])
    assert len(todos) == 2

    with pytest.raises(InvalidFilterExpressionError):
        todos = cal_db.get_todos(["or"])

    with pytest.raises(InvalidFilterExpressionError):
        todos = cal_db.get_todos(["+right", "or"])

    with pytest.raises(InvalidFilterExpressionError):
        todos = cal_db.get_todos(["+right", "or", "or", "summary.contains:test"])

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_default_values_for_properties():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    config = Configuration(config_file_path)
    cal_db = Calendars(config)

    todo = TodoPropertyHandler(config, cal_db.create_todo())
    todo.set_properties(
        {'summary': 'test_wrong'})
    cal_db.write_todo("test", todo.get_ical_todo())

    cal_db = Calendars(config)
    todos = cal_db.get_todos(["status:needs-action"])
    assert len(todos) == 1

    todos = cal_db.get_todos(["status.not_eq:completed"])
    assert len(todos) == 1

    remove_dummy_calendars(tmp_dir, config_file_path)
