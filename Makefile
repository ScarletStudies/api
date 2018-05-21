.PHONY: test coverage

test:
	pytest -s

coverage:
	coverage run -m pytest
	coverage report
	coverage html
	firefox htmlcov/index.html


