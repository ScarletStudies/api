IMAGE_NAME ?= ssapi
CONTAINER_NAME ?= ssapi
CONTAINER_INSTANCE ?= default

PORTS ?= -p 8081:80

.PHONY: build irun drun stop test coverage

build: Dockerfile
	docker build -t $(IMAGE_NAME) -f Dockerfile .

irun:
	docker run --rm -it $(PORTS) $(IMAGE_NAME)

drun:
	docker run --rm --name $(CONTAINER_NAME)-$(CONTAINER_INSTANCE) -d $(PORTS) $(IMAGE_NAME)

stop:
	docker stop $(CONTAINER_NAME)-$(CONTAINER_INSTANCE)

test:
	pytest -s

coverage:
	coverage run -m pytest
	coverage report
	coverage html
	firefox htmlcov/index.html

default: build
