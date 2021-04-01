import icalendar
import datetime
import humanize
import dateutil.tz as tz

from icalwarrior.todo import Todo
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


    def format_property_value(self, prop_name : str, todo : icalendar.Todo) -> str:

        result = ""

        if prop_name in todo:

            type_fact = icalendar.prop.TypesFactory()

            if type_fact.for_property(prop_name) is icalendar.prop.vDDDTypes:
                # Use vDDDTypes here as this is the default format for dates read by icalendar
                prop_value = icalendar.prop.vDDDTypes.from_ical(todo[prop_name])
                now = adapt_datetype(datetime.datetime.now(tz.gettz()), prop_value)

                result = prop_value.strftime(self.config.get_datetime_format())
                if isinstance(now, datetime.datetime):
                    result = prop_value.strftime(self.config.get_datetime_format())
                    result += " (" + humanize.naturaltime(prop_value, when=now) + ")"
                else:
                    result = prop_value.strftime(self.config.get_date_format())
                    result += " (" + humanize.naturalday(prop_value) + ")"

                #foo = datetime.datetime.now() + (now - prop_value)
                #result += " (" + str(humanize.naturaltime(foo)) + ")"

            elif type_fact.for_property(prop_name) is icalendar.prop.vText:
                prop_value = str(todo[prop_name])
                result = prop_value

            elif type_fact.for_property(prop_name) is icalendar.prop.vInt:
                prop_value = icalendar.vInt.from_ical(todo[prop_name])
                result = prop_value

            elif type_fact.for_property(prop_name) is icalendar.prop.vCategory:
                # TODO: from_ical vom vCategory throws an assertion error.
                #       We therefore convert it manually.
                prop_value = ",".join([str(c) for c in todo[prop_name].cats])
                result = prop_value

        if prop_name in todo['context']:

            if prop_name in Todo.TEXT_FILTER_PROPERTIES:
                prop_value = todo['context'][prop_name]
                result = prop_value

            elif prop_name in Todo.INT_FILTER_PROPERTIES:
                prop_value = todo['context'][prop_name]
                result = prop_value

        return result
