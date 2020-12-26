from enum import Enum
from typing import List

from icalwarrior.util import expand_prefix

class ArgType(Enum):
    INT = 1
    PROPERTY = 2
    STRING = 3
    CATEGORY = 4

def arg_type(arg : str, properties : List[str]) -> ArgType:
    result = ArgType.STRING

    if arg.isdigit():
        result = ArgType.INT

    elif (arg.startswith('+') or arg.startswith('-')) and arg[1:].isalnum():
        result = ArgType.CATEGORY

    elif arg.find(':') != -1:
        col_pos = arg.find(':')
        prop = arg[0:col_pos]
        if expand_prefix(prop, properties) != "":
            result = ArgType.PROPERTY

    return result
