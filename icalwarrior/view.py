from typing import List, Set, Union
import tableformatter
from colorama import init, Fore, Back, Style
import icalendar
import datetime
import humanize
import dateutil.tz as tz

from icalwarrior.todo import Todo
from icalwarrior.configuration import Configuration
from icalwarrior.util import adapt_datetype

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

    if prop_name in todo:

        type_fact = icalendar.prop.TypesFactory()

        if type_fact.for_property(prop_name) is icalendar.prop.vDDDTypes:
            # Use vDDDTypes here as this is the default format for dates read by icalendar
            prop_value = icalendar.prop.vDDDTypes.from_ical(todo[prop_name])
            result = prop_value.strftime(config.get_datetime_format())

            now = adapt_datetype(datetime.datetime.now(tz.gettz()), prop_value)
            result += " (" + humanize.naturaldelta(now - prop_value) + ")"

        elif type_fact.for_property(prop_name) is icalendar.prop.vText:
            prop_value = icalendar.prop.vText.from_ical(todo[prop_name])
            result = prop_value

        elif type_fact.for_property(prop_name) is icalendar.prop.vInt:
            prop_value = icalendar.vInt.from_ical(todo[prop_name])
            result = prop_value

        elif type_fact.for_property(prop_name) is icalendar.prop.vCategory:
            # TODO: from_ical vom vCategory throws an assertion error.
            #       We therefore convert it manually.
            prop_value = ",".join([str(c) for c in todo[prop_name].cats])
            result = prop_value

    if prop_name in todo['context']:

        if prop_name in Todo.TEXT_FILTER_PROPERTIES:
            prop_value = todo['context'][prop_name]
            result = prop_value

        elif prop_name in Todo.INT_FILTER_PROPERTIES:
            prop_value = todo['context'][prop_name]
            result = prop_value

    return result

def print_todo(config : Configuration, todo : icalendar.Todo) -> None:

    property_order = config.get_config(['info_columns']).split(",")

    cols = ["Property", "Value"]

    rows = []
    for prop in property_order:
        rows.append([format_property_name(prop), format_property_value(config, prop, todo)])

    print_table(rows, cols)

def print_table(rows : List[object], columns : List[str], max_col_width = 0) -> None:

    # Add single newline at the beginning
    # to make output more readable
    print()

    formatted_cols = columns
    if max_col_width > 0:
        formatted_cols = [tableformatter.Column(col, width=max_col_width, wrap_mode=tableformatter.WrapMode.TRUNCATE_END) for col in columns]

    print(tableformatter.generate_table(
        rows,
        formatted_cols,
        grid_style=ReportGrid()))
