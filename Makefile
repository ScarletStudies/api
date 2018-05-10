.PHONY: test coverage

test:
	pytest

coverage:
	coverage run -m pytest
	coverage report
	coverage html
	firefox htmlcov/index.html
