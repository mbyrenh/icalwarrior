<!--
SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>

SPDX-License-Identifier: GPL-3.0-or-later
-->

# 2. Enumerate ToDo items anew each time the program is called

Date: 2022-06-11

## Status

Accepted

Affected by [3. Store each todo item in a separate file](0003-store-each-todo-item-in-a-separate-file.md)

## Context

To make it easy to modify or delete existing ToDo items, it is desirable to have a short numeric identifier for every item. Icalendar items only have rather long, alphanumeric identifiers which are unsuitable for quick addressing of todo items by the user. 

## Decision

To avoid the need to maintain an additional assignment of a unique integer to each todo item in a separate database or index file, the program instead enumerates todo items in the order they are read during initalization. Thus, when the program is invoked, it assigns the index $n$ to the $n$-th item file read.

## Consequences

Whenever a todo item is added or removed from a calendar, the IDs assigned to one or more other items may change.
