from typing import List, Set, Union
import tableformatter
from colorama import init, Fore, Back, Style

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

def print_table(rows : List[object], columns : List[str]) -> None:

    print(tableformatter.generate_table(
        rows,
        columns,
        grid_style=ReportGrid()))
