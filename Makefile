install: test
	pip install .

mypy:
	mypy icalwarrior/*.py

lint:
	flake8 icalwarrior/*.py

test:
	pytest icalwarrior/test

.PHONY: install test mypy lint
