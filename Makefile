VERSION ?= 0.1.8

build:
	python -m build

push:
	python3 -m twine upload --repository pypi dist/*	


docker-build:
	docker build -t fairscape-cli:$(VERSION)-python3.11 .
	docker build -t fairscape-cli:$(VERSION)-python3.10 --build-arg VERSION=3.10-slim .
	docker build -t fairscape-cli:$(VERSION)-python3.9 --build-arg VERSION=3.9-slim .
	docker build -t fairscape-cli:$(VERSION)-python3.8 --build-arg VERSION=3.8-slim .

docker-test: 
	docker run fairscape-cli:$(VERSION)-python3.11 ./tests/test_build.sh
	docker run fairscape-cli:$(VERSION)-python3.10 ./tests/test_build.sh
	docker run fairscape-cli:$(VERSION)-python3.9 ./tests/test_build.sh
	docker run fairscape-cli:$(VERSION)-python3.8 ./tests/test_build.sh