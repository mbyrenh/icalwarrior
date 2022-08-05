# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Iterable, Callable, Union, Dict, TypeAlias
from enum import Enum
import datetime
import icalendar
from icalwarrior.model.items import TodoModel
from icalwarrior.input.date import expand_prefix
from icalwarrior.configuration import Configuration
from icalwarrior.filtering.operators import *
import icalwarrior.constants as constants

class ConstraintElementType(Enum):
    logical_relation = 'logical_relation'
    property_value = 'property_value'

OperatorArg: TypeAlias = Union[datetime.datetime, datetime.date, int, str]
ConstraintElement: TypeAlias = Union[str, tuple[str,str,str]]
ConstraintSpec: TypeAlias = tuple[ConstraintElementType, ConstraintElement]

class UnknownOperatorError(Exception):

    def __init__(self, prop : str, operator : str, supported : Iterable[str]) -> None:
        self.prop = prop
        self.op = operator
        self.supported = supported

    def __str__(self) -> str:
        return "Unknown operator: " + self.op + " for property " + self.prop + ". Supported operators: " + ", ".join(self.supported)

class InvalidFilterExpressionError(Exception):

    def __init__(self, expression : str) -> None:
        self.expression = expression

    def __str__(self) -> str:
        return "Invalid filter expression \"" + self.expression + "\"."

class InvalidConstraintFormatError(Exception):

    def __init__(self, constraint : str) -> None:
        self.constraint = constraint

    def __str__(self) -> str:
        return "Invalid constraint \"" + self.constraint + "\". Constraint format is NAME[.OPERATOR]:VALUE"

class ConstraintEvaluator:

    DATE_OPERATORS : Dict[str, Callable[[Configuration, datetime.datetime | datetime.date, str], bool]] = {
        'before' : date_before,
        'after' : date_after,
        'equals' : date_equals
    }

    TEXT_OPERATORS : Dict[str, Callable[[Configuration, str, str], bool]] = {
        'contains' : text_contains,
        'not_contains' : text_not_contains,
        'equals' : text_equals,
        'not_equals' : text_not_equals
    }

    INT_OPERATORS : Dict[str, Callable[[Configuration, int, int], bool]]  = {
        'gt' : int_gt,
        'geq' : int_geq,
        'lt' : int_lt,
        'leq' : int_leq,
        'equals' : int_equals,
        'not_equals' : int_not_equals
    }

    TEXT_FILTER_PROPERTIES = [
        'uid',
        'list'
    ]

    INT_FILTER_PROPERTIES = [
        'id'
    ]

    @staticmethod
    def supported_filter_properties() -> List[str]:
        return TodoModel.DATE_PROPERTIES \
               + TodoModel.TEXT_PROPERTIES \
               + TodoModel.ENUM_PROPERTIES \
               + TodoModel.INT_PROPERTIES \
               + ConstraintEvaluator.TEXT_FILTER_PROPERTIES \
               + ConstraintEvaluator.INT_FILTER_PROPERTIES

    def __init__(self, config : Configuration, normalized_constraints : List[ConstraintSpec]):
        self.config = config
        self.constraints = normalized_constraints

    @classmethod
    def from_string_list(cls, config : Configuration, constraints : List[str]) -> 'ConstraintEvaluator':

        class ConstraintType(Enum):
            NONE = "NONE"
            PROPERTY_VALUE = "PROPERTY_VALUE"
            LOGIC_RELATION = "LOGIC_RELATION"

        normalized_constraints : List[ConstraintSpec] = []

        previous_constraint_type : ConstraintType = ConstraintType.NONE
        for constraint in constraints:

            if constraint in ("and", "or"):

                if previous_constraint_type != ConstraintType.PROPERTY_VALUE:
                    raise InvalidFilterExpressionError(" ".join(constraints))

                normalized_constraints.append((ConstraintElementType.logical_relation, constraint))
                previous_constraint_type = ConstraintType.LOGIC_RELATION

            else:

                if previous_constraint_type == ConstraintType.PROPERTY_VALUE:
                    normalized_constraints.append((ConstraintElementType.logical_relation, "and"))

                if constraint.startswith(constants.CATEGORY_INCLUDE_PREFIX) or constraint.startswith(
                        constants.CATEGORY_EXCLUDE_PREFIX):

                    prop_name = "categories"

                    if constraint.startswith(constants.CATEGORY_INCLUDE_PREFIX):
                        prop_val = constraint[len(constants.CATEGORY_INCLUDE_PREFIX):]
                        operator = "contains"
                    else:
                        prop_val = constraint[len(constants.CATEGORY_EXCLUDE_PREFIX):]
                        operator = "not_contains"

                    normalized_constraints.append((ConstraintElementType.property_value, (prop_name, operator, prop_val)))

                else:

                    col_pos = constraint.find(":")
                    if col_pos == -1:
                        raise InvalidConstraintFormatError(constraint)

                    dot_pos = constraint[0:col_pos].find(".")
                    if dot_pos != -1:
                        operator = constraint[dot_pos + 1:col_pos]
                        prop_name = expand_prefix(constraint[0:dot_pos], ConstraintEvaluator.supported_filter_properties())
                    else:
                        operator = "equals"
                        prop_name = expand_prefix(constraint[0:col_pos], ConstraintEvaluator.supported_filter_properties())

                    prop_val = constraint[col_pos + 1:]

                    normalized_constraints.append((ConstraintElementType.property_value, (prop_name, operator, prop_val)))

                previous_constraint_type = ConstraintType.PROPERTY_VALUE

        if previous_constraint_type != ConstraintType.PROPERTY_VALUE:
            raise InvalidFilterExpressionError(" ".join(constraints))

        return ConstraintEvaluator(config, normalized_constraints)

    def satisfies_constraints(self, todo : TodoModel) -> bool:

        buf = ""
        for constraint in self.constraints:

            constraint_type = constraint[0]
            if constraint_type == ConstraintElementType.logical_relation:
                assert isinstance(constraint[1], str)
                buf += " " + constraint[1] + " "

            else:

                prop_name = constraint[1][0]
                operator = constraint[1][1]
                prop_val = constraint[1][2]
                buf += str(self._evaluate(todo, prop_name, operator, prop_val))

        return bool(eval(buf))


    def _evaluate(self, todo : TodoModel, prop : str, operator : str, value : str) -> bool:

        result = False
        prop_value : OperatorArg = ""
        supported_operators : List[str] = []

        if prop in ConstraintEvaluator.supported_filter_properties() and todo.has_property(prop):

            type_fact = icalendar.prop.TypesFactory()

            if type_fact.for_property(prop) is icalendar.prop.vText:
                prop_value = todo.get_string(prop)
                supported_operators = list(ConstraintEvaluator.TEXT_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            elif type_fact.for_property(prop) is icalendar.prop.vCategory:
                # TODO: from_ical vom vCategory throws an assertion error.
                #       We therefore convert it manually.
                prop_value = ",".join([str(c) for c in todo.get_categories()])
                supported_operators = list(ConstraintEvaluator.TEXT_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            elif type_fact.for_property(prop) is icalendar.prop.vDDDTypes:
                prop_value = todo.get_date_or_datetime(prop)
                supported_operators = list(ConstraintEvaluator.DATE_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            elif type_fact.for_property(prop) is icalendar.prop.vInt:
                prop_value = todo.get_int(prop)
                supported_operators = list(ConstraintEvaluator.INT_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            if op == "":
                raise UnknownOperatorError(prop, operator, supported_operators)

            if isinstance(prop_value, int):
                result = ConstraintEvaluator.INT_OPERATORS[op](self.config, prop_value, int(value))
            elif isinstance(prop_value, str):
                result = ConstraintEvaluator.TEXT_OPERATORS[op](self.config, prop_value, value)
            else:
                result = ConstraintEvaluator.DATE_OPERATORS[op](self.config, prop_value, value)

        elif prop in todo.CONTEXT_PROPERTIES:

            if prop in ConstraintEvaluator.TEXT_FILTER_PROPERTIES:
                prop_value = str(todo.get_context(prop))
                supported_operators = list(ConstraintEvaluator.TEXT_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            elif prop in ConstraintEvaluator.INT_FILTER_PROPERTIES:
                prop_value = int(todo.get_context(prop))
                supported_operators = list(ConstraintEvaluator.INT_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            if op == "":
                raise UnknownOperatorError(prop, operator, supported_operators)

            if isinstance(prop_value, int):
                result = ConstraintEvaluator.INT_OPERATORS[op](self.config, prop_value, int(value))
            elif isinstance(prop_value, str):
                result = ConstraintEvaluator.TEXT_OPERATORS[op](self.config, prop_value, value)

        return result
