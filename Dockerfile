ARG VERSION=3.8-slim
#ARG VERSION=3.11.6-slim
#ARG CLIVERSION=0.1.16a4

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:${VERSION}

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /fairscape_cli

# add user to container
#RUN adduser -u 5678 --disabled-password --gecos "" cliuser && \
#	chown -R cliuser /fairscape_cli
#USER cliuser

# build local code 
RUN pip install --upgrade pip

COPY pyproject.toml pyproject.toml
COPY dist/ dist/
COPY tests/ tests/
COPY tests/data tests/data
COPY examples/ examples/

COPY src/ src/
RUN pip install -e .
# copy built version

#RUN pip install dist/fairscape_cli-0.1.16a10-py3-none-any.whl
