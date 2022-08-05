import os
import os.path
from tempfile import NamedTemporaryFile, gettempdir
import pytest
from icalwarrior.configuration import Configuration, InvalidConfigurationFileError

def test_invalid_config_file_unterminated_string():

    config_file = NamedTemporaryFile()
    config_file_path = os.path.join(gettempdir(), config_file.name)
#    config_file.write(b'foo: 33 bar:')
    config_file.write(b'foo: "Hello')
    config_file.flush()

    with pytest.raises(InvalidConfigurationFileError):
        config = Configuration(config_file_path)

def test_invalid_config_file_format():

    config_file = NamedTemporaryFile()
    config_file_path = os.path.join(gettempdir(), config_file.name)
    config_file.write(b'foo: 33 bar:')
    config_file.flush()

    with pytest.raises(InvalidConfigurationFileError):
        config = Configuration(config_file_path)
