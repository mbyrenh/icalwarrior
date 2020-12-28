import os
import os.path
import logging
from tempfile import NamedTemporaryFile, TemporaryDirectory, gettempdir
from click.testing import CliRunner
from icalwarrior.cli import run_cli
from icalwarrior.calendars import Calendars
from icalwarrior.configuration import Configuration
import icalwarrior.constants as constants

def setup_dummy_calendar():
    # Create temporary directory for calendars
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = os.path.join(gettempdir(), tmp_dir.name)
    os.mkdir(os.path.join(tmp_dir_path, "test"))

    # Create temporary config file
    config_file = NamedTemporaryFile(delete=False)
    config_file_path = os.path.join(gettempdir(), config_file.name)

    config_file.write(("calendars: " + tmp_dir.name + "\n").encode("utf-8"))
    config_file.close()

    return (tmp_dir, config_file_path)

def remove_dummy_calendar(tmp_dir, config_file_path):
    # Delete temporary config file
    os.remove(config_file_path)

    # Delete temporary directory
    tmp_dir.cleanup()

def test_calendars():
    # Create temporary directory for calendars
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = os.path.join(gettempdir(), tmp_dir.name)
    os.mkdir(os.path.join(tmp_dir_path, "test1"))
    os.mkdir(os.path.join(tmp_dir_path, "test2"))
    os.mkdir(os.path.join(tmp_dir_path, "test3"))

    # Create temporary config file
    config_file = NamedTemporaryFile(delete=False)
    config_file_path = os.path.join(gettempdir(), config_file.name)

    config_file.write(("calendars: " + tmp_dir.name + "\n").encode("utf-8"))
    config_file.close()

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", config_file_path, "calendars"])
    assert result.exit_code == 0
    assert result.output.find("test1") != -1
    assert result.output.find("test2") != -1
    assert result.output.find("test3") != -1

    # Delete temporary config file
    os.remove(config_file_path)

    # Delete temporary directory
    tmp_dir.cleanup()

def test_adding():

    tmp_dir, config_file_path = setup_dummy_calendar()

    config = Configuration(config_file_path)
    cal_db = Calendars(config)
    assert len(cal_db.get_todos()) == 0

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "+testcat", "due:today+3d", "dtstart:today+1d"])
    assert result.exit_code == 0

    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert 'summary' in todos[0]
    assert str(todos[0]['summary']) == "Testtask"
    assert 'categories' in todos[0]
    assert str(todos[0]['categories'].cats[0]) == "testcat"
    assert 'due' in todos[0]
    assert 'dtstart' in todos[0]
    assert 'created' in todos[0]
    assert 'uid' in todos[0]
    assert 'status' in todos[0]
    assert str(todos[0]['status']).lower() == "needs-action"

    remove_dummy_calendar(tmp_dir, config_file_path)


def test_categories_modification():

    tmp_dir, config_file_path = setup_dummy_calendar()

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", constants.CATEGORY_INCLUDE_PREFIX + "test1", constants.CATEGORY_INCLUDE_PREFIX + "test2"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert 'categories' in todos[0]
    assert len(todos[0]['categories'].cats) == 2
    assert str(todos[0]['categories'].cats[0]) == "test1"
    assert str(todos[0]['categories'].cats[1]) == "test2"

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "mod", "1", "--", constants.CATEGORY_EXCLUDE_PREFIX + "test1"])
    assert result.exit_code == 0

    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert 'categories' in todos[0]
    assert len(todos[0]['categories'].cats) == 1
    assert str(todos[0]['categories'].cats[0]) == "test2"

    remove_dummy_calendar(tmp_dir, config_file_path)

def test_property_removal():

    tmp_dir, config_file_path = setup_dummy_calendar()

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "due:today", "+testcat"])
    assert result.exit_code == 0

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "mod", "1", "--", constants.CATEGORY_EXCLUDE_PREFIX + "testcat"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert 'categories' not in todos[0]
    assert 'due' in todos[0]

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "mod", "1", "due:"])
    assert result.exit_code == 0

    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert 'due' not in todos[0]

    remove_dummy_calendar(tmp_dir, config_file_path)

def test_deletion():

    tmp_dir, config_file_path = setup_dummy_calendar()

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask", "due:today", "+testcat"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1

    result = runner.invoke(run_cli, ["-c", str(config_file_path), "del", "1"])
    assert result.exit_code == 0

    config = Configuration(config_file_path)
    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 0

    remove_dummy_calendar(tmp_dir, config_file_path)
