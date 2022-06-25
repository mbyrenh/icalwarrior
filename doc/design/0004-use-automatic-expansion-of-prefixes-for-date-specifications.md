<!--
SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>

SPDX-License-Identifier: GPL-3.0-or-later
-->

# 4. Use automatic expansion of prefixes for date specifications

Date: 2022-06-11

## Status

Accepted

Related to [5. Use separate separator symbol for time specifications of relative dates](0005-use-separate-separator-symbol-for-time-specifications-of-relative-dates.md)

## Context

To reduce typing overhead, it is desirable to allow the user to type in unique prefixes when doing relative date specifications. For example, a user should be able to write

   todo add "Send reminder email to Joe" due:mon+2w

instead of having to write

   todo add "Send reminder email to Joe" due:monday+2weeks.

## Decision

Icalwarrior implements automatic expansion of unique prefixes within relative date specifications.

## Consequences

Relative date formats become harder to parse, as prefixes may instead of complete date words may be used.
