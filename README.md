<!--
SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>

SPDX-License-Identifier: GPL-3.0-or-later
-->

# Icalwarrior

Icalwarrior is a CLI task manager that uses the ical format for tasks, similar to [Todoman](https://github.com/pimutils/todoman). At the same time, Icalwarrior's command line interface is similar to the one from [Taskwarrior](https://taskwarrior.org/). As a consequence, Icalwarrior lets you work with your tasks with similar efficiency as Taskwarrior does while at the same time lets you profit from the many applications supporting ical-based task management. For example, you can synchronize your tasks with [Nextcloud](nextcloud.com) or [Radicale](https://radicale.org/) and manage your tasks on Android using [OpenTasks](https://opentasks.app/) or [Tasks.org](https://tasks.org/).

## Setup

### Build

After cloning the repository, Icalwarrior can be built and installed by calling `make`.

### Configuration

Unless a different path is specified via the `--config` command line option, Icalwarrior tries to read its configuration from the path
``
$HOME/.config/ical/config.yaml
``
. A sample for such a configuration file can be found in this repository.

## Usage

Given that a valid configuration file is given, just run `todo` to see a list of available commands together with a descriptive text.
To see the parameters expected by a given command `COM`, just run `todo COM`.

### Working with todo lists. 

Icalwarrior has been designed so that one can leverage tools like [vdirsyncer](https://github.com/pimutils/vdirsyncer) to synchronize todo items with a CalDAV server.
As a consequence, Icalwarrior supports management of multiple todo lists, where each todo list is represented by a separate directory. 

For example, given that the `lists_dir` value in the configuration file is set to `/home/user/mytodos`, the todo list directory may have the structure
``
/home/user/mytodos
├── home
├── party
├── projectA
└── projectB
``
where `home`, `party`, `projectA`, and `projectB` each represent a separate todo list in the form of a separate directory.

Similar to [Taskwarrior](https://taskwarrior.org/), Icalwarrior aims to minimize the typing overhead needed to do any modification to the todo list. To do so, Icalwarrior automatically detects commands, todo property names and todo lists as soon as a unique prefix is given.
For example, given the above todo lists, consider the case thet a new todo item with the summary `Buy drinks and snacks` is to be added to the `party` todo list. Without leveraging prefix detection, one can do so by running
``
todo add party "Buy drinks and snacks"
``.
Given that only the `add` command supported by Icalwarrior starts with the letter `a` and `pa` is a unique prefix for the `party` todo list among all of the above todo lists, one can instead write
``
todo a pa "Buy drinks and snacks"
``
to get the same result. If one wants to add a todo item with to the `home` todo list, it is even sufficient to write
``
todo a h "Do the laundry"
``

As the above example suggests, Icalwarrior needs at least a list name (or unique prefix of it) and a summary text to be able to create a new todo. However, Icalwarrior also supports setting of further todo properties. To obtain a list of the properties that Icalwarrior currently supports along with a specification of allowed values, one can call 
``
todo info properties
``.

In contrast to the summary text, the other properties need to be named explicitly when a value is to be assigned. For example, one may run
``
todo add party "Send invitations" description:"Jim,Laura,Anna,Mark,Tom,Sandra"
``
to add a todo which holds the names of the persons to be invited in the description field. However, similar to Taskwarrior, the unique prefix matching also applies to the properties, so that it is sufficient to run
``
todo a pa "Send invitations" de:"Jim, Laura, Anna, Mark, Tom, Sandra"
``

To furthermore enable writing and editing of description texts with multiple lines etc. in a text editor the `description` command can be used.

Another property for which specific functionality has been added are categories. While one may append `categories:catA,catB,catC` to a `todo add` or `todo modify` command to assign the categories `catA`, `catB` and `catC` to the todo item, this approach becomes cumbersome when one later on wants add another category to the same item or remove one. To support such cases, Icalwarrior interprets the `+` sign as prefix as indicator for addition of a category and `_` as indicator for removal of a category. For example, given that a todo with ID `1` exists to which the categories `catA` and `catB` have been assigned, one may run
``
todo mod 1 _catB +catC 
``
to remove the assignment to category `catB` and add an assignment to category `catC`. While using a minus sign for the removal of a category assignment would be more intuitive, Icalwarrior currently uses underscore for technical reasons, as the minus sign is misinterpreted as a command line option.

Another feature that Icalwarrior shares with Taskwarrior is that, additional to absolute date specifications, whose format is given by the `datetime_format` and `date_format` configuration file, Icalwarrior supports relative date specifications.
For example, if one plans to go shopping groceries on the coming Friday, one may run
``
todo add home "Buy groceries" due:friday
``
to let Icalwarrior create a todo item whose `due` property is set to the next friday starting from the current day.
Of course, unique prefix matching also applies for relative date specifications, so that
``
todo a h "Buy groceries" due:f
``

Furthermore, Icalwarrior also supports date calculations for relative dates. Given that in the above example, one actually wants to go shopping on the friday of the following week, one may instead run
``
todo add home "Buy groceries" due:friday+1week
``
or, more simply
``
todo a h "Buy groceries" due:f+1w.
``

To see a complete list of supported relative date specifications and calculation units, one can run
``
todo info dates.
``

### Caveats

Icalwarrior is designed to avoid additional bookkeeping that may become inconsistent, as documented in [ADR #2](doc/design/0002-enumerate-todo-items-anew-each-time-the-program-is-called.md). As a consequence, the assignment of IDs does not reflect the order in which the todo items were created but instead reflects the order in which they are read from disk. This means that when a new todo item is added, it is possible that an ID previously assigned to another item is assigned to the new item, while a new ID is assigned to the other item. As an example, consider the following scenario, where a user so far has created three todo items in a list called `home`:
``
Todo item with summary "Item A" has ID 1
Todo item with summary "Item B" has ID 2
Todo item with summary "Item C" has ID 3
``
When the user then runs `todo add home "Item D"`, it is possible that the assignment then looks as follows:
``
Todo item with summary "Item A" has ID 1
Todo item with summary "Item D" has ID 2
Todo item with summary "Item B" has ID 3
Todo item with summary "Item C" has ID 4
``

Similarly, if the user then deletes the item "Item A" by calling `todo delete 1`, then the assignment will look as follows:
``
Todo item with summary "Item D" has ID 1
Todo item with summary "Item B" has ID 2
Todo item with summary "Item C" has ID 3
``

To reduce the potential for errors due to this design decision, Icalwarrior implements the following features:
- The `delete` command supports multiple IDs to be given. Thus, given the above scenario with four items, the user may delete item "Item A" and "Item B" by calling `todo delete 1 3`. In contrast, calling `todo delete 1` and subsequently calling `todo delete 3` would delete the items "Item A" and "Item C".
- Every operation that affects the assignment of ID numbers displays a corresponding warning message after its execution.

### Showing todo lists

Also similar to [Taskwarrior](https://taskwarrior.org/) (although currently to a greatly lesser extent), Icalwarrior allows creation of customized reports, by specifying them in Icalwarrior's configuration file.
Examples for reports can be found in the sample configuration file.

The criteria which todo items are shown in a particular report are defined in the "constraint" value. The syntax to specify these criteria is very similar to the syntax used to set properties of todo items when using the `add` or `modify` command. However, it differs in two points:

- Properties can be extended with logical conditions, which are separated via a dot character. For example, when one wants to get all items that are due before the current day, one can write `due.before:today` and similarly `due.after:today` to get all items whose due date is later than the current day. A list of supported logical conditions for each supported property can be shown by calling `todo info filter`.
- Any pair of conditions may either be connected via `and` or via `or`. For convenience, if there is no such term between a pair of conditions, then Icalwarrior will interpret the conditions to be connected via `and`.

One peculiarity of the current implementation of reports is that todo items are colored based on their due date. In particular, a todo item is colored red, if its due date is more than seven days in the past from the current date, green if its due date is more than one day in the future and yellow otherwise.

## License

Icalwarrior is licensed under the GPL 3 license, using the [REUSE tool](https://reuse.software/) from the Free Software Foundation Europe.
