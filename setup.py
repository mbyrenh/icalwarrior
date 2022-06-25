# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import setup, find_packages

setup(
    name="icalwarrior",
    version=0.1,

    author="Martin Byrenheid",
    author_email="martin@byrenheid.net",

    packages=find_packages(include=["icalwarrior", "icalwarrior.*"]),

    install_requires=[
        'mypy',
        'lxml',
        'click',
        'icalendar',
        'tableformatter',
        'colorama',
        'termcolor',
        'pyyaml',
        'humanize',
        'pytest',
        'coverage',
        'flake8',
        'types-PyYAML',
        'types-python-dateutil',
        'types-termcolor',
        'types-colorama'
    ],

    entry_points='''
        [console_scripts]
        todo=icalwarrior.__main__:main
    '''
)
