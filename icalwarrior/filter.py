from typing import List, Iterable, Mapping, Callable, Any, Union, Dict, TypeAlias
import datetime
import icalendar
from icalwarrior.todo import TodoPropertyHandler
from icalwarrior.util import expand_prefix, decode_date, adapt_datetype
from icalwarrior.configuration import Configuration

OperatorArg: TypeAlias = Union[datetime.datetime, datetime.date, int, str]

class UnknownOperatorError(Exception):

    def __init__(self, prop : str, operator : str, supported : Iterable[str]) -> None:
        self.prop = prop
        self.op = operator
        self.supported = supported

    def __str__(self) -> str:
        return "Unknown operator: " + self.op + " for property " + self.prop + ". Supported operators: " + ", ".join(self.supported)

def date_before(config : Configuration, date_a : datetime.datetime | datetime.date, date_b : str) -> bool:
    comp_date = adapt_datetype(decode_date(date_b, config), date_a)
    return date_a < comp_date

def date_after(config : Configuration, date_a : datetime.datetime | datetime.date, date_b : str) -> bool:
    comp_date = adapt_datetype(decode_date(date_b, config), date_a)
    return date_a > comp_date

def date_equals(config : Configuration, date_a : datetime.datetime | datetime.date, date_b : str) -> bool:
    comp_date = adapt_datetype(decode_date(date_b, config), date_a)
    # format dates to ignore datetime, as we
    # do not consider time of day for equality test
    return date_a.strftime("%Y-%m-%d") == comp_date.strftime("%Y-%m-%d")

def text_contains(config : Configuration, text_a : str, text_b : str) -> bool:
    return text_a.lower().find(text_b.lower()) != -1

def text_not_contains(config : Configuration, text_a : str, text_b : str) -> bool:
    return text_a.lower().find(text_b.lower()) == -1

def text_equals(config : Configuration, text_a : str, text_b : str) -> bool:
    return text_a.lower() == text_b.lower()

def text_not_equals(config : Configuration, text_a : str, text_b : str) -> bool:
    return text_a.lower() != text_b.lower()

def int_gt(config : Configuration, int_a : int, int_b : int) -> bool:
    return int(int_a) > int(int_b)

def int_geq(config : Configuration, int_a : int, int_b : int) -> bool:
    return int(int_a) >= int(int_b)

def int_lt(config : Configuration, int_a : int, int_b : int) -> bool:
    return int(int_a) < int(int_b)

def int_leq(config : Configuration, int_a : int, int_b : int) -> bool:
    return int(int_a) <= int(int_b)

def int_equals(config : Configuration, int_a : int, int_b : int) -> bool:
    return int(int_a) == int(int_b)

def int_not_equals(config : Configuration, int_a : int, int_b : int) -> bool:
    return int(int_a) != int(int_b)

class Constraint:

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

    @staticmethod
    def evaluate(config : Configuration, todo : TodoPropertyHandler, prop : str, operator : str, value : str) -> bool:

        result = False
        prop_value : OperatorArg = ""
        supported_operators : List[str] = []

        if prop in TodoPropertyHandler.supported_filter_properties() and todo.has_property(prop):

            type_fact = icalendar.prop.TypesFactory()

            if type_fact.for_property(prop) is icalendar.prop.vText:
                prop_value = todo.get_string(prop)
                supported_operators = list(Constraint.TEXT_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            elif type_fact.for_property(prop) is icalendar.prop.vCategory:
                # TODO: from_ical vom vCategory throws an assertion error.
                #       We therefore convert it manually.
                prop_value = ",".join([str(c) for c in todo.get_categories()])
                supported_operators = list(Constraint.TEXT_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            elif type_fact.for_property(prop) is icalendar.prop.vDDDTypes:
                prop_value = todo.get_date_or_datetime(prop)
                supported_operators = list(Constraint.DATE_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            elif type_fact.for_property(prop) is icalendar.prop.vInt:
                prop_value = todo.get_int(prop)
                supported_operators = list(Constraint.INT_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            if op == "":
                raise UnknownOperatorError(prop, operator, supported_operators)

            if isinstance(prop_value, int):
                result = Constraint.INT_OPERATORS[op](config, prop_value, int(value))
            elif isinstance(prop_value, str):
                result = Constraint.TEXT_OPERATORS[op](config, prop_value, value)
            else:
                result = Constraint.DATE_OPERATORS[op](config, prop_value, value)

        elif prop in todo.get_context():

            if prop in TodoPropertyHandler.TEXT_FILTER_PROPERTIES:
                prop_value = str(todo.get_context()[prop])
                supported_operators = list(Constraint.TEXT_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            elif prop in TodoPropertyHandler.INT_FILTER_PROPERTIES:
                prop_value = int(todo.get_context()[prop])
                supported_operators = list(Constraint.INT_OPERATORS.keys())
                op = expand_prefix(operator,supported_operators)

            if op == "":
                raise UnknownOperatorError(prop, operator, supported_operators)

            if isinstance(prop_value, int):
                result = Constraint.INT_OPERATORS[op](config, prop_value, int(value))
            elif isinstance(prop_value, str):
                result = Constraint.TEXT_OPERATORS[op](config, prop_value, value)

        return result
