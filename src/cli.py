import sys
from datetime import datetime
import random

from typing import List

import click
from args import arg_type
from configuration import Configuration
from calendars import Calendars
from todo import Todo

class InvalidArgumentException(Exception):

    def __init__(self, arg_name :str, supported : List[str]) -> None:
        self.arg_name = arg_name
        self.supported = supported

    def __str__(self):
        return ("Unknown property '" + self.arg_name + "'. Supported properties are " + ",".join(self.supported))

@click.group(invoke_without_command=True)
@click.option('-c', '--config', default=Configuration.getDefaultConfigPath(), help='Path to the configuration file')
@click.pass_context
def run_cli(ctx, config):

    try:
        print("Config path " + config)
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
@click.argument('calendar', nargs=1)
@click.argument('title', nargs=1)
@click.argument('properties',nargs=-1)
def add(ctx, calendar, title, properties):

    calendars = Calendars(ctx.obj['config'])

    if not calendar in calendars:
        print("Unknown caledar \"" + calendar + ". Known calendars are " + ",".join(calendars))

    for arg in properties:
        argtype = arg_type(arg, Todo.SUPPORTED_PROPERTIES.keys())




#    todo = Todo.fromArgs(args)
#
#    # TODO: Check if a calendar is given and the given calendar exists
#    if (todo.calendarName == None):
#        click.echo('No calendar given to add the todo to.')
#        sys.exit(1)
#    elif (not calendars.calendarExists(todo.calendarName)):
#        click.echo('Unknown calendar "' + todo.calendarName + '". Available calendars are "' + ', "'.join(calendars.getCalendars()) + '".')
#        sys.exit(1)
#    
#    uid = "".join(random.choices([str(i) for i in range(10)], k=24))
#    todo.getIcalTodo().add('uid', uid)
#
#    now = datetime.now()
#    todo.getIcalTodo().add('created', now)
#    todo.getIcalTodo().add('last-modified', now)
#    todo.getIcalTodo().add('status', 'needs-action'.upper())
#
#    todoCal = Calendar()
#    todoCal.add('prodid', itodo.__productname__ + "/" + itodo.__version__)
#    todoCal.add('version', '2.0')
#    todoCal.add_component(todo.getIcalTodo())
#    click.echo("Adding event")
#    click.echo(todoCal.to_ical())
#
#    fh = open(ctx.obj['config'].getCalendarDir() + "/" + todo.getCalendar() + "/" + uid + ".ics", "wb")
#    fh.write(todoCal.to_ical())
#    fh.close()
