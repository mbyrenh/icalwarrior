# 3. Store each todo item in a separate file

Date: 2022-06-11

## Status

Accepted

Affects [2. Enumerate ToDo items anew each time the program is called](0002-enumerate-todo-items-anew-each-time-the-program-is-called.md)

## Context

Icalwarrior has been designed to support using [vdirsyncer](https://github.com/pimutils/vdirsyncer) to synchronize todo entries with a caldav server.

## Decision

Whenever a todo item is added to a calendar, a new file containing the todo item in ical format is created in the corresponding directory.

## Consequences

The program needs to read all files in the calendar directories each time it is invoked.
