from typing import List, Union, Tuple, Any
from datetime import datetime, date, time, timedelta
class vText:
    @classmethod
    def from_ical(cls, ical : str) -> int: ...

class vCategory:
    cats : List[str]

    @staticmethod
    def from_ical(ical : str) -> List[str]: ...

class vInt:
    @classmethod
    def from_ical(cls, ical: str) -> int: ...

class vDuration:
    pass

class vPeriod:
    pass

class vDatetime:
    pass

class vDate:
    pass

class vTime:
    pass

class vDDDTypes:

    def __init__(self, dt : object): ...

    @classmethod
    def from_ical(cls, ical : object, timezone : object = None) -> Union[datetime,date,timedelta,time,Tuple[Union[date,datetime]],vDuration,vPeriod,vDatetime,vDate,vTime]: ...

class TypesFactory:
    def for_property(self, name : str) -> Any: ...
