from typing import List, Dict
from os import listdir, mkdir
from os.path import isdir, isfile
import _pickle as pickle

import icalendar

from todo import Todo
from configuration import Configuration

class DuplicateCalendarNameError(Exception):

    def __init__(self, calendarName : str, firstCalDir : str, secondCalDir : str) -> None:
        self.calendarName = calendarName
        self.firstCalDir = firstCalDir
        self.secondCalDir = secondCalDir

    def __str__(self):
        return ("Duplicate name '" + self.calendarName + "' found in " + self.firstCalDir + " and " + self.secondCalDir)

class Calendars:

    index_file = "todo.index"

    def __init__(self, config : Configuration) -> None:
        self.config = config

        self.calendars = self.scanCalendars()

        # TODO: Read calendars and create mapping from calendar-UID to obj-ID for events and for todos
        #       And identify missing numbers.
        if not isdir(self.config.getDataPath()):
            mkdir(self.config.getDataPath())

        if not isfile(self.config.getDataPath() + "/" + self.index_file):
            print("Building index...")
            self.__buildIndex()
            print("Completed")

        self.__loadIndexes()

    def __loadIndexes(self) -> None:

        with open(self.config.getDataPath() + "/" + self.index_file, 'rb') as indexFile:
            self.todoIndex = pickle.load(indexFile)

    def __buildIndex(self) -> None:

        assert isdir(self.config.getDataPath())

        evID = 1
        eventMapping = {}
        todoID = 1
        todoMapping = {}

        for currentCalendar in self.calendars:
            calFiles = listdir(self.calendars[currentCalendar])
            for calFile in calFiles:
                with open(self.calendars[currentCalendar] + '/' + calFile, 'r') as icalFile:
                    iCalendar = icalendar.Calendar.from_ical(icalFile.read())
                    for event in iCalendar.walk('vevent'):
                        eventMapping[currentCalendar + "-" + event.get('uid')] = evID
                        evID += 1
                    for todo in iCalendar.walk('vtodo'):
                        todoMapping[currentCalendar + "-" + todo.get('uid')] = todoID
                        todoID += 1

        with open(self.config.getDataPath() + "/" + self.index_file, 'wb') as indexFile:
            pickle.dump(todoMapping, indexFile)

    def scanCalendars(self) -> Dict[str, str]:
        result = {}
        calDir = self.config.getCalendarDir()
        calNames = listdir(calDir)
        for name in calNames:
            calPath = calDir + "/" + name
            if name in result:
                raise DuplicateCalendarNameError(name, result[name], calPath)
            else:
                result[name] = calPath 
        return result

    def calendarExists(self, calendar : str) -> bool:
        if calendar in self.calendars:
            return True
        else:
            return False

    def getCalendars(self) -> List[str]:
        return self.calendars.keys()

    def getToDos(self, calendar = None) -> List[Todo]:

        assert calendar is None or self.calendarExists(calendar)

        relevantCalendars = self.calendars.keys()
        if not calendar == None:
            relevantCalendars = [calendar]

        result = []

        for currentCalendar in relevantCalendars:
            calFiles = listdir(self.calendars[currentCalendar])
            for calFile in calFiles:
                icalFile = open(self.calendars[currentCalendar] + '/' + calFile, 'r')
                iCalendar = icalendar.Calendar.from_ical(icalFile.read())
                for todo in iCalendar.walk('vtodo'):
                    result += [Todo(currentCalendar, self.todoIndex[currentCalendar + "-" + todo.get("uid")], todo)]
                icalFile.close()

        return result

    def __getNewTodoID(self) -> int:

        existingIDs = set(self.todoIndex.values())
        IDrange = set(range(1, max(existingIDs)+2))
        freeID = min(IDrange.difference(existingIDs))
        return(freeID)
