VERSION ?= 1.0.1

build:
	#rm dist/*
	python3 -m build

push:
	python3 -m twine upload --repository fairscape-cli dist/*	

push-test:
	python3 -m twine upload --repository test-fairscape-cli dist/*	

test-script:
	./tests/bats/bin/bats tests/test.bats

test:
	#python3 -m build
	docker build -t fairscape-cli:$(VERSION) .
	docker run -it fairscape-cli:$(VERSION) bash ./tests/bats/bin/bats tests/test.bats


docker-build:
	docker build -t fairscape-cli:$(VERSION) --build-arg="CLIVERSION=$(VERSION)" .
	#docker build -t fairscape-cli:$(VERSION)-python3.10 --build-arg VERSION=3.10-slim .
	#docker build -t fairscape-cli:$(VERSION)-python3.9 --build-arg VERSION=3.9-slim .
	#docker build -t fairscape-cli:$(VERSION)-python3.8 --build-arg VERSION=3.8-slim .

docker-run:
	docker run -it fairscape-cli:$(VERSION) bash

docker-test: 
	docker run fairscape-cli:$(VERSION)-python3.11 ./tests/test_build.sh
	#docker run fairscape-cli:$(VERSION)-python3.10 ./tests/test_build.sh
	#docker run fairscape-cli:$(VERSION)-python3.9 ./tests/test_build.sh
	#docker run fairscape-cli:$(VERSION)-python3.8 ./tests/test_build.sh
