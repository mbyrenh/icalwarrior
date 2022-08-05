# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Union, Callable, Optional, Dict
import tableformatter
from colorama import Back, Style

from icalwarrior.view.formatter import StringFormatter
from icalwarrior.view.tagger import Tagger
from icalwarrior.model.items import TodoModel
from icalwarrior.configuration import Configuration

class ReportGrid(tableformatter.Grid):

    def __init__(self) -> None:
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
        self.border_header_col_divider = '─'
        self.border_header_header_col_divider = '╬'

        self.border_left = True
        self.border_left_row_divider = ''

        self.border_right = True
        self.border_right_row_divider = ''

        self.col_divider = True
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
        color = self.bg_primary
        if isinstance(row_index, int) and row_index % 2 == 0:
            color = self.bg_alt
        return color

    def header_col_divider_span(self, row_index: Union[int, None]) -> str:
        return '║'

class InvalidReportError(Exception):

    def __init__(self, report_name : str, error_msg : str) -> None:
        self.report_name = report_name
        self.error_msg = error_msg

    def __str__(self) -> str:
        return ("Invalid report \"" + self.report_name + "\": " + self.error_msg)

class TabularPrinter:

    def __init__(self,
                 rows : List[List[str]],
                 columns : List[str],
                 max_column_width : int,
                 wrap_mode : tableformatter.WrapMode,
                 row_tagger : Optional[Callable[[List[str]], Dict[str,int]]]) -> None:
        self.columns = columns
        self.max_column_width = max_column_width
        self.wrap_mode = wrap_mode
        self.rows = rows
        self.tagger = row_tagger

    def print(self) -> None:
        # Add single newline at the beginning
        # to make output more readable
        print()

        formatted_cols = self.columns
        if self.max_column_width > 0:
            formatted_cols = [
                tableformatter.Column(
                    col,
                    width=self.max_column_width,
                    wrap_mode=self.wrap_mode)
                for col in self.columns]

        print(tableformatter.generate_table(
            self.rows,
            formatted_cols,
            grid_style=ReportGrid(),
            row_tagger=self.tagger))

class TabularToDoListView:

    def __init__(
        self,
        config : Configuration,
        report_name : str,
        todos : List[TodoModel],
        property_formatter : StringFormatter,
        row_tagger : Tagger) -> None:

        self.config = config
        self.report_name = report_name
        self.property_formatter = property_formatter
        self.row_tagger = row_tagger
        self.todos = todos

    def show(self) -> None:

        report_config = self.config.get_config(['reports', self.report_name])

        if "columns" not in report_config:
            raise InvalidReportError(self.report_name, "No columns specified for report.")

        columns = ["id"] + report_config['columns'].split(",")

        # Check if a maximum number of entries has been configured
        row_limit = len(self.todos)
        max_column_width = 0
        try:
            if 'max_list_length' in report_config:
                row_limit = min(report_config['max_list_length'], row_limit)

            if 'max_column_width' in report_config:
                max_column_width = int(report_config['max_column_width'])

        except KeyError:
            pass

        rows = []

        for i in range(row_limit):
            row = []
            for column in columns:
                row.append(self.property_formatter.format_property_value(column, self.todos[i]))

            rows.append(row)

        columns = [self.property_formatter.format_property_name(col) for col in columns]

        printer = TabularPrinter(rows, columns, max_column_width, tableformatter.WrapMode.TRUNCATE_END, self.row_tagger.tag)
        printer.print()

class TabularToDoView:

    def __init__(self, config : Configuration, todo : TodoModel, formatter : StringFormatter) -> None:
        self.config = config
        self.todo = todo
        self.formatter = formatter

    def show(self) -> None:

        property_order = self.config.get_config(['info_columns']).split(",")

        cols = ["Property", "Value"]

        rows = []
        for prop in property_order:

            if self.todo.has_property(prop):

                rows.append(
                    [
                        self.formatter.format_property_name(prop),
                        self.formatter.format_property_value(prop, self.todo)
                    ])

        printer = TabularPrinter(rows, cols, 0, tableformatter.WrapMode.TRUNCATE_END, None)
        printer.print()

