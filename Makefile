.PHONY: test coverage flask

coverage:
	coverage run -m pytest
	coverage report
	coverage html
	firefox htmlcov/index.html

flask:
	SSAPI_SETTINGS="$(shell pwd)/env/$(E).env" flask $(A)

test:
	SSAPI_SETTINGS="$(shell pwd)/env/test.env" pytest -s $(F)
