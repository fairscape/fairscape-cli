VERSION ?= 0.1.16a4

buildpackage:
	python3 -m build

push:
	python3 -m twine upload --repository pypi dist/*	

push-test:
	python3 -m twine upload --repository test-fairscape-cli dist/*	

test:
	python3 -m build
	docker build -t fairscape-cli:$(VERSION)-python3.11 --build-arg="CLIVERSION=0.1.16a4" .
	docker run -it fairscape-cli:$(VERSION)-python3.11 bash ./tests/test_build.sh


docker-build:
	docker build -t fairscape-cli:$(VERSION)-python3.11 --build-arg="CLIVERSION=0.1.16a4" .
	#docker build -t fairscape-cli:$(VERSION)-python3.10 --build-arg VERSION=3.10-slim .
	#docker build -t fairscape-cli:$(VERSION)-python3.9 --build-arg VERSION=3.9-slim .
	#docker build -t fairscape-cli:$(VERSION)-python3.8 --build-arg VERSION=3.8-slim .

docker-run:
	docker run -it fairscape-cli:$(VERSION)-python3.11 bash

docker-test: 
	docker run fairscape-cli:$(VERSION)-python3.11 ./tests/test_build.sh
	#docker run fairscape-cli:$(VERSION)-python3.10 ./tests/test_build.sh
	#docker run fairscape-cli:$(VERSION)-python3.9 ./tests/test_build.sh
	#docker run fairscape-cli:$(VERSION)-python3.8 ./tests/test_build.sh
