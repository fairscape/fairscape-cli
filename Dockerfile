ARG VERSION=3.11.6-slim

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:${VERSION}

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# add user to container
WORKDIR /fairscape_cli
#RUN adduser -u 5678 --disabled-password --gecos "" cliuser && \
#	chown -R cliuser /fairscape_cli
#USER cliuser

# build local code 
RUN pip install --upgrade pip

# copy local code
COPY . /fairscape_cli
# install local package
RUN pip install .

#CMD ["python", "fairscape_cli/main.py"]
