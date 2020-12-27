install: test
	pip install .

test:
	pytest icalwarrior/test

.PHONY: install test
