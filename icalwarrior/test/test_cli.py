import os
import os.path
import logging
from tempfile import NamedTemporaryFile, TemporaryDirectory, gettempdir
import icalendar
from click.testing import CliRunner
from icalwarrior.cli import run_cli
from icalwarrior.calendars import Calendars
from icalwarrior.configuration import Configuration
import icalwarrior.constants as constants
from icalwarrior.test.util import setup_dummy_calendars, remove_dummy_calendars

def test_calendars():
    # Create temporary directory for calendars
    tmp_dir, config_file_path = setup_dummy_calendars(['test1','test2','test3'])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", config_file_path, "calendars"])
    assert result.exit_code == 0
    assert result.output.find("test1") != -1
    assert result.output.find("test2") != -1
    assert result.output.find("test3") != -1

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_adding():

    tmp_dir, config_file_path = setup_dummy_calendars(["test", "teft"])

    config = Configuration(config_file_path)
    cal_db = Calendars(config)
    assert len(cal_db.get_todos()) == 0

    runner = CliRunner()

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "+testcat", "due:today+3d", "dtstart:today+1d"])
    print(result.output)
    assert result.exit_code == 0

    cal_db = Calendars(config)
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
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 2

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_info():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "+testcat"])
    assert result.exit_code == 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "info", "1"])

    assert "Testtask" in result.output
    assert "testcat" in result.output

    remove_dummy_calendars(tmp_dir, config_file_path)


def test_categories_modification():

    tmp_dir, config_file_path = setup_dummy_calendars(["test"])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", constants.CATEGORY_INCLUDE_PREFIX + "test1", constants.CATEGORY_INCLUDE_PREFIX + "test2"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert todos[0].has_property("categories")
    assert len(todos[0].get_categories()) == 2
    assert str(todos[0].get_categories()[0]) == "test1"
    assert str(todos[0].get_categories()[1]) == "test2"

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "mod", "1", "--", constants.CATEGORY_EXCLUDE_PREFIX + "test1"])
    assert result.exit_code == 0

    cal_db = Calendars(config)
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
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert not todos[0].has_property("categories")
    assert todos[0].has_property('due')

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "mod", "1", "due:"])
    assert result.exit_code == 0

    cal_db = Calendars(config)
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
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert todos[0].has_property('status')
    assert todos[0].get_string('status').lower() == 'needs-action'

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "done", "1"])
    print(result.output)
    assert result.exit_code == 0

    cal_db = Calendars(config)
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
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "del", "1"],input="y")
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "due:today", "+testcat"])
    assert result.exit_code == 0
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask2", "due:today", "+testcat"])
    assert result.exit_code == 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "del", "1", "2"],input="yy")

    remove_dummy_calendars(tmp_dir, config_file_path)

def test_move():

    tmp_dir, config_file_path = setup_dummy_calendars(["test1", "test2"])

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test1", "Testtask", "due:today", "+testcat"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = Calendars(config)
    todos = cal_db.get_todos(["calendar:test1"])
    assert len(todos) == 1
    todos = cal_db.get_todos(["calendar:test2"])
    assert len(todos) == 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "move", "1", "test1", "test2"])
    assert result.exit_code == 0

    cal_db = Calendars(config)
    todos = cal_db.get_todos(["calendar:test1"])
    assert len(todos) == 0
    todos = cal_db.get_todos(["calendar:test2"])
    assert len(todos) == 1

    remove_dummy_calendars(tmp_dir, config_file_path)

