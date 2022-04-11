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

## License

Icalwarrior is licensed under the GPL 3.0 license.
