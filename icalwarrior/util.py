from typing import List

from configuration import Configuration
from datetime import datetime, date
from dateutil.relativedelta import *
import calendar

def expand_prefix(prefix : str, candidates : List[str]) -> str:

    result = ""

    for candidate in candidates:
        if candidate.find(prefix) == 0:
            if result == "":
                result = candidate
            else:
                result = ""
                break

    return result

class InvalidSynonymError(Exception):

    def __init__(self, actual : str, supported : List[str]) -> None:
        self.actual = actual
        self.supported = supported

    def __str__(self):
        return "Invalid date symonym or ambiguous prefix \"" + self.actual + "\". Supported synonyms are " + ",".join(self.supported) + "."

class InvalidDateFormulaError(Exception):

    def __init__(self, error : str) -> None:
        self.error = error

    def __str__(self):
        return "Invalid date format: " + self.error

class InvalidDateFormatError(Exception):

    def __init__(self, dateformat : str) -> None:
        self.dateformat = dateformat

    def __str__(self):
        return "Invalid date format. Expected format is " + self.dateformat + "."

def remove_units(start_date : datetime, unit : str, quantity : int) -> datetime:

    result = {
        "days" : start_date - relativedelta(days=+quantity),
        "weeks" : start_date - relativedelta(weeks=+quantity),
        "months" : start_date - relativedelta(months=+quantity),
        "years" : start_date - relativedelta(years=+quantity)
    }[unit]

    return result

def add_units(start_date : datetime, unit : str, quantity : int) -> datetime:

    result = {
        "days" : start_date + relativedelta(days=+quantity),
        "weeks" : start_date + relativedelta(weeks=+quantity),
        "months" : start_date + relativedelta(months=+quantity),
        "years" : start_date + relativedelta(years=+quantity)
    }[unit]

    return result

def decode_date_formula(formula : str) -> datetime:
    synonyms = {"today" : date.today(),
                "tomorrow" : (date.today() + relativedelta(days=+1)),
                "monday" : (date.today() + relativedelta(weekday=calendar.MONDAY)),
                "tuesday" : (date.today() + relativedelta(weekday=calendar.TUESDAY)),
                "wednesday" : (date.today() + relativedelta(weekday=calendar.WEDNESDAY)),
                "thursday" : (date.today() + relativedelta(weekday=calendar.THURSDAY)),
                "friday" : (date.today() + relativedelta(weekday=calendar.FRIDAY))}

    units = ["days",
             "weeks",
             "months",
             "years"]

    result = None
    buf = ""
    i = 0
    while i < len(formula) and formula[i].isalpha():
        buf += formula[i]
        i += 1

    synonym = expand_prefix(buf, synonyms)
    if synonym == "":
        raise InvalidSynonymError(buf, synonyms)

    # Convert synonym to formulatime
    result = synonyms[synonym]

    # If there are more characters, continue reading
    while i < len(formula):

        # First, read operator
        op = ""
        if formula[i] == "+" or formula[i] == "-":
            op = formula[i]
            i += 1
        else:
            raise InvalidDateFormulaError("Expected either \"+\" or \"-\" at position " + str(i))

        # Afterwards, read number and unit
        buf = ""
        num = 0
        while i < len(formula) and formula[i].isdigit():
            buf += formula[i]
            i += 1

        try:
            num = int(buf)
        except ValueError as err:
            raise InvalidDateFormulaError("Expected digit at position " + str(i)) from err

        buf = ""
        while i < len(formula) and formula[i].isalpha():
            buf += formula[i]
            i += 1

        unit = expand_prefix(buf, units)
        if unit == "":
            raise InvalidDateFormulaError("Invalid unit or ambiguous prefix \"" + buf + "\". Supported units are " + ",".join(units))

        if op == "+":
            result = add_units(result, unit, num)
        elif op == "-":
            result = remove_units(result, unit, num)

    return result

def decode_date(date : str, config : Configuration) -> datetime:

    if len(date) == 0:
        raise InvalidDateFormatError(config.get_date_format() + " or " + config.get_datetime_format())

    result = None

    if date[0].isdigit():

        now = datetime.now()
        read_date = None
        # If the date length is at least as long as the datetime format,
        # check if it is correctly formatted
        if len(date) == len(now.strftime(config.get_datetime_format())):
            try:
                read_date = datetime.strptime(date, config.get_datetime_format())
            except ValueError:
                pass

        # If the date length is at least as long as the datetime format,
        # check if it is correctly formatted
        if len(date) == len(now.strftime(config.get_date_format())):
            try:
                read_date = datetime.strptime(date, config.get_date_format())
            except ValueError:
                pass

        if read_date is None:
                raise InvalidDateFormatError(config.get_date_format() + " or " + config.get_datetime_format())
        else:
            result = read_date


    ## otherwise, read it as a formula
    else:
        result = decode_date_formula(date)

    return result
