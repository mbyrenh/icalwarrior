from typing import List
from pathlib import Path
import yaml

import icalwarrior.constants as constants

class UnknownConfigurationOptionError(Exception):

    def __init__(self, option : str) -> None:
        self.option = option

    def __str__(self) -> str:
        return "Unknown configuration option \"" + self.option + "\""


class Configuration:

    def __init__(self, configFile : str) -> None:
        config_handle = open(configFile)
        self.config = yaml.load(config_handle, Loader=yaml.Loader)
        config_handle.close()

    @staticmethod
    def get_default_config_path() -> str:
        return str(Path.home()) + "/.config/ical/config.yaml"

    def get_config(self, option_path : List[str]) -> object:
        option = self.config

        try:
            for element in option_path:
                option = option[element]
        except ValueError as err:
            raise UnknownConfigurationOptionError(element) from err

        return option

    def get_calendar_dir(self) -> List[str]:
        """Returns a list of paths containing calendar directories."""

        result = []
        if 'calendars' in self.config:
            result = self.config['calendars']
        return result

    def get_datetime_format(self) -> str:
        result = constants.DEFAULT_DATETIME_FORMAT
        if 'datetime_format' in self.config:
            result = self.config['datetime_format']
        return result

    def get_date_format(self) -> str:
        result = constants.DEFAULT_DATE_FORMAT
        if 'date_format' in self.config:
            result = self.config['date_format']
        return result

    def get_time_format_for_relative_dates(self) -> str:
        return constants.RELATIVE_DATE_TIME_FORMAT
