from typing import List, Set, Union
import tableformatter
from colorama import init, Fore, Back, Style
import icalendar
import datetime
import humanize
import dateutil.tz as tz

from icalwarrior.todo import Todo
from icalwarrior.configuration import Configuration

class ReportGrid(tableformatter.Grid):

    def __init__(self):
        super().__init__()
        self.show_header = True
        self.border_top = False

        self.border_top_left = '╔'
        self.border_top_span = '═'
        self.border_top_right = '╗'
        self.border_top_col_divider = '╤'
        self.border_top_header_col_divider = '╦'

        self.border_header_divider = True
        self.border_left_header_divider = ''
        self.border_right_header_divider = ''
        self.border_header_divider_span = '─'
        self.border_header_col_divider = '╪'
        self.border_header_header_col_divider = '╬'

        self.border_left = True
        self.border_left_row_divider = ''

        self.border_right = True
        self.border_right_row_divider = ''

        self.col_divider = False
        self.row_divider = False
        self.row_divider_span = '─'

        self.row_divider_col_divider = '┼'
        self.row_divider_header_col_divider = '╫'

        self.border_bottom = False
        self.border_bottom_left = '╚'
        self.border_bottom_right = '╝'
        self.border_bottom_span = '═'
        self.border_bottom_col_divider = '╧'
        self.border_bottom_header_col_divider = '╩'

        self.bg_reset = Style.RESET_ALL
        self.bg_primary = Style.RESET_ALL
        self.bg_alt = Back.BLACK

    def border_left_span(self, row_index: Union[int, None]) -> str:
        color = self.bg_primary
        if isinstance(row_index, int) and row_index % 2 == 0:
                color = self.bg_alt
        return color

    def border_right_span(self, row_index: Union[int, None]) -> str:
        return self.bg_reset

    def col_divider_span(self, row_index: Union[int, None]) -> str:
        return '│'

    def header_col_divider_span(self, row_index: Union[int, None]) -> str:
        return '║'

def format_property_name(prop_name : str) -> str:

    property_aliases = {

        'dtstart' : 'starts',
        'dtend' : 'ends'

    }

    result = property_aliases.get(prop_name, prop_name).capitalize()

    return result


def format_property_value(config : Configuration, prop_name : str, todo : icalendar.Todo) -> str:

    result = ""

    if prop_name in todo or prop_name in todo['context']:
        if prop_name in Todo.DATE_PROPERTIES + Todo.DATE_IMMUTABLE_PROPERTIES:
            prop_value = todo[prop_name]
            # Use vDDDTypes here as this is the default format for dates read by icalendar
            prop_date = icalendar.vDDDTypes.from_ical(prop_value)
            result = prop_date.strftime(config.get_datetime_format())

            now = datetime.datetime.now(tz.gettz())
            result += " (" + humanize.naturaldelta(now - prop_date) + ")"

        elif prop_name in Todo.TEXT_PROPERTIES + Todo.TEXT_IMMUTABLE_PROPERTIES:
            prop_value = todo[prop_name]
            if isinstance(prop_value, icalendar.prop.vCategory):
                result = ", ".join(prop_value.cats)
            else:
                result = prop_value

        elif prop_name in Todo.INT_PROPERTIES:
            prop_value = icalendar.vInt.from_ical(todo[prop_name])
            result = prop_value

        elif prop_name in Todo.ENUM_PROPERTIES:
            prop_value = todo[prop_name]
            result = prop_value

        elif prop_name in Todo.TEXT_FILTER_PROPERTIES:
            prop_value = todo['context'][prop_name]
            result = prop_value

        elif prop_name in Todo.INT_FILTER_PROPERTIES:
            prop_value = todo['context'][prop_name]
            result = prop_value

    return result

def print_todo(config : Configuration, todo : icalendar.Todo) -> None:

    property_order = ['summary', 'created', 'due', 'uid', 'status', 'categories', 'calendar']

    cols = ["Property", "Value"]

    rows = []
    for prop in property_order:
        rows.append([format_property_name(prop), format_property_value(config, prop, todo)])

    print_table(rows, cols)


def print_table(rows : List[object], columns : List[str]) -> None:

    print(tableformatter.generate_table(
        rows,
        columns,
        grid_style=ReportGrid()))
