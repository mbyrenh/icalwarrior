install: test
	pip install .

htmldoc:
	sphinx-build -b html doc/source doc/build/html

mypy:
	MYPYPATH=stubs mypy --python-executable venv/bin/python --exclude icalwarrior/test --exclude icalwarrior/perf --strict icalwarrior/

lint:
	flake8 icalwarrior/*.py

test:
	coverage run --source icalwarrior -m pytest icalwarrior/test
	mkdir -p out/coverage
	coverage html -d out/coverage

.PHONY: install test mypy lint htmldoc
