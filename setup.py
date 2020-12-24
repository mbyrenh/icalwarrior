from setuptools import setup, find_packages

setup(
    name="ical warrior",
    version=0.1,

    author="Martin Byrenheid",
    author_email="martin@byrenheid.net",

    packages=find_packages("src"),
    package_dir={"": "src"},

    install_requires=[
        'click',
        'icalendar',
        'tabulate',
        'colored'
    ],

    entry_points='''
        [console_scripts]
        itodo=itodo.__main__:cli
    '''
)
