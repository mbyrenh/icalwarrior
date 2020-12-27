import os
import os.path
import logging
from tempfile import NamedTemporaryFile, TemporaryDirectory, gettempdir
from click.testing import CliRunner
from icalwarrior.cli import run_cli
from icalwarrior.calendars import Calendars
from icalwarrior.configuration import Configuration

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
    # Create temporary directory for calendars
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = os.path.join(gettempdir(), tmp_dir.name)
    os.mkdir(os.path.join(tmp_dir_path, "test"))

    # Create temporary config file
    config_file = NamedTemporaryFile(delete=False)
    config_file_path = os.path.join(gettempdir(), config_file.name)

    config_file.write(("calendars: " + tmp_dir.name + "\n").encode("utf-8"))
    config_file.close()

    config = Configuration(config_file_path)
    cal_db = Calendars(config)
    assert len(cal_db.get_todos()) == 0

    runner = CliRunner()
    result = runner.invoke(run_cli, ["-c", str(config_file_path), "add", "test", "Testtask"])
    assert result.exit_code == 0

    cal_db = Calendars(config)
    todos = cal_db.get_todos()
    assert len(todos) == 1
    assert str(todos[0]['summary']) == "Testtask"

    # Delete temporary config file
    os.remove(config_file_path)

    # Delete temporary directory
    tmp_dir.cleanup()
