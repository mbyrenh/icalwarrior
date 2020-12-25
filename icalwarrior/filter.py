from typing import List
import icalendar
from icalwarrior.todo import Todo
from icalwarrior.util import expand_prefix, decode_date
from icalwarrior.configuration import Configuration

class UnknownOperatorError(Exception):

    def __init__(self, prop : str, operator : str, supported : List[str]) -> None:
        self.prop = prop
        self.op = operator
        self.supported = supported

    def __str__(self):
        return "Unknown operator: " + self.op + " for property " + self.prop + ". Supported operators: " + ", ".join(self.supported)

def date_before(config : Configuration, date_a : str, date_b : str) -> bool:
    ical_date = icalendar.vDatetime.from_ical(date_a)
    comp_date = decode_date(date_b, config)
    return ical_date < comp_date

def date_after(config : Configuration, date_a : str, date_b : str) -> bool:
    ical_date = icalendar.vDatetime.from_ical(date_a)
    comp_date = decode_date(date_b, config)
    return ical_date > comp_date

def date_equals(config : Configuration, date_a : str, date_b : str) -> bool:
    ical_date = icalendar.vDatetime.from_ical(date_a)
    comp_date = decode_date(date_b, config)
    return ical_date == comp_date

def text_contains(config : Configuration, text_a : str, text_b : str) -> bool:
    return text_a.find(text_b) != -1

def text_equals(config : Configuration, text_a : str, text_b : str) -> bool:
    return text_a == text_b

def int_gt(config : Configuration, int_a : str, int_b : str) -> bool:
    return int(int_a) > int(int_b)

def int_geq(config : Configuration, int_a : str, int_b : str) -> bool:
    return int(int_a) >= int(int_b)

def int_lt(config : Configuration, int_a : str, int_b : str) -> bool:
    return int(int_a) < int(int_b)

def int_leq(config : Configuration, int_a : str, int_b : str) -> bool:
    return int(int_a) <= int(int_b)

def int_equals(config : Configuration, int_a : str, int_b : str) -> bool:
    return int(int_a) == int(int_b)

class Constraint:

    DATE_OPERATORS = {
        'before' : date_before,
        'after' : date_after,
        'equals' : date_equals
    }

    TEXT_OPERATORS = {
        'contains' : text_contains,
        'equals' : text_equals
    }

    INT_OPERATORS = {
        'gt' : int_gt,
        'geq' : int_geq,
        'lt' : int_lt,
        'leq' : int_leq,
        'equals' : int_equals
    }

    @staticmethod
    def evaluate(config : Configuration, todo : icalendar.Todo, prop : str, operator : str, value : str) -> bool:

        result = False
        operators = None
        prop_value = None

        if prop in Todo.TEXT_PROPERTIES:
            operators = Constraint.TEXT_OPERATORS
            prop_value = todo[prop]

        elif prop in Todo.TEXT_FILTER_PROPERTIES:
            operators = Constraint.TEXT_OPERATORS
            prop_value = todo['context'][prop]

        elif prop in Todo.DATE_PROPERTIES:
            operators = Constraint.DATE_OPERATORS
            prop_value = todo[prop]

        elif prop in Todo.INT_PROPERTIES:
            operators = Constraint.INT_OPERATORS
            prop_value = todo[prop]

        elif prop in Todo.INT_FILTER_PROPERTIES:
            operators = Constraint.INT_OPERATORS
            prop_value = todo['context'][prop]

        op = expand_prefix(operator, operators.keys())

        if op == "":
            raise UnknownOperatorError(prop, operator, operators.keys())

        result = operators[op](config, prop_value, value)

        return result
