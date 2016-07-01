# make this target from the root of the repo to run the unit tests
.PHONY: tests
tests:
	python -m unittest discover tests/
