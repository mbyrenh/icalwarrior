install: test
	pip install .

mypy:
	mypy icalwarrior/*.py

lint:
	flake8 icalwarrior/*.py

test:
	coverage run --source icalwarrior -m pytest icalwarrior/test
	mkdir -p out/coverage
	coverage html -d out/coverage

.PHONY: install test mypy lint
