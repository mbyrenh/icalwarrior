# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import icalendar
import datetime
import humanize
import dateutil.tz as tz

from icalwarrior.todo import TodoPropertyHandler
from icalwarrior.configuration import Configuration
from icalwarrior.util import adapt_datetype

class StringFormatter:

    def __init__(self, config : Configuration) -> None:
        self.config = config

    def format_property_name(self, prop_name : str) -> str:

        property_aliases = {

            'dtstart' : 'starts',
            'dtend' : 'ends'

        }

        result = property_aliases.get(prop_name, prop_name).capitalize()

        return result


    def format_property_value(self, prop_name : str, todo : TodoPropertyHandler) -> str:

        result = ""

        if todo.has_property(prop_name):

            type_fact = icalendar.prop.TypesFactory()

            if type_fact.for_property(prop_name) is icalendar.prop.vDDDTypes:
                prop_value = todo.get_date_or_datetime(prop_name)
                now = adapt_datetype(datetime.datetime.now(tz.gettz()), prop_value)

                result = prop_value.strftime(self.config.get_datetime_format())
                if isinstance(now, datetime.datetime):
                    assert isinstance(prop_value, datetime.datetime)
                    result = prop_value.strftime(self.config.get_datetime_format())
                    result += " (" + humanize.naturaltime(prop_value, when=now) + ")"
                else:
                    result = prop_value.strftime(self.config.get_date_format())
                    result += " (" + humanize.naturalday(prop_value) + ")"

            elif type_fact.for_property(prop_name) is icalendar.prop.vText:
                result = todo.get_string(prop_name)

            elif type_fact.for_property(prop_name) is icalendar.prop.vInt:
                result = str(todo.get_int(prop_name))

            elif type_fact.for_property(prop_name) is icalendar.prop.vCategory:
                # TODO: from_ical vom vCategory throws an assertion error.
                #       We therefore convert it manually.
                result = ",".join([str(c) for c in todo.get_categories()])

        if prop_name in todo.get_context():

            if prop_name in TodoPropertyHandler.TEXT_FILTER_PROPERTIES:
                result = str(todo.get_context()[prop_name])

            elif prop_name in TodoPropertyHandler.INT_FILTER_PROPERTIES:
                result = str(todo.get_context()[prop_name])

        return result
