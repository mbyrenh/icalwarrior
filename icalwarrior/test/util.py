# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import os.path
from tempfile import NamedTemporaryFile, TemporaryDirectory, gettempdir

def setup_dummy_calendars(calendars):
    # Create temporary directory for calendars
    tmp_dir = TemporaryDirectory()
    tmp_dir_path = os.path.join(gettempdir(), tmp_dir.name)

    for cal in calendars:
        os.mkdir(os.path.join(tmp_dir_path, cal))

    # Create temporary config file
    config_file = NamedTemporaryFile(delete=False)
    config_file_path = os.path.join(gettempdir(), config_file.name)

    config_file.write(("calendars: " + tmp_dir.name + "\n").encode("utf-8"))
    config_file.write(("info_columns: uid,summary,created,categories,description\n").encode("utf-8"))
    config_file.close()

    return (tmp_dir, config_file_path)

def remove_dummy_calendars(tmp_dir, config_file_path):
    # Delete temporary config file
    os.remove(config_file_path)

    # Delete temporary directory
    tmp_dir.cleanup()
