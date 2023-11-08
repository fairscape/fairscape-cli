VERSION ?= 0.1.7a4

build:
	python -m build

push:
	python3 -m twine upload --repository pypi dist/*	

docker-build:
	docker build -t fairscape-cli:$VERSION .

docker-test:
	docker run fariscape-cli:$VERSION pytest tests/test_rocrate.py