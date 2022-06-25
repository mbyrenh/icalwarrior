# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
from dateutil.relativedelta import *
import dateutil.tz as tz
import pytest

from icalwarrior.util import decode_date, InvalidDateFormatError, InvalidDateFormulaError, synonyms 
from icalwarrior.configuration import Configuration
from icalwarrior.constants import RELATIVE_DATE_TIME_SEPARATOR, RELATIVE_DATE_TIME_FORMAT

class DummyConfiguration:

    def get_date_format(self) -> str:
        result = self.dateformat
        return result

    def get_datetime_format(self) -> str:
        result = self.datetimeformat
        return result

    def get_time_format_for_relative_dates(self) -> str:
        return RELATIVE_DATE_TIME_FORMAT

def today_as_date() -> datetime.date:
    return datetime.date.today()

def test_absolute_date_decode():

    config = DummyConfiguration()
    config.dateformat = "%Y-%m-%d"
    config.datetimeformat = "%Y-%m-%dT%H:%M:%S"

    datestr = "2000-08-14"
    result = decode_date(datestr, config)

    assert result == datetime.datetime(2000,8,14)

def test_absolute_date_with_time_decode():

    config = DummyConfiguration()
    config.dateformat = "%Y-%m-%d"
    config.datetimeformat = "%Y-%m-%dT%H:%M:%S"

    datestr = "2000-08-14T12:34:01"
    result = decode_date(datestr, config)
    assert result == datetime.datetime(2000,8,14,12,34,1)

def test_relative_date_decode():

    config = DummyConfiguration()
    config.dateformat = "%Y-%m-%d"
    config.timeformat = "%H:%M:%S"
    config.datetimeformat = config.dateformat + "T" + config.timeformat

    datestr = "today+2d"
    result = decode_date(datestr, config)

    assert result == today_as_date() + relativedelta(days=+2)

def test_relative_date_with_time_decode():

    config = DummyConfiguration()
    config.dateformat = "%Y-%m-%d"
    config.timeformat = "%H:%M"
    config.datetimeformat = config.dateformat + "T" + config.timeformat

    datestr = "today" + RELATIVE_DATE_TIME_SEPARATOR + "12:34+2d"
    result = decode_date(datestr, config)
    expected = datetime.datetime.combine(today_as_date(), datetime.time(12,34), tz.gettz()) + relativedelta(days=+2)
    assert result == expected

def test_date_decode_invalid_format():

    config = DummyConfiguration()
    config.dateformat = "%Y-%m-%d"
    config.datetimeformat = "%Y-%m-%dT%H:%M:%S"
    with pytest.raises(InvalidDateFormatError):
        datestr = ""
        result = decode_date(datestr, config)
    with pytest.raises(InvalidDateFormatError):
        datestr = "2000-08-33"
        result = decode_date(datestr, config)
    with pytest.raises(InvalidDateFormatError):
        datestr = "14.08.2020"
        result = decode_date(datestr, config)
    with pytest.raises(InvalidDateFormatError):
        datestr = "2000-08-14T12:34:011"
        result = decode_date(datestr, config)

def test_relative_date_not_same_day():
    config = DummyConfiguration()
    config.dateformat = "%Y-%m-%d"
    config.timeformat = "%H:%M:%S"
    config.datetimeformat = config.dateformat + "T" + config.timeformat

    datestr = "today"
    today = decode_date(datestr, config)

    # For each weekday, make sure it never returns today
    for day, day_date in synonyms.items():

        if day != "today":
            assert day_date != today

def test_date_decode_formula():
    datestr = "tod+2w-2d"
    config = DummyConfiguration()
    config.dateformat = "%Y-%m-%d"
    config.datetimeformat = "%Y-%m-%dT%H:%M:%S"

    result = decode_date(datestr, config)

    assert result == today_as_date() + relativedelta(weeks=+2) - relativedelta(days=+2)

def test_date_decode_invalid_formula():
    config = DummyConfiguration()
    config.dateformat = "%Y-%m-%d"
    config.datetimeformat = "%Y-%m-%dT%H:%M:%S"
    with pytest.raises(InvalidDateFormatError):
        datestr = "to+2w-2d"
        result = decode_date(datestr, config)

    with pytest.raises(InvalidDateFormulaError):
        datestr = "tod++2w-2d"
        result = decode_date(datestr, config)

    with pytest.raises(InvalidDateFormulaError):
        datestr = "tod+"
        result = decode_date(datestr, config)
