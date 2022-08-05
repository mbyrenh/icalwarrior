# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from icalwarrior.model.lists import TodoDatabase
from icalwarrior.model.items import TodoModel
from icalwarrior.configuration import Configuration
from icalwarrior.filtering.constraints import InvalidFilterExpressionError
from icalwarrior.filtering.constraints import ConstraintEvaluator
from util import setup_dummy_calendars, remove_dummy_calendars

def test_get_todo_and_autoinsertion():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)

    todo = TodoModel(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_wrong',
        'status': 'needs-action'})
    cal_db.get_list("test").add(todo.get_ical_todo())

    # Re-create Calendars instance to trigger reading of newly created todos
    cal_db = TodoDatabase(config)
    todo = TodoModel(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_wrong',
        'status': 'needs-action',
        'category_modifiers': ['+right']})
    cal_db.get_list("test").add(todo.get_ical_todo())

    # Re-create Calendars instance to trigger reading of newly created todos
    cal_db = TodoDatabase(config)
    todo = TodoModel(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_right',
        'status': 'needs-action',
        'category_modifiers': ['+right']})
    cal_db.get_list("test").add(todo.get_ical_todo())

    # Re-create Calendars instance to trigger reading of newly created todos
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 3

    todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["summary.contains:right", "+right"]))
    assert len(todos) == 1

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_get_todo_logic_operators():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)

    todo = TodoModel(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_wrong',
        'status': 'needs-action'})
    cal_db.get_list("test").add(todo.get_ical_todo())

    todo = TodoModel(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_wrong',
        'status': 'needs-action',
        'categories': ["right"]})
    cal_db.get_list("test").add(todo.get_ical_todo())

    todo = TodoModel(config, cal_db.create_todo())
    todo.set_properties({
        'summary': 'test_right',
        'status': 'needs-action',
        'categories': ["right"]})
    cal_db.get_list("test").add(todo.get_ical_todo())

    # Re-create Calendars instance to trigger reading of newly created todos
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["summary.contains:right", "or", "+right"]))
    assert len(todos) == 2

    with pytest.raises(InvalidFilterExpressionError):
        todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["or"]))

    with pytest.raises(InvalidFilterExpressionError):
        todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["+right", "or"]))

    with pytest.raises(InvalidFilterExpressionError):
        todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["+right", "or", "or", "summary.contains:test"]))

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_default_values_for_properties():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)

    todo = TodoModel(config, cal_db.create_todo())
    todo.set_properties(
        {'summary': 'test_wrong'})
    cal_db.get_list("test").add(todo.get_ical_todo())

    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["status:needs-action"]))
    assert len(todos) == 1

    todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["status.not_eq:completed"]))
    assert len(todos) == 1

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_nonexistent_lists_dir():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    tmp_dir.cleanup()

    config = Configuration(config_file_path)

    with pytest.raises(FileNotFoundError):
        cal_db = TodoDatabase(config)

