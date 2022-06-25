# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import os.path
import os
import subprocess
from tempfile import NamedTemporaryFile, gettempdir

from typing import List, cast, Optional

import json
import click
import colorama
import tableformatter
import datetime
from termcolor import colored
from icalwarrior.configuration import Configuration, UnknownConfigurationOptionError
from icalwarrior.calendars import Calendars
from icalwarrior.todo import TodoPropertyHandler
from icalwarrior.util import expand_prefix, decode_date
from icalwarrior.args import decode_raw_arg_list
from icalwarrior.view.formatter import StringFormatter
from icalwarrior.view.tagger import DueDateBasedTagger
from icalwarrior.view.tabular import TabularToDoListView, TabularPrinter, TabularToDoView
from icalwarrior.view.sorter import ToDoSorter

class InvalidArgumentException(Exception):

    def __init__(self, arg_name :str, supported : List[str]) -> None:
        self.arg_name = arg_name
        self.supported = supported

    def __str__(self) -> str:
        return ("Unknown property '" + self.arg_name + "'. Supported properties are " + ",".join(self.supported))

class CommandAliases(click.Group):

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        cmd = expand_prefix(cmd_name, self.list_commands(ctx))
        if cmd != "":
            return click.Group.get_command(self, ctx, cmd)
        fail(ctx,'Invalid command "%s"' % cmd_name)
        return None

def fail(ctx: click.Context, msg : str) -> None:
    ctx.fail(colored(msg, 'red'))

def success(msg : str) -> None:
    click.echo(colored(msg, 'green'))

def hint(msg : str) -> None:
    click.echo(colored(msg, 'yellow'))

@click.command(cls=CommandAliases)
@click.option('-c', '--config', default=Configuration.get_default_config_path(), help='Path to the configuration file')
@click.pass_context
def run_cli(ctx: click.Context, config: str) -> None:

    colorama.init()

    try:
        configuration = Configuration(config)

        ctx.ensure_object(dict)
        ctx.obj['config'] = configuration
    except FileNotFoundError:
        fail(ctx, "Unable to find configuration file " + config)
    except PermissionError:
        fail(ctx, "Missing permissions to open configuration file " + config)

# Type cast needed to tell mypy that run_cli is actually
# an instance of CommandAliases. Otherwise, it will infer
# it to be of type Command, which is a subclass of CommandAliases.
run_cli = cast(CommandAliases, run_cli)

@run_cli.command()
@click.pass_context
def calendars(ctx: click.Context) -> None:
    cal = Calendars(ctx.obj['config'])

    cols = ["Name", "Path", "Total number of todos", "Number of completed todos"]
    rows : List[List[str]] = []

    cal_db = Calendars(ctx.obj['config'])
    for name in cal.get_calendars():
        path = os.path.join(ctx.obj['config'].get_calendar_dir(), name)
        todos = cal_db.get_todos(["cal:" + name])
        completed_todos = cal_db.get_todos(["cal:" + name, "and", "status:completed"])
        rows.append([name, path, str(len(todos)), str(len(completed_todos))])

    printer = TabularPrinter(rows, cols, 0, tableformatter.WrapMode.WRAP, None)
    printer.print()

@run_cli.command()
@click.pass_context
@click.argument('calendar', nargs=1, required=True)
@click.argument('summary', nargs=1, required=True)
@click.argument('properties', nargs=-1)
def add(ctx: click.Context, calendar: str, summary: str, properties: List[str]) -> None:

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        fail(ctx, "No calendars found. Please check your configuration.")

    calendar_name = expand_prefix(calendar, cal_db.get_calendars())
    if calendar_name == "":
        fail(ctx, "Unknown calendar \"" + calendar + ". Known calendars are " + ", ".join(cal_db.get_calendars()) + ".")

    if len(summary) == 0:
        fail(ctx, "Summary text must be non-empty.")

    todo = None
    try:
        todo = TodoPropertyHandler(ctx.obj['config'], cal_db.create_todo())
        property_dict = decode_raw_arg_list(ctx.obj['config'], ['summary:' + summary, 'status:needs-action'] + [p for p in properties])
        todo.set_properties(property_dict)
        cal_db.write_todo(calendar_name, todo.get_ical_todo())
    except Exception as err:
        fail(ctx, str(err))

    assert todo is not None
    # Re-read calendars to trigger id generation of todo
    uid = todo.get_string('uid')
    cal_db = Calendars(ctx.obj['config'])
    todo = cal_db.get_todos(["uid:" + uid])[0]

    success("Successfully created new todo \"" + todo.get_string('summary') + "\" with ID " + str(todo.get_context()["id"]) + ".")

@run_cli.command()
@click.pass_context
@click.argument('identifier', nargs=1, type=int)
@click.argument('properties',nargs=-1)
def modify(ctx: click.Context, identifier: int, properties: List[str]) ->  None:

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        fail(ctx,"No calendars found. Please check your configuration.")

    todos = cal_db.get_todos(["id:"+str(identifier)])

    if len(todos) == 0:
        fail(ctx,"Invalid identifier " + str(identifier) + ".")

    todo = todos[0]
    try:

        property_changes = decode_raw_arg_list(ctx.obj['config'], properties)
        todo.set_properties(property_changes)

        cal_name = str(todo.get_context()['calendar'])
        todo_id = str(todo.get_context()['id'])

        cal_db.write_todo(cal_name, todo.get_ical_todo())
    except Exception as err:
        fail(ctx,str(err))
    success("Successfully modified todo " + todo_id + ".")

@run_cli.command()
@click.pass_context
@click.argument('report',nargs=1,default="default")
@click.argument('constraints',nargs=-1)
def show(ctx: click.Context, report: str, constraints: List[str]) -> None:

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        fail(ctx,"No calendars found. Please check your configuration.")

    # Check if the report exists
    # and if it exists, extract columns
    # and constraints
    reports = ctx.obj['config'].get_config(['reports'])

    report_expanded = expand_prefix(report, reports.keys())

    if report_expanded == "":
        ctx.fail("Unknown or ambiguous report name \"" + report + "\". Known reports are " + ", ".join(reports.keys()) + ".")

    if 'constraint' in reports[report_expanded]:
        if len(constraints) > 0:
            constraints = [c for c in constraints] + ['and'] + reports[report_expanded]['constraint'].split(" ")
        else:
            constraints = reports[report_expanded]['constraint'].split(" ")

    try:
        todos = cal_db.get_todos(constraints)
        todos = ToDoSorter(todos, "due").get_sorted()

        row_limit = len(todos)

        if 'max_list_length' in reports[report_expanded]:
            row_limit = min(reports[report_expanded]['max_list_length'], row_limit)

        formatter = StringFormatter(ctx.obj['config'])
        tagger = DueDateBasedTagger(todos, datetime.timedelta(days=7), datetime.timedelta(days=1))
        view = TabularToDoListView(ctx.obj['config'], report_expanded, todos, formatter, tagger)
        view.show()
        hint("Showing " + str(row_limit) + " out of " + str(len(todos)) + " todos.")
    except Exception as err:
        fail(ctx,str(err))

@run_cli.command()
@click.pass_context
@click.argument('ids',nargs=-1,required=True)
def done(ctx: click.Context, ids: List[str]) -> None:

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        fail(ctx,"No calendars found. Please check your configuration.")

    # first, check if all ids are valid
    pending_todos = []
    for i in ids:
        todos = cal_db.get_todos(["id:"+i])

        if len(todos) == 0:
            fail(ctx,"Invalid identifier " + i + ".")

        pending_todos.append(todos[0])

    try:
        for todo in pending_todos:
            todo.set_properties({
                'status': 'COMPLETED', 
                'percent-complete': 100, 
                'completed': datetime.datetime.now()})
            todo_id = todo.get_context()['id']
            cal_db.write_todo(str(todo.get_context()['calendar']), todo.get_ical_todo())
            success("Set status of todo " + str(todo_id) + " to COMPLETED.")
    except Exception as err:
        fail(ctx, str(err))


@run_cli.command()
@click.pass_context
@click.argument('ids',nargs=-1,required=True)
def delete(ctx: click.Context, ids: List[str]) -> None:

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        fail(ctx,"No calendars found. Please check your configuration.")

    constraints : List[str] = []
    for idnum in ids:

        if len(constraints) != 0:
            constraints.append("or")
        constraints.append("id:" + idnum)

    try:
       todos = cal_db.get_todos(constraints)
    except Exception as err:
        fail(ctx,str(err))

    if len(todos) != len(ids):
        fail(ctx,"At least one identifier is unknown.")

    for todo in todos:
        try:
            if click.confirm('Delete todo ' + str(todo.get_context()['id']) + ' "' + todo.get_string('summary') + '"?'):
                cal_db.delete_todo(todo.get_ical_todo())
                success("Successfully deleted todo " + str(todo.get_context()['id']))
        except Exception as err:
            fail(ctx,str(err))

@run_cli.command()
@click.pass_context
@click.argument('identifier',type=int,required=True)
@click.argument('source',required=True)
@click.argument('destination',required=True)
def move(ctx: click.Context, identifier: int, source: str, destination: str) -> None:

    cal_db = Calendars(ctx.obj['config'])

    if source not in cal_db.get_calendars():
        fail(ctx,"Unknown calendar \"" + source +"\".")

    if destination not in cal_db.get_calendars():
        fail(ctx,"Unknown calendar \"" + destination +"\".")

    constraints = ["id:" + str(identifier)]

    try:
       todos = cal_db.get_todos(constraints)
    except Exception as err:
        fail(ctx,str(err))

    if len(todos) == 0:
        fail(ctx,"No todo with identifier " + str(identifier) + " has been found.")

    try:
        cal_db.move_todo(todos[0].get_string('uid'), source, destination)
    except Exception as err:
        fail(ctx,str(err))
    success("Successfully moved todo to calendar " + destination)

@run_cli.command()
@click.pass_context
@click.argument('identifier',nargs=1,required=True, type=int)
def info(ctx: click.Context, identifier: int) -> None:

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        fail(ctx,"No calendars found. Please check your configuration.")

    try:
        todos = cal_db.get_todos(['id:' + str(identifier)])
    except Exception as err:
        fail(ctx,str(err))

    if len(todos) < 1:
        fail(ctx,"Unknown identifier.")

    formatter = StringFormatter(ctx.obj['config'])
    todoView = TabularToDoView(ctx.obj['config'], todos[0], formatter)
    todoView.show()

@run_cli.command()
@click.pass_context
@click.argument('identifier',nargs=1,required=True, type=int)
def description(ctx: click.Context, identifier: int) -> None:

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        fail(ctx,"No calendars found. Please check your configuration.")

    try:
        todos = cal_db.get_todos(['id:' + str(identifier)])
    except Exception as err:
        fail(ctx,str(err))

    if len(todos) < 1:
        fail(ctx, "Unknown identifier.")

    todo = todos[0]

    # Create temporary text file
    # Set delete to False, so that we can close
    # the file without it being deleted and then re-open it
    # with a text editor.
    tmp_file = NamedTemporaryFile(delete=False)
    tmp_file_path = os.path.join(gettempdir(), tmp_file.name)

    # If the todo has a description already, write it into the text file
    if todo.has_property("description"):
        tmp_file.write(todo.get_string('description').encode('utf-8'))

    tmp_file.close()

    # Open the text file using the system editor
    default_editor = os.getenv('EDITOR')
    if default_editor is None:
        default_editor = "xdg-open"

    subprocess.call([default_editor, tmp_file_path])

    if click.confirm('Shall the new description be used?'):
        desc_file = open(tmp_file_path, 'r')
        new_desc = str(desc_file.read())
        desc_file.close()

        if todo.has_property("description"):
            todo.unset_property("description")

        todo.set_properties({'description' : new_desc})
        cal_name = str(todo.get_context()['calendar'])
        cal_db.write_todo(cal_name, todo.get_ical_todo())
        success("Successfully updated description.")

    os.remove(tmp_file_path)

@run_cli.command()
@click.pass_context
@click.argument('expr',nargs=1,required=True)
def calculate(ctx: click.Context, expr: str) -> None:
    try:
        result = decode_date(expr, ctx.obj['config'])
    except Exception as err:
        fail(ctx,str(err))
    print(result.strftime(ctx.obj['config'].get_datetime_format()))


@run_cli.command()
@click.pass_context
@click.argument('calendar',required=True)
def cleanup(ctx: click.Context, calendar: str) -> None:

    cal_db = Calendars(ctx.obj['config'])
    if calendar not in cal_db.get_calendars():
        fail(ctx,"Calendar + " + calendar + " not found. Please check your configuration.")

    try:
        todos = cal_db.get_todos(["calendar:"+calendar, "and", "status:completed"])
    except Exception as err:
        fail(ctx,str(err))

    if len(todos) == 0:
        hint("No completed todos found in calendar " + calendar + ".")
    else:
        if click.confirm('Delete ' + str(len(todos)) + ' completed todos from calendar ' + calendar +'?'):
            for todo in todos:
                try:
                    cal_db.delete_todo(todo.get_ical_todo())
                except Exception as err:
                    fail(ctx,str(err))
                success("Successfully deleted todo " + str(todo.get_context()['id']))

        else:
            hint("No todos deleted from " + calendar + ".")

@run_cli.command()
@click.pass_context
@click.argument('constraints',nargs=-1)
def export(ctx: click.Context, constraints: List[str]) -> None:

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        fail(ctx,"No calendars found. Please check your configuration.")

    try:
       todos = cal_db.get_todos(constraints)
    except Exception as err:
        fail(ctx,str(err))

    objects = []

    formatter = StringFormatter(ctx.obj['config'])

    for todo in todos:
        obj = {}
        for prop_name in todo.get_property_names():
            obj[prop_name] = formatter.format_property_value(prop_name, todo)

        objects.append(obj)

    click.echo(json.dumps(objects))
