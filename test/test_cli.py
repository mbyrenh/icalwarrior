# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
from dateutil.relativedelta import relativedelta
from click.testing import CliRunner
from icalwarrior.cli import run_cli
from icalwarrior.model.lists import TodoDatabase
from icalwarrior.input.date import today_as_datetime
from icalwarrior.configuration import Configuration
from icalwarrior.filtering.constraints import ConstraintEvaluator
import icalwarrior.constants as constants
from util import setup_dummy_calendars, remove_dummy_calendars

def test_lists():
    # Create temporary directory for calendars
    tmp_dir, config_file_path = setup_dummy_calendars(['test1','test2','test3'])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", config_file_path, "lists"])
    assert result.exit_code == 0
    assert result.output.find("test1") != -1
    assert result.output.find("test2") != -1
    assert result.output.find("test3") != -1

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_adding():

    tmp_dir, config_file_path = setup_dummy_calendars(["test", "teft"])

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    assert len(cal_db.get_todos()) == 0

    runner = CliRunner()

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "+testcat", "due:today+3d", "dtstart:today+1d"])
    print(result.output)
    assert result.exit_code == 0

    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert todos[0].has_property('summary')
    assert todos[0].get_string('summary') == "Testtask"
    assert todos[0].has_property('categories')
    assert todos[0].get_categories()[0] == "testcat"
    assert todos[0].has_property('due')
    assert todos[0].has_property('dtstart')
    assert todos[0].has_property('created')
    assert todos[0].has_property('uid')
    assert todos[0].has_property('status')
    assert todos[0].get_string('status').lower() == "needs-action"

    # Test failure if given calendar name prefix is ambiguous
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "te", "Testtask 2"])
    assert result.exit_code > 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "tef", "Testtask 2"])
    assert result.exit_code == 0
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 2

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_add_empty_summary():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", ""])
    assert "Summary text must be non-empty." in result.output
    assert result.exit_code > 0

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_show():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "+testcat"])
    assert result.exit_code == 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "show", "1"])

    assert "Testtask" in result.output
    assert "testcat" in result.output

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_mod_empty_summary():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Test"])
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "mod", "1", ""])
    assert "Summary text must be non-empty." in result.output
    assert result.exit_code > 0

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_due_absolute_date_with_time():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])
    config = Configuration(config_file_path)
    due_date_str = (datetime.datetime.now() + relativedelta(days=+1)).strftime(config.get_datetime_format())

    # Getting due date from parsing ensures we truncate seconds and microseconds
    due_date = datetime.datetime.strptime(due_date_str, config.get_datetime_format())

    runner = CliRunner()

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Test", "due:"+due_date_str])
    assert result.exit_code == 0

    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["status:needs-action"]))
    assert todos[0].get_datetime("due") == due_date

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_due_relative_date_with_time():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])
    config = Configuration(config_file_path)
    expected_date_str = (today_as_datetime() + relativedelta(days=+1, hours=+13, minutes=+37)).strftime(config.get_datetime_format())
    expected_due_date = datetime.datetime.strptime(expected_date_str, config.get_datetime_format())

    due_date_str = "tomorrow" + constants.RELATIVE_DATE_TIME_SEPARATOR + "13:37"
    runner = CliRunner()

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Test", "due:"+due_date_str])
    assert result.exit_code == 0

    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["status:needs-action"]))
    assert todos[0].get_datetime("due") == expected_due_date

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_categories_explicit_specification():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "categories:test1,test2"])
    print(result.output)
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()

    print(result.output)
    assert len(todos) == 1
    assert todos[0].has_property("categories")
    assert len(todos[0].get_categories()) == 2
    assert str(todos[0].get_categories()[0]) == "test1"
    assert str(todos[0].get_categories()[1]) == "test2"

def test_categories_modification():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", constants.CATEGORY_INCLUDE_PREFIX + "test1", constants.CATEGORY_INCLUDE_PREFIX + "test2"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()

    assert len(todos) == 1
    assert todos[0].has_property("categories")
    assert len(todos[0].get_categories()) == 2
    assert str(todos[0].get_categories()[0]) == "test1"
    assert str(todos[0].get_categories()[1]) == "test2"

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "mod", "1", "--", constants.CATEGORY_EXCLUDE_PREFIX + "test1"])
    assert result.exit_code == 0

    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert todos[0].has_property("categories")
    assert len(todos[0].get_categories()) == 1
    assert str(todos[0].get_categories()[0]) == "test2"

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_property_removal():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "due:today", "+testcat"])
    assert result.exit_code == 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "mod", "1", "--", constants.CATEGORY_EXCLUDE_PREFIX + "testcat"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert not todos[0].has_property("categories")
    assert todos[0].has_property('due')

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "mod", "1", "due:"])
    assert result.exit_code == 0

    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert not todos[0].has_property('due')

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_done():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert todos[0].has_property('status')
    assert todos[0].get_string('status').lower() == 'needs-action'

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "done", "1"])
    print(result.output)
    assert result.exit_code == 0

    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert todos[0].has_property('status')
    assert todos[0].get_string('status').lower() == 'completed'
    assert todos[0].get_int('percent-complete') == 100
    assert todos[0].has_property('completed')

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_deletion():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "due:today", "+testcat"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "del", "1"],input="y")
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "due:today", "+testcat"])
    assert result.exit_code == 0
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask2", "due:today", "+testcat"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 2

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "del", "1", "2"],input="y\ny\n")

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 0

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_move():

    tmp_dir, config_file_path = setup_dummy_calendars(["test1", "test2"])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test1", "Testtask", "due:today", "+testcat"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["list:test1"]))
    assert len(todos) == 1
    todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["list:test2"]))
    assert len(todos) == 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "move", "1", "test2"])
    assert result.exit_code == 0

    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["list:test1"]))
    assert len(todos) == 0
    todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["list:test2"]))
    assert len(todos) == 1

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_invalid_config_file():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    config_file = open(config_file_path, "w")
    config_file.write('foo: "Hello')
    config_file.flush()

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask"])
    assert result.exit_code != 0

def test_nonexistent_lists_dir():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    config_file = open(config_file_path, "w")
    config_file.write('lists_dir: /nonexistent')
    config_file.flush()

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask"])
    assert result.exit_code != 0

def test_list_cleanup():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask"])
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask 2"])
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask 3"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 3

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "done", "1", "3"])
    assert result.exit_code == 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "cleanup", "test"], input="y")
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = TodoDatabase(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
