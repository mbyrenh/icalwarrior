from typing import List


from icalwarrior.configuration import Configuration
import datetime
from dateutil.relativedelta import *
import dateutil.tz as tz
import calendar
import icalendar

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

def today_as_datetime() -> datetime:
    return datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time(), tz.gettz())

def adapt_datetype(date : datetime.datetime, ref : icalendar.vDDDTypes) -> object:
    result = date
    # Additional check for instance of datetime is necessary
    # to avoid treating a datetime as date.
    if isinstance(ref, datetime.datetime):
        pass
    elif isinstance(ref, datetime.date):
        result = result.date()
    elif isinstance(ref, datetime.time):
        result = result.time()
    return result

def decode_date_formula(base_date : datetime, formula : str) -> datetime:
    units = ["days",
             "weeks",
             "months",
             "years"]

    result = base_date
    buf = ""
    i = 0

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

    synonyms = {
        "today" : today_as_datetime(),
        "tomorrow" : (today_as_datetime() + relativedelta(days=+1)),
        "monday" : (today_as_datetime() + relativedelta(weekday=calendar.MONDAY)),
        "tuesday" : (today_as_datetime() + relativedelta(weekday=calendar.TUESDAY)),
        "wednesday" : (today_as_datetime() + relativedelta(weekday=calendar.WEDNESDAY)),
        "thursday" : (today_as_datetime() + relativedelta(weekday=calendar.THURSDAY)),
        "friday" : (today_as_datetime() + relativedelta(weekday=calendar.FRIDAY)),
        "saturday" : (today_as_datetime() + relativedelta(weekday=calendar.SATURDAY)),
        "sun" : (today_as_datetime() + relativedelta(weekday=calendar.SUNDAY))
        }

    if len(date) == 0:
        raise InvalidDateFormatError(config.get_date_format() + " or " + config.get_datetime_format())

    result = None

    now = datetime.datetime.now(tz.gettz())
    read_date = None
    base_end = 0
    # If the date length is at least as long as the datetime format,
    # check if it is correctly formatted
    min_len = len(now.strftime(config.get_datetime_format()))
    if len(date) >= min_len:
        try:
            read_date = datetime.datetime.strptime(date[0:min_len], config.get_datetime_format())
            base_end = min_len-1
        except ValueError:
            pass

    # If the date length is at least as long as the datetime format,
    # check if it is correctly formatted
    min_len = len(now.strftime(config.get_date_format()))
    if len(date) >= min_len:
        try:
            read_date = datetime.datetime.strptime(date[0:min_len], config.get_date_format())
            base_end = min_len-1
        except ValueError:
            pass

    if read_date is not None:
        result = read_date

    # Check if we can find a synonym
    else:
        buf = ""
        i = 0
        while i < len(date) and date[i].isalpha():
            buf += date[i]
            i += 1

        synonym = expand_prefix(buf, synonyms)
        if synonym == "":
            raise InvalidDateFormatError(config.get_date_format() + " or " + config.get_datetime_format())

        result = synonyms[synonym]
        base_end = i-1

    result = decode_date_formula(result, date[base_end+1:])

    return result
