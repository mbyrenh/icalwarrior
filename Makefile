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

reuse:
	reuse lint

test:
	coverage run --source icalwarrior -m pytest icalwarrior/test
	mkdir -p out/coverage
	coverage html -d out/coverage

clean:
	rm -rf build
	rm -rf out
	rm -rf icalwarrior.egg-info
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf .coverage

.PHONY: install test mypy lint htmldoc reuse
