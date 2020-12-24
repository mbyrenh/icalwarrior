from typing import List
from datetime import datetime
import icalendar

from icalwarrior.args import arg_type, ArgType
from icalwarrior.util import decode_date
from icalwarrior.configuration import Configuration

class Todo:

    # Each key denotes the parameter name
    # for the command line parameter and the corresponding
    # value denotes the ical property name.
    SUPPORTED_PROPERTIES = {
        'due' : ('due', decode_date)
    }

    """Valid status values for VTODO according
       to RFC 5545, page 92."""
    STATUS_VALUES = ["needs-action", "completed", "in-process", "cancelled"]

    @staticmethod
    def set_properties(todo : icalendar.Todo, config : Configuration, raw_properties : List[str]) -> None:
        # Collect categories in list and add it once to the todo
        # as otherwise, icalendar will add a separate CATEGORIES-line
        # for each category.
        categories = []
        modified = False

        for arg in raw_properties:
            argtype = arg_type(arg, Todo.SUPPORTED_PROPERTIES.keys())

            if argtype == ArgType.CATEGORY:

                categories.append(arg[1:])

            elif argtype == ArgType.PROPERTY:

                col_pos = arg.find(':')
                arg_name = arg[0:col_pos]
                arg_raw_value = arg[col_pos+1:]

                prop_name, conv = Todo.SUPPORTED_PROPERTIES[arg_name]
                arg_value = conv(arg_raw_value, config)
                todo.add(prop_name, arg_value, encode=True)
                modified = True

            elif argtype == ArgType.STRING:

                del todo['summary']
                todo.add('summary', arg)
                modified = True

        if len(categories) > 0:
            todo.add("categories", categories)
            modified = True

        if modified:
            if 'last-modified' in todo:
                del todo['last-modified']
            todo.add('last-modified', datetime.now())

            del todo['dtstamp']
            todo.add('dtstamp', datetime.now())
