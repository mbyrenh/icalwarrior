import icalendar

class Todo:

    PARAM_SEPARATOR = ':'

    # Each key denotes the parameter name
    # for the command line parameter and the corresponding
    # value denotes the ical property name.
    SUPPORTED_PROPERTIES = {
        'due' : 'due'
    }

    def __init__(self, calendar : str, id : int, icalTodo : icalendar.Todo) -> None:
        self.calendarName = calendar
        self.id = id
        self.icalTodo = icalTodo

    def getCalendar(self) -> str:
        return self.calendarName

    def getIcalTodo(self) ->  icalendar.Todo:
        return self.icalTodo

    def getID(self) -> int:
        return self.id
