# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum
import datetime
from typing import List, Dict, Union

import icalwarrior.constants as constants
from icalwarrior.input.date import expand_prefix, decode_date, InvalidEnumValueError
from icalwarrior.model.items import TodoModel, UnknownPropertyError
from icalwarrior.configuration import Configuration

class InvalidCategorySpecificationError(Exception):

    def __str__(self) -> str:
        return "You cannot specify categories explicitly and supply category modifiers in the same call."


class ArgType(Enum):
    INT = 1
    PROPERTY = 2
    STRING = 3
    CATEGORY_MODIFIER = 4

def arg_type(arg : str, properties : List[str]) -> ArgType:
    result = ArgType.STRING

    if arg.isdigit():
        result = ArgType.INT

    elif (arg.startswith(constants.CATEGORY_INCLUDE_PREFIX) or arg.startswith(
            constants.CATEGORY_EXCLUDE_PREFIX)) and arg[1:].isalnum():
        result = ArgType.CATEGORY_MODIFIER

    elif arg.find(':') != -1:
        col_pos = arg.find(':')
        prop = arg[0:col_pos]
        if expand_prefix(prop, properties) != "":
            result = ArgType.PROPERTY

    return result

def parse_property_str(config : Configuration, prop_name : str, raw_value : str) -> Union[str, List[str], datetime.datetime, datetime.date]:

    result : Union[str, List[str], datetime.date, datetime.datetime] = raw_value

    if prop_name in TodoModel.DATE_PROPERTIES:
        result = decode_date(raw_value, config)

    elif prop_name in TodoModel.TEXT_PROPERTIES:

        # Check if the user specified categories explicitly
        if prop_name == 'categories':
            result = raw_value.split(",")

    elif prop_name in TodoModel.INT_PROPERTIES:
        # To check if the value is actually an int, try converting
        result = str(int(raw_value))

    elif prop_name in TodoModel.ENUM_PROPERTIES:

        if raw_value.lower() in TodoModel.ENUM_VALUES[prop_name]:
            pass # We already assigned raw_value to result

        else:
            raise InvalidEnumValueError(prop_name, raw_value, TodoModel.ENUM_VALUES[prop_name])
    else:
        raise UnknownPropertyError(prop_name, TodoModel.supported_properties())

    return result


def decode_property_list(config : Configuration, raw_properties : List[str]) -> Dict[str, Union[str, List[str], int, datetime.datetime, datetime.date, List[str]]]:

    result : Dict[str, Union[str, List[str], int, datetime.datetime, datetime.date, List[str]]] = {}
    category_modifiers : List[str] = []

    for arg in raw_properties:
        argtype = arg_type(arg, TodoModel.supported_properties())

        if argtype == ArgType.CATEGORY_MODIFIER:
            category_modifiers.append(arg)

        elif argtype == ArgType.PROPERTY:

            col_pos = arg.find(':')
            arg_name = arg[0:col_pos]
            arg_raw_value = arg[col_pos+1:]

            arg_name_full = expand_prefix(arg_name, TodoModel.supported_properties())

            if arg_raw_value != "":
                arg_value = parse_property_str(config, arg_name_full, arg_raw_value)
                result[arg_name_full] = arg_value

            # Also include empty string, so that we can later on know
            # that we need to remove the property.
            else:
                result[arg_name_full] = arg_raw_value

        elif argtype == ArgType.STRING:

            if 'summary' in result:
                raise Exception("Unable to detect property from argument " + arg)

            # Ensure that we do not write an empty
            # summary.
            if len(arg) == 0:
                raise Exception("Summary text must be non-empty.")

            result['summary'] = arg

        # We do not support explicit specification of categories
        # in conjunction with category modifiers
        if len(category_modifiers) > 0:

            if 'categories' in result:
                raise InvalidCategorySpecificationError()

            result['category_modifiers'] = category_modifiers

    return result