import datetime
from dateutil.relativedelta import *
import dateutil.tz as tz
import pytest

from icalwarrior.util import decode_date, InvalidDateFormatError, InvalidDateFormulaError
from icalwarrior.configuration import Configuration

class DummyConfiguration:

    def get_date_format(self) -> str:
        result = self.dateformat
        return result

    def get_datetime_format(self) -> str:
        result = self.datetimeformat
        return result

def today_as_datetime() -> datetime.datetime:
    return datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time(), tz.gettz())

def test_date_decode_format():

    config = DummyConfiguration()
    config.dateformat = "%Y-%m-%d"
    config.datetimeformat = "%Y-%m-%dT%H:%M:%S"

    datestr = "2000-08-14"
    result = decode_date(datestr, config)

    assert result == datetime.datetime(2000,8,14)

    datestr = "2000-08-14T12:34:01"
    result = decode_date(datestr, config)
    assert result == datetime.datetime(2000,8,14,12,34,1)

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
    with pytest.raises(InvalidDateFormulaError):
        datestr = "2000-08-14T12:34:011"
        result = decode_date(datestr, config)

def test_date_decode_formula():
    datestr = "tod+2w-2d"
    config = DummyConfiguration()
    config.dateformat = "%Y-%m-%d"
    config.datetimeformat = "%Y-%m-%dT%H:%M:%S"

    result = decode_date(datestr, config)

    assert result == today_as_datetime() + relativedelta(weeks=+2) - relativedelta(days=+2)

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
