from typing import List
import icalendar
from icalwarrior.todo import Todo
from icalwarrior.util import expand_prefix, decode_date, adapt_datetype
from icalwarrior.configuration import Configuration

class UnknownOperatorError(Exception):

    def __init__(self, prop : str, operator : str, supported : List[str]) -> None:
        self.prop = prop
        self.op = operator
        self.supported = supported

    def __str__(self):
        return "Unknown operator: " + self.op + " for property " + self.prop + ". Supported operators: " + ", ".join(self.supported)

def date_before(config : Configuration, date_a : object, date_b : str) -> bool:
    comp_date = adapt_datetype(decode_date(date_b, config), date_a)
    return date_a < comp_date

def date_after(config : Configuration, date_a : object, date_b : str) -> bool:
    comp_date = adapt_datetype(decode_date(date_b, config), date_a)
    return date_a > comp_date

def date_equals(config : Configuration, date_a : object, date_b : str) -> bool:
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

def int_gt(config : Configuration, int_a : int, int_b : str) -> bool:
    return int(int_a) > int(int_b)

def int_geq(config : Configuration, int_a : int, int_b : str) -> bool:
    return int(int_a) >= int(int_b)

def int_lt(config : Configuration, int_a : str, int_b : str) -> bool:
    return int(int_a) < int(int_b)

def int_leq(config : Configuration, int_a : str, int_b : str) -> bool:
    return int(int_a) <= int(int_b)

def int_equals(config : Configuration, int_a : str, int_b : str) -> bool:
    return int(int_a) == int(int_b)

def int_not_equals(config : Configuration, int_a : str, int_b : str) -> bool:
    return int(int_a) != int(int_b)

class Constraint:

    DATE_OPERATORS = {
        'before' : date_before,
        'after' : date_after,
        'equals' : date_equals
    }

    TEXT_OPERATORS = {
        'contains' : text_contains,
        'not_contains' : text_not_contains,
        'equals' : text_equals,
        'not_equals' : text_not_equals
    }

    INT_OPERATORS = {
        'gt' : int_gt,
        'geq' : int_geq,
        'lt' : int_lt,
        'leq' : int_leq,
        'equals' : int_equals,
        'not_equals' : int_not_equals
    }

    @staticmethod
    def evaluate(config : Configuration, todo : icalendar.Todo, prop : str, operator : str, value : str) -> bool:

        result = False
        operators = None
        prop_value = None

        if prop in todo:

            type_fact = icalendar.prop.TypesFactory()

            if type_fact.for_property(prop) is icalendar.prop.vText:
                operators = Constraint.TEXT_OPERATORS
                prop_value = icalendar.prop.vText.from_ical(todo[prop])

            elif type_fact.for_property(prop) is icalendar.prop.vCategory:
                operators = Constraint.TEXT_OPERATORS
                # TODO: from_ical vom vCategory throws an assertion error.
                #       We therefore convert it manually.
                prop_value = ",".join([str(c) for c in todo[prop].cats])

            elif type_fact.for_property(prop) is icalendar.prop.vDDDTypes:
                operators = Constraint.DATE_OPERATORS
                prop_value = icalendar.prop.vDDDTypes.from_ical(todo[prop])

            elif type_fact.for_property(prop) is icalendar.prop.vInt:
                operators = Constraint.INT_OPERATORS
                prop_value = icalendar.prop.vInt.from_ical(todo[prop])

            op = expand_prefix(operator, operators.keys())

            if op == "":
                raise UnknownOperatorError(prop, operator, operators.keys())

            result = operators[op](config, prop_value, value)

        elif prop in todo['context']:

            if prop in Todo.TEXT_FILTER_PROPERTIES:
                operators = Constraint.TEXT_OPERATORS
                prop_value = todo['context'][prop]

            elif prop in Todo.INT_FILTER_PROPERTIES:
                operators = Constraint.INT_OPERATORS
                prop_value = todo['context'][prop]

            op = expand_prefix(operator, operators.keys())

            if op == "":
                raise UnknownOperatorError(prop, operator, operators.keys())

            result = operators[op](config, prop_value, value)

        return result
