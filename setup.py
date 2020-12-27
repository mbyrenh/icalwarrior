from setuptools import setup, find_packages

setup(
    name="icalwarrior",
    version=0.1,

    author="Martin Byrenheid",
    author_email="martin@byrenheid.net",

    packages=find_packages(include=["icalwarrior", "icalwarrior.*"]),

    install_requires=[
        'click',
        'icalendar',
        'tableformatter',
        'colorama',
        'termcolor',
        'pyyaml',
        'humanize',
        'pytest'
    ],

    entry_points='''
        [console_scripts]
        todo=icalwarrior.__main__:main
    '''
)
