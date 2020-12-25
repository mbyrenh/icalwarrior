import sys
from datetime import datetime
import uuid
import os.path
import dateutil.tz as tz

from typing import List

import icalendar
import click
import tableformatter
from icalwarrior.configuration import Configuration
from icalwarrior.calendars import Calendars
from icalwarrior.todo import Todo
from icalwarrior.util import expand_prefix
from icalwarrior.view import print_table, print_todo

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
    now = datetime.now(tz.gettz())
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

    todos = cal_db.get_todos(["id:"+str(identifier)])

    if len(todos) == 0:
        print("Invalid identifier " + identifier + ".")
        sys.exit(1)

    todo = todos[0]
    Todo.set_properties(todo, ctx.obj['config'], properties)

    cal_name = todo['context']['calendar']

    cal_db.write_todo(cal_name, todo)

@run_cli.command()
@click.pass_context
@click.argument('constraints',nargs=-1)
def show(ctx, constraints):

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        print("No calendars found. Please check your configuration.")
        sys.exit(1)

    todos = cal_db.get_todos(constraints)

    columns = ['ID', 'Summary', 'Calendar', 'Status']
    rows = []

    for i in range(len(todos)):
        rows.append((todos[i]['context']['id'], todos[i]['summary'], todos[i]['context']['calendar'], todos[i]['status']))

    print_table(rows, columns)

@run_cli.command()
@click.pass_context
@click.argument('ids',nargs=-1,required=True)
def done(ctx, ids):

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        print("No calendars found. Please check your configuration.")
        sys.exit(1)

    # first, check if all ids are valid
    pending_todos = []
    for i in ids:
        todos = cal_db.get_todos(["id:"+i])

        if len(todos) == 0:
            print("Invalid identifier " + i + ".")
            sys.exit(1)

        pending_todos.append(todos[0])

    for todo in pending_todos:
        todo['status'] = 'completed'.upper()
        cal_db.write_todo(todo['context']['calendar'], todo)


@run_cli.command()
@click.pass_context
@click.argument('ids',nargs=-1,required=True)
def delete(ctx, ids):

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        print("No calendars found. Please check your configuration.")
        sys.exit(1)

    constraints = []
    for idnum in ids:

        if len(constraints) != 0:
            constraints.append("or")
        constraints.append("id:" + idnum)

    todos = cal_db.get_todos(constraints)

    if len(todos) != len(ids):
        print("At least one identifier is unknown.")
        sys.exit(1)

    for todo in todos:
        cal_db.delete_todo(todo)

@run_cli.command()
@click.pass_context
@click.argument('identifier',nargs=1,required=True, type=int)
def info(ctx, identifier):

    cal_db = Calendars(ctx.obj['config'])
    if len(cal_db.get_calendars()) == 0:
        print("No calendars found. Please check your configuration.")
        sys.exit(1)

    todos = cal_db.get_todos(['id:' + str(identifier)])

    if len(todos) < 1:
        print("Unknown identifier.")
        sys.exit(1)

    print_todo(ctx.obj['config'], todos[0])


@run_cli.command()
@click.pass_context
def description(ctx):
    pass
