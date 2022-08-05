# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os.path
import os
import subprocess
from tempfile import NamedTemporaryFile, gettempdir

from typing import List, Optional

import json
import click
import colorama
import tableformatter
import datetime
from termcolor import colored
from icalwarrior.configuration import Configuration
from icalwarrior.model.items import TodoModel
from icalwarrior.model.lists import TodoDatabase
from icalwarrior.input.date import expand_prefix, decode_date, DATE_SYNONYMS, DATE_FORMULA_UNITS
from icalwarrior.input.cli import decode_property_list
from icalwarrior.view.formatter import StringFormatter
from icalwarrior.view.tagger import DueDateBasedTagger
from icalwarrior.view.tabular import TabularToDoListView, TabularPrinter, TabularToDoView
from icalwarrior.view.sorter import ToDoSorter
from icalwarrior.filtering.constraints import ConstraintEvaluator

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

def display_change_warning() -> None:
    hint("The ID assigned to one or more other tasks may have changed.")
    hint("Consider requesting another report before performing further actions.")

@click.group(cls=CommandAliases)
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

@run_cli.command(short_help="Show summary statistics about the lists icalwarrior is aware of.")
@click.pass_context
def lists(ctx: click.Context) -> None:
    config = ctx.obj['config']

    try:
        cal = TodoDatabase(config)

        cols = ["Name", "Path", "Total number of todos", "Number of completed todos"]
        rows : List[List[str]] = []

        cal_db = TodoDatabase(config)
        for name in cal.get_list_names():
            path = os.path.join(config.get_lists_dir(), name)
            todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["list:" + name]))
            completed_todos = cal_db.get_todos(
                ConstraintEvaluator.from_string_list(
                    config, ["list:" + name, "and", "status:completed"]))
            rows.append([name, path, str(len(todos)), str(len(completed_todos))])

        printer = TabularPrinter(rows, cols, 0, tableformatter.WrapMode.WRAP, None)
        printer.print()
    except Exception as err:
        fail(ctx, str(err))

@run_cli.command(short_help="Create a new empty todo list")
@click.pass_context
@click.argument('list_name', nargs=1, required=True)
def newlist(ctx: click.Context, list_name : str) -> None:
    config = ctx.obj['config']

    try:
        cal_db = TodoDatabase(config)
        cal_db.add_list(list_name)

        success("Successfully created list " + list_name + ".")
    except Exception as err:
        fail(ctx, str(err))

@run_cli.command(short_help="Remove an existing todo list")
@click.pass_context
@click.argument('list_name', nargs=1, required=True)
def droplist(ctx: click.Context, list_name : str) -> None:
    config = ctx.obj['config']

    try:
        cal_db = TodoDatabase(config)
        cal_db.delete_list(list_name)
        success("Successfully removed list " + list_name +".")
        display_change_warning()
    except Exception as err:
        fail(ctx, str(err))

@run_cli.command(short_help="Add a new todo item to a list.")
@click.pass_context
@click.argument('list_name', nargs=1, required=True)
@click.argument('summary', nargs=1, required=True)
@click.argument('properties', nargs=-1)
def add(ctx: click.Context, list_name: str, summary: str, properties: List[str]) -> None:
    config = ctx.obj['config']

    try:
        cal_db = TodoDatabase(config)

        if len(cal_db.get_list_names()) == 0:
            fail(ctx, "No lists found. Please check your configuration.")

        full_list_name = expand_prefix(list_name, cal_db.get_list_names())
        if full_list_name == "":
            fail(ctx, "Unknown list name or prefix \"" + list_name + ". Known lists are " + ", ".join(cal_db.get_list_names()) + ".")

        if len(summary) == 0:
            fail(ctx, "Summary text must be non-empty.")

        todo = TodoModel(config, cal_db.create_todo())
        property_dict = decode_property_list(config, ['summary:' + summary, 'status:needs-action'] + [p for p in properties])
        todo.set_properties(property_dict)
        cal_db.get_list(full_list_name).add(todo.get_ical_todo())

        assert todo is not None
        # Re-read lists to trigger id generation of todo
        uid = todo.get_string('uid')
        cal_db = TodoDatabase(config)
        todo = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["uid:" + uid]))[0]

        success("Successfully created new todo \"" + todo.get_string('summary') + "\" with ID " + str(todo.get_context("id")) + ".")
        display_change_warning()
    except Exception as err:
        fail(ctx, str(err))

@run_cli.command(short_help="Modify an existing todo item.")
@click.pass_context
@click.argument('identifier', nargs=1, type=int)
@click.argument('properties',nargs=-1)
def modify(ctx: click.Context, identifier: int, properties: List[str]) ->  None:
    config = ctx.obj['config']

    try:

        cal_db = TodoDatabase(config)
        if len(cal_db.get_list_names()) == 0:
            fail(ctx,"No lists found. Please check your configuration.")

        todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["id:"+str(identifier)]))

        if len(todos) == 0:
            fail(ctx,"Invalid identifier " + str(identifier) + ".")

        todo = todos[0]
        property_changes = decode_property_list(config, properties)
        todo.set_properties(property_changes)

        cal_name = str(todo.get_context('list'))
        todo_id = str(todo.get_context('id'))

        cal_db.get_list(cal_name).add(todo.get_ical_todo())
        success("Successfully modified todo " + todo_id + ".")

    except Exception as err:
        fail(ctx, str(err))

@run_cli.command(short_help="Print a given report defined in the configuration file.")
@click.pass_context
@click.argument('name',nargs=1,default="default")
@click.argument('constraints',nargs=-1)
def report(ctx: click.Context, name: str, constraints: List[str]) -> None:
    config = ctx.obj['config']

    try:

        cal_db = TodoDatabase(config)
        if len(cal_db.get_list_names()) == 0:
            fail(ctx,"No lists found. Please check your configuration.")

        # Check if the report exists
        # and if it exists, extract columns
        # and constraints
        reports = config.get_config(['reports'])

        report_expanded = expand_prefix(name, reports.keys())

        if report_expanded == "":
            ctx.fail("Unknown or ambiguous report name \"" + name + "\". Known reports are " + ", ".join(reports.keys()) + ".")

        if 'constraint' in reports[report_expanded]:
            if len(constraints) > 0:
                constraints = [c for c in constraints] + ['and'] + reports[report_expanded]['constraint'].split(" ")
            else:
                constraints = reports[report_expanded]['constraint'].split(" ")

        constraint_evaluator = ConstraintEvaluator.from_string_list(config, constraints)
        todos = cal_db.get_todos(constraint_evaluator)
        todos = ToDoSorter(todos, "due").get_sorted()

        row_limit = len(todos)

        if 'max_list_length' in reports[report_expanded]:
            row_limit = min(reports[report_expanded]['max_list_length'], row_limit)

        formatter = StringFormatter(config)
        tagger = DueDateBasedTagger(todos, datetime.timedelta(days=7), datetime.timedelta(days=1))
        view = TabularToDoListView(config, report_expanded, todos, formatter, tagger)
        view.show()
        hint("Showing " + str(row_limit) + " out of " + str(len(todos)) + " todos.")

    except Exception as err:
        fail(ctx,str(err))

@run_cli.command(short_help="Mark one or more todo items as done.")
@click.pass_context
@click.argument('ids',nargs=-1,required=True)
def done(ctx: click.Context, ids: List[str]) -> None:
    config = ctx.obj['config']

    try:

        cal_db = TodoDatabase(config)
        if len(cal_db.get_list_names()) == 0:
            fail(ctx,"No lists found. Please check your configuration.")

        # first, check if all ids are valid
        pending_todos = []
        for i in ids:
            todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["id:"+i]))

            if len(todos) == 0:
                fail(ctx,"Invalid identifier " + i + ".")

            pending_todos.append(todos[0])

        for todo in pending_todos:
            todo.set_properties({
                'status': 'COMPLETED', 
                'percent-complete': 100, 
                'completed': datetime.datetime.now()})
            todo_id = todo.get_context('id')
            cal_db.get_list(str(todo.get_context('list'))).add(todo.get_ical_todo())
            success("Set status of todo " + str(todo_id) + " to COMPLETED.")

    except Exception as err:
        fail(ctx, str(err))


@run_cli.command(short_help="Delete a todo item.")
@click.pass_context
@click.argument('ids',nargs=-1,required=True)
def delete(ctx: click.Context, ids: List[str]) -> None:
    config = ctx.obj['config']

    try:

        cal_db = TodoDatabase(config)
        if len(cal_db.get_list_names()) == 0:
            fail(ctx,"No lists found. Please check your configuration.")

        constraints : List[str] = []
        for idnum in ids:

            if len(constraints) != 0:
                constraints.append("or")
            constraints.append("id:" + idnum)

        todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, constraints))

        if len(todos) != len(ids):
            fail(ctx,"At least one identifier is unknown.")

        for todo in todos:
            if click.confirm('Delete todo ' + str(todo.get_context('id')) + ' "' + todo.get_string('summary') + '"?'):
                cal_db.get_list(str(todo.get_context('list'))).delete(todo.get_ical_todo())
                success("Successfully deleted todo " + str(todo.get_context('id')))

        display_change_warning()

    except Exception as err:
        fail(ctx,str(err))

@run_cli.command(short_help="Move a todo item from one list to another.")
@click.pass_context
@click.argument('identifier',type=int,required=True)
@click.argument('destination',required=True)
def move(ctx: click.Context, identifier: int, destination: str) -> None:
    config = ctx.obj['config']

    try:

        cal_db = TodoDatabase(ctx.obj['config'])

        if destination not in cal_db.get_list_names():
            fail(ctx,"Unknown list \"" + destination +"\".")

        constraints = ["id:" + str(identifier)]

        todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, constraints))
        if len(todos) == 0:
            fail(ctx,"No todo with identifier " + str(identifier) + " has been found.")

        todo = todos[0]
        source = str(todo.get_context('list'))
        cal_db.get_list(source).delete(todo.get_ical_todo())
        cal_db.get_list(destination).add(todo.get_ical_todo())

        success("Successfully moved todo to list " + destination)
        display_change_warning()
    except Exception as err:
        fail(ctx,str(err))

@run_cli.command(short_help="Print a summary of a single todo item.")
@click.pass_context
@click.argument('identifier',nargs=1,required=True, type=int)
def show(ctx: click.Context, identifier: int) -> None:
    config = ctx.obj['config']

    try:

        cal_db = TodoDatabase(config)
        if len(cal_db.get_list_names()) == 0:
            fail(ctx,"No lists found. Please check your configuration.")

        todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ['id:' + str(identifier)]))

        if len(todos) < 1:
            fail(ctx,"Unknown identifier.")

        formatter = StringFormatter(config)
        todo_view = TabularToDoView(config, todos[0], formatter)
        todo_view.show()

    except Exception as err:
        fail(ctx, str(err))

@run_cli.command(short_help="Change the description text of a todo item.")
@click.pass_context
@click.argument('identifier',nargs=1,required=True, type=int)
def description(ctx: click.Context, identifier: int) -> None:
    config = ctx.obj['config']

    try:

        cal_db = TodoDatabase(config)
        if len(cal_db.get_list_names()) == 0:
            fail(ctx,"No lists found. Please check your configuration.")

        todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ['id:' + str(identifier)]))

        if len(todos) < 1:
            fail(ctx, "Unknown identifier.")

        todo = todos[0]

        # Set delete to False, so that we can close
        # the file without it being deleted and then re-open it
        # with a text editor.
        tmp_file = NamedTemporaryFile(delete=False)
        tmp_file_path = os.path.join(gettempdir(), tmp_file.name)

        if todo.has_property("description"):
            tmp_file.write(todo.get_string('description').encode('utf-8'))

        tmp_file.close()

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
            list_name = str(todo.get_context('list'))
            cal_db.get_list(list_name).add(todo.get_ical_todo())
            success("Successfully updated description.")

        os.remove(tmp_file_path)

    except Exception as err:
        fail(ctx,str(err))

@run_cli.command(short_help="Perform date calculations.")
@click.pass_context
@click.argument('expr',nargs=1,required=True)
def calculate(ctx: click.Context, expr: str) -> None:
    config = ctx.obj['config']
    try:
        result = decode_date(expr, config)
    except Exception as err:
        fail(ctx,str(err))
    print(result.strftime(config.get_datetime_format()))


@run_cli.command(short_help="Delete all completed todo items in a given list.")
@click.pass_context
@click.argument('list',required=True)
def cleanup(ctx: click.Context, list_name: str) -> None:
    config = ctx.obj['config']

    try:

        any_change_performed = False
        cal_db = TodoDatabase(config)
        if list_name not in cal_db.get_list_names():
            fail(ctx,"List + " + list_name + " not found. Please check your configuration.")

        todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, ["list:" + list_name, "and", "status:completed"]))
        if len(todos) == 0:
            hint("No completed todos found in list " + list_name + ".")
        else:
            if click.confirm('Delete ' + str(len(todos)) + ' completed todos from list ' + list_name + '?'):
                for todo in todos:
                    cal_db.get_list(str(todo.get_context('list'))).delete(todo.get_ical_todo())
                    success("Successfully deleted todo " + str(todo.get_context('id')))
                    any_change_performed = True

            else:
                hint("No todos deleted from " + list_name + ".")

        if any_change_performed:
            display_change_warning()
    except Exception as err:
        fail(ctx, str(err))

@run_cli.command(short_help="Print a JSON representation of all todos satisfying a given filter expression.")
@click.pass_context
@click.argument('constraints',nargs=-1)
def export(ctx: click.Context, constraints: List[str]) -> None:
    config = ctx.obj['config']

    try:

        cal_db = TodoDatabase(config)
        if len(cal_db.get_list_names()) == 0:
            fail(ctx,"No lists found. Please check your configuration.")

        todos = cal_db.get_todos(ConstraintEvaluator.from_string_list(config, constraints))

        objects = []

        formatter = StringFormatter(ctx.obj['config'])

        for todo in todos:
            obj = {}
            for prop_name in todo.get_property_names():
                obj[prop_name] = formatter.format_property_value(prop_name, todo)

            objects.append(obj)

        click.echo(json.dumps(objects))

    except Exception as err:
        fail(ctx,str(err))

@run_cli.group(short_help="Show further information about specific aspects of icalwarrior.", cls=CommandAliases)
def info() -> None:
    pass

@info.command(short_help="Shows properties that can be set using the 'add' or 'modify' command.")
def properties() -> None:
    columns = ["Property", "Allowed values"]
    rows = []
    for prop in TodoModel.supported_properties():
        if prop in TodoModel.DATE_PROPERTIES:
            rows += [[prop, "Any date"]]
        elif prop in TodoModel.TEXT_PROPERTIES:
            rows += [[prop, "Any text"]]
        elif prop in TodoModel.INT_PROPERTIES:
            rows += [[prop, "Any integer"]]
        elif prop in TodoModel.ENUM_PROPERTIES:
            rows += [[prop, ", ".join(TodoModel.ENUM_VALUES[prop])]]

    output = TabularPrinter(rows, columns, 0, tableformatter.WrapMode.WRAP, None)
    output.print()

@info.command(short_help="Shows properties together with the corresponding operators that can be used for filtering.")
def filter() -> None:
    columns = ["Property", "Supported filter operators"]
    rows = []
    for prop in ConstraintEvaluator.supported_filter_properties():
        if prop in TodoModel.DATE_PROPERTIES:
            rows += [[prop, ", ".join(ConstraintEvaluator.DATE_OPERATORS.keys())]]
        elif prop in TodoModel.TEXT_PROPERTIES or prop in ConstraintEvaluator.TEXT_FILTER_PROPERTIES or prop in TodoModel.ENUM_PROPERTIES:
            rows += [[prop, ", ".join(ConstraintEvaluator.TEXT_OPERATORS.keys())]]
        elif prop in TodoModel.INT_PROPERTIES or prop in ConstraintEvaluator.INT_FILTER_PROPERTIES:
            rows += [[prop, ", ".join(ConstraintEvaluator.INT_OPERATORS.keys())]]

    output = TabularPrinter(rows, columns, 0, tableformatter.WrapMode.WRAP, None)
    output.print()

@info.command(short_help="Shows relative date specifications and calculation units")
def dates() -> None:

    columns = ["Type", "Supported values"]
    rows = [["Relative date specificiations", ", ".join(DATE_SYNONYMS)],
            ["Date calculation units", ", ".join(DATE_FORMULA_UNITS)]]

    output = TabularPrinter(rows, columns, 0, tableformatter.WrapMode.WRAP, None)
    output.print()

@info.command(short_help="Shows information related to defining reports")
def reports() -> None:
    pass