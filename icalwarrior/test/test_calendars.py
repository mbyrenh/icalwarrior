import pytest
import os
import os.path

from tempfile import NamedTemporaryFile, TemporaryDirectory, gettempdir
from icalwarrior.calendars import Calendars, InvalidFilterExpressionError
from icalwarrior.todo import Todo
from icalwarrior.configuration import Configuration

def setup_dummy_calendars(calendars):
    # Create temporary directory for calendars
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = os.path.join(gettempdir(), tmp_dir.name)

    for cal in calendars:
        os.mkdir(os.path.join(tmp_dir_path, cal))

    # Create temporary config file
    config_file = NamedTemporaryFile(delete=False)
    config_file_path = os.path.join(gettempdir(), config_file.name)

    config_file.write(("calendars: " + tmp_dir.name + "\n").encode("utf-8"))
    config_file.write(("info_columns: uid,summary,created,categories,description\n").encode("utf-8"))
    config_file.close()

    return (tmp_dir, config_file_path)

def remove_dummy_calendars(tmp_dir, config_file_path):
    # Delete temporary config file
    os.remove(config_file_path)

    # Delete temporary directory
    tmp_dir.cleanup()

def test_get_todo_and_autoinsertion():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    config = Configuration(config_file_path)
    cal_db = Calendars(config)

    todo = Todo.create(cal_db.get_unused_uid())
    Todo.set_properties(todo, config, ['summary:test_wrong', 'status:needs-action'])
    cal_db.write_todo("test", todo)

    # Re-create Calendars instance to trigger reading of newly created todos
    cal_db = Calendars(config)
    todo = Todo.create(cal_db.get_unused_uid())
    Todo.set_properties(todo, config, ['summary:test_wrong', 'status:needs-action', "+right"])
    cal_db.write_todo("test", todo)

    # Re-create Calendars instance to trigger reading of newly created todos
    cal_db = Calendars(config)
    todo = Todo.create(cal_db.get_unused_uid())
    Todo.set_properties(todo, config, ['summary:test_right', 'status:needs-action', "+right"])
    cal_db.write_todo("test", todo)

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

    todo = Todo.create(cal_db.get_unused_uid())
    Todo.set_properties(todo, config, ['summary:test_wrong', 'status:needs-action'])
    cal_db.write_todo("test", todo)

    todo = Todo.create(cal_db.get_unused_uid())
    Todo.set_properties(todo, config, ['summary:test_wrong', 'status:needs-action', "+right"])
    cal_db.write_todo("test", todo)

    todo = Todo.create(cal_db.get_unused_uid())
    Todo.set_properties(todo, config, ['summary:test_right', 'status:needs-action', "+right"])
    cal_db.write_todo("test", todo)

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

    todo = Todo.create(cal_db.get_unused_uid())
    Todo.set_properties(todo, config, ['summary:test_wrong'])
    cal_db.write_todo("test", todo)

    cal_db = Calendars(config)
    todos = cal_db.get_todos(["status:needs-action"])
    assert len(todos) == 1

    todos = cal_db.get_todos(["status.not_eq:completed"])
    assert len(todos) == 1

    remove_dummy_calendars(tmp_dir, config_file_path)
