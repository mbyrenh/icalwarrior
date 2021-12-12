from typing import List, Union,Tuple
from datetime import datetime, date, time, timedelta
class vText:
    pass

class vCategory:
    cats : List[vText]

class vInt:
    pass

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
    @classmethod
    def from_ical(cls, ical : object, timezone : object) -> Union[datetime,date,timedelta,time,Tuple[Union[date,datetime]],vDuration,vPeriod,vDatetime,vDate,vTime]: ...
