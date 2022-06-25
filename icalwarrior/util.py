# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Iterable, Union, Dict

import calendar
import datetime
from dateutil.relativedelta import relativedelta
import dateutil.tz as tz
import icalendar
import icalwarrior.constants as constants
from icalwarrior.configuration import Configuration

class InvalidEnumValueError(Exception):

    def __init__(self, prop : str, given : str, supported : List[str]) -> None:
        self.prop = prop
        self.given = given
        self.supported = supported

    def __str__(self) -> str:
        return "Invalid value \"" + self.given + "\" for property \"" + self.prop + "\". Supported values are " + ", ".join(self.supported)


def expand_prefix(prefix : str, candidates : Iterable[str]) -> str:

    result = ""

    for candidate in candidates:
        if candidate.find(prefix) == 0:
            if result == "":
                result = candidate
            else:
                result = ""
                break

    return result

class InvalidDateFormulaError(Exception):

    def __init__(self, error : str) -> None:
        self.error = error

    def __str__(self) -> str:
        return "Invalid date format: " + self.error

class InvalidDateFormatError(Exception):

    def __init__(self, date_format : str, datetime_format : str, synonyms : Iterable[str]) -> None:
        self.date_format = date_format
        self.datetime_format = datetime_format
        self.synonyms = synonyms

    def __str__(self) -> str:
        return "Invalid date format. Expected format is " + self.date_format + " or " + self.datetime_format + " or a synonym from " + ", ".join(self.synonyms) + "."

def remove_units(start_date : datetime.date | datetime.datetime, unit : str, quantity : int) -> datetime.date | datetime.datetime:

    result = {
        "minutes": start_date - relativedelta(minutes=+quantity),
        "hours": start_date - relativedelta(hours=+quantity),
        "days": start_date - relativedelta(days=+quantity),
        "weeks": start_date - relativedelta(weeks=+quantity),
        "months": start_date - relativedelta(months=+quantity),
        "years": start_date - relativedelta(years=+quantity)
    }[unit]

    return result

def add_units(start_date : datetime.date | datetime.datetime, unit : str, quantity : int) -> datetime.date | datetime.datetime:

    result = {
        "minutes": start_date + relativedelta(minutes=+quantity),
        "hours": start_date + relativedelta(hours=+quantity),
        "days": start_date + relativedelta(days=+quantity),
        "weeks": start_date + relativedelta(weeks=+quantity),
        "months": start_date + relativedelta(months=+quantity),
        "years": start_date + relativedelta(years=+quantity)
    }[unit]

    return result

def today_as_datetime() -> datetime.datetime:
    return datetime.datetime.combine(
        datetime.date.today(),
        datetime.datetime.min.time(),
        tz.gettz())

def today_as_date() -> datetime.date:
    return datetime.date.today()

def tomorrow_as_date() -> datetime.date:
    return today_as_date() + relativedelta(days=+1)

def adapt_datetype(date : datetime.date | datetime.datetime, ref : object) -> datetime.datetime | datetime.date:
    result = date

    # Additional check for instance of datetime is necessary
    # to avoid treating a datetime as date.
    if isinstance(ref, datetime.datetime):

        if isinstance(result, datetime.datetime):
            if ref.tzinfo is None or ref.tzinfo.utcoffset(ref) is None:
                result = result.replace(tzinfo=None)

        elif isinstance(result, datetime.date):
            result = datetime.datetime.combine(
                result,
                datetime.datetime.min.time(),
                ref.tzinfo
            )

    elif isinstance(ref, datetime.date):
        if isinstance(result, datetime.datetime):
            result = result.date()

    return result

def decode_date_formula(base_date : datetime.datetime | datetime.date, formula : str) -> datetime.datetime | datetime.date:
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

def decode_relative_date(date : str, config : Configuration) -> datetime.date | datetime.datetime:

    # First, determine base date
    buf = ""
    i = 0
    while i < len(date) and date[i].isalpha():
        buf += date[i]
        i += 1

    synonym = expand_prefix(buf, synonyms.keys())
    if synonym == "":
        raise InvalidDateFormatError(
            config.get_date_format(),
            config.get_datetime_format(),
            synonyms.keys())

    result : datetime.date | datetime.datetime = synonyms[synonym]

    # Now, check if a time is given as well
    # Assumes that configured date format uses zero-padded numbers
    decoded_time = None
    if i < len(date) and date[i] == constants.RELATIVE_DATE_TIME_SEPARATOR:
        i = i + 1
        now = datetime.datetime.now(tz.gettz())
        time_len = len(now.strftime(config.get_time_format_for_relative_dates()))
        try:
            decoded_time = datetime.datetime.strptime(date[i:i+time_len], config.get_time_format_for_relative_dates()).time()
            result = datetime.datetime.combine(
                result,
                decoded_time,
                tz.gettz())
            i = i+time_len
        except ValueError:
            raise InvalidDateFormatError(
                config.get_date_format(),
                config.get_datetime_format(),
                synonyms.keys())

    # Check if there is an additional offset
    if len(date) > i:
        result = decode_date_formula(result, date[i:])

    return result

def decode_date(date : str, config : Configuration) -> datetime.date | datetime.datetime:

    if len(date) == 0:
        raise InvalidDateFormatError(config.get_date_format(), config.get_datetime_format(), synonyms.keys())

    read_date = None
    try:

        read_date = datetime.datetime.strptime(date, config.get_date_format())
        return read_date

    except ValueError:
        read_date = None

    try:
        read_date = datetime.datetime.strptime(date, config.get_datetime_format())
        return read_date
    except ValueError:
        read_date = None

    return decode_relative_date(date, config)

synonyms : Dict[str, Union[datetime.date, datetime.datetime]] = {
    "now" : datetime.datetime.now(),
    "today" : today_as_date(),
    "tomorrow" : tomorrow_as_date(),
    "monday" : (tomorrow_as_date() + relativedelta(weekday=calendar.MONDAY)),
    "tuesday" : (tomorrow_as_date() + relativedelta(weekday=calendar.TUESDAY)),
    "wednesday" : (tomorrow_as_date() + relativedelta(weekday=calendar.WEDNESDAY)),
    "thursday" : (tomorrow_as_date() + relativedelta(weekday=calendar.THURSDAY)),
    "friday" : (tomorrow_as_date() + relativedelta(weekday=calendar.FRIDAY)),
    "saturday" : (tomorrow_as_date() + relativedelta(weekday=calendar.SATURDAY)),
    "sunday" : (tomorrow_as_date() + relativedelta(weekday=calendar.SUNDAY))
    }
