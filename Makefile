VERSION ?= 1.0

build:
	python -m build

push:
	python3 -m twine upload --repository pypi dist/*	

test:
	echo hello