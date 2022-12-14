# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Any
from pathlib import Path
import yaml

from yaml.scanner import ScannerError
import icalwarrior.constants as constants

class UnknownConfigurationOptionError(Exception):

    def __init__(self, option : str) -> None:
        self.option = option

    def __str__(self) -> str:
        return "Unknown configuration option \"" + self.option + "\""

class InvalidConfigurationFileError(Exception):

    def __init__(self, path: str) -> None:
        self.path = path

    def __str__(self) -> str:
        return "Config file " + self.path + " is not a valid YAML file."

class Configuration:

    def __init__(self, configFile : str) -> None:
        config_handle = open(configFile)

        try:
            self.config = yaml.load(config_handle, Loader=yaml.Loader)
        except ScannerError as err:
            raise InvalidConfigurationFileError(configFile) from err
        config_handle.close()

    @staticmethod
    def get_default_config_path() -> str:
        return str(Path.home()) + "/.config/ical/config.yaml"

    def get_config(self, option_path : List[str]) -> Any:
        option = self.config

        try:
            for element in option_path:
                option = option[element]
        except ValueError as err:
            raise UnknownConfigurationOptionError(element) from err

        return option

    def get_lists_dir(self) -> str:
        """Returns the path to a directory containing todo list directories."""

        result = []
        if 'lists_dir' in self.config:
            result = self.config['lists_dir']

        if not isinstance(result, str):
            raise Exception("Non-string type returned for 'lists_dir' configuration value.")

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
