# SPDX-FileCopyrightText: 2022 Martin Byrenheid <martin@byrenheid.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

install:
	pip install .

htmldoc:
	sphinx-build -b html doc/source doc/build/html

mypy:
	mkdir -p out/mypy
	MYPYPATH=stubs mypy --html-report out/mypy --exclude icalwarrior/test --exclude icalwarrior/perf --strict icalwarrior/

lint:
	flake8 icalwarrior/*.py

test:
	coverage run --source icalwarrior -m pytest icalwarrior/test
	mkdir -p out/coverage
	coverage html -d out/coverage

.PHONY: install test mypy lint htmldoc
