import sys
from datetime import datetime
import uuid
import os.path

from typing import List

import icalendar
import click
from icalwarrior.args import arg_type, ArgType
from icalwarrior.configuration import Configuration
from icalwarrior.calendars import Calendars
from icalwarrior.todo import Todo
from icalwarrior.util import expand_prefix

class InvalidArgumentException(Exception):

    def __init__(self, arg_name :str, supported : List[str]) -> None:
        self.arg_name = arg_name
        self.supported = supported

    def __str__(self):
        return ("Unknown property '" + self.arg_name + "'. Supported properties are " + ",".join(self.supported))

DEFAULT_COMMAND = 'show'

class CommandAliases(click.Group):

    def get_command(self,ctx,cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv

        cmd = expand_prefix(cmd_name, self.list_commands(ctx))
        if cmd != "":
            return click.Group.get_command(self, ctx, cmd)
        ctx.fail('Invalid command "%s"' % cmd_name)

@click.command(cls=CommandAliases)
@click.option('-c', '--config', default=Configuration.get_default_config_path(), help='Path to the configuration file')
@click.pass_context
def run_cli(ctx, config):

    try:
        configuration = Configuration(config)

        ctx.ensure_object(dict)
        ctx.obj['config'] = configuration
    except FileNotFoundError:
        print("Unable to find configuration file " + config)
        sys.exit(1)
    except PermissionError:
        print("Missing permissions to open configuration file " + config)
        sys.exit(1)

@run_cli.command()
@click.pass_context
def calendars(ctx):
    cal = Calendars(ctx.obj['config'])

    for name in cal.get_calendars():
        path = os.path.join(ctx.obj['config'].get_calendar_dir(),name)
        print(name + " - " + path)


@run_cli.command()
@click.pass_context
@click.argument('calendar', nargs=1)
@click.argument('summary', nargs=1)
@click.argument('properties',nargs=-1)
def add(ctx, calendar, summary, properties):

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        print("No calendars found. Please check your configuration.")
        sys.exit(1)

    if not cal_db.calendarExists(calendar):
        print("Unknown calendar \"" + calendar + ". Known calendars are " + ", ".join(cal_db.get_calendars()) + ".")
        sys.exit(1)

    todo = icalendar.Todo()

    uid = uuid.uuid4()
    while not cal_db.is_unique_uid(uid):
        uid = uuid.uuid4()

    todo.add('uid', uid)
    todo.add('summary', summary)
    todo.add('status', 'needs-action'.upper())
    now = datetime.now()
    todo.add('dtstamp', now, encode=True)
    todo.add('created', now, encode=True)

    Todo.set_properties(todo, ctx.obj['config'], properties)

    cal_db.write_todo(calendar, todo)

@run_cli.command()
@click.pass_context
@click.argument('identifier', nargs=1, type=int)
@click.argument('properties',nargs=-1)
def mod(ctx, identifier, properties):

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        print("No calendars found. Please check your configuration.")
        sys.exit(1)

    todos = cal_db.get_todos()

    if identifier > len(todos):
        print("Invalid identifier " + identifier + ".")
        sys.exit(1)

    todo = todos[identifier]
    Todo.set_properties(todo, ctx.obj['config'], properties)

    cal_name = cal_db.get_calendar(todo)

    cal_db.write_todo(cal_name, todo)

@run_cli.command()
@click.pass_context
def show(ctx):

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        print("No calendars found. Please check your configuration.")
        sys.exit(1)

    todos = cal_db.get_todos()
    for i in range(len(todos)):
        print(str(i) + " " + todos[i]['summary'] + " " + cal_db.get_calendar(todos[i]))

@run_cli.command()
@click.pass_context
@click.argument('ids',nargs=-1,required=True)
def done(ctx, ids):

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        print("No calendars found. Please check your configuration.")
        sys.exit(1)

    todos = cal_db.get_todos()
    # first, check if all ids are valid
    for i in ids:
        if i > len(todos):
            print("Invalid identifier " + i + ".")
            sys.exit(1)

    for i in ids:
        todo = todos[i]
        cal_name = cal_db.get_calendar(todo)
        todo['status'] = 'completed'.upper()
        cal_db.write_todo(cal_name, todo)


@run_cli.command()
@click.pass_context
@click.argument('ids',nargs=-1,required=True)
def delete(ctx, ids):

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        print("No calendars found. Please check your configuration.")
        sys.exit(1)

    todos = cal_db.get_todos()
    # first, check if all ids are valid
    for i in ids:
        if i > len(todos):
            print("Invalid identifier " + i + ".")
            sys.exit(1)

    for i in ids:
        todo = todos[i]
        cal_db.delete_todo(todo)
