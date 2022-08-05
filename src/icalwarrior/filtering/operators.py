# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import datetime
from icalwarrior.input.date import decode_date, adapt_datetype
from icalwarrior.configuration import Configuration

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