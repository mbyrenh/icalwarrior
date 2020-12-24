from typing import List
from pathlib import Path
import yaml

class Configuration:

    default_date_format = "%Y-%m-%d"

    config = None

    def __init__(self, configFile : str) -> None:
        config_handle = open(configFile)
        self.config = yaml.load(config_handle, Loader=yaml.Loader)
        print(self.config)
        config_handle.close()

        print('Config is')
        print(self.config)

    @staticmethod
    def get_default_config_path() -> str:
        return str(Path.home()) + "/.config/ical/config.yaml"

    @staticmethod
    def get_default_data_path() -> str:
        return str(Path.home()) + "/.local/share/ical"

    def get_data_path(self) -> str:
        result = Configuration.get_default_data_path()
        if 'dataPath' in self.config:
            result = self.config['dataPath']
        return result

    def get_calendar_dir(self) -> List[str]:
        """Returns a list of paths containing calendar directories."""

        result = []
        if 'calendars' in self.config:
            result = self.config['calendars']
        return result

    def get_datetime_format(self) -> str:
        result = self.default_date_format
        if 'datetimeformat' in self.config:
            result = self.config['datetimeformat']
        return result


    def get_date_format(self) -> str:
        result = self.default_date_format
        if 'dateformat' in self.config:
            result = self.config['dateformat']
        return result
