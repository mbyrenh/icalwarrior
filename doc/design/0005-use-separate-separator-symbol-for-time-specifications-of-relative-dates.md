# 5. Use separate separator symbol for time specifications of relative dates

Date: 2022-06-11

## Status

Accepted

Related to [4. Use automatic expansion of prefixes for date specifications](0004-use-automatic-expansion-of-prefixes-for-date-specifications.md)

## Context

It is desirable to support time specifications also for relative date specifications. However, when doing so, the symbol separating the date from the time specification must be chosen in a way that avoids ambiguity.

## Decision

The character "@" is chosen as separator symbol for time specifications in relative dates.

## Consequences

It may be confusing to the user to use a different symbol to distinguish the time from the date in a relative date specification than in an absolute date specification.
