# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11.6-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

WORKDIR /fairscape_cli
COPY . /fairscape_cli

# add user to container
RUN adduser -u 5678 --disabled-password --gecos "" cliuser && \
	chown -R cliuser /fairscape_cli
USER cliuser

# install poetry dependencies
RUN python3 -m pip install --upgrade pip && \
	python3 -m pip install pipx 
RUN python3 -m pipx ensurepath
RUN export PATH="/home/cliuser/.local/bin:$PATH"
	
RUN /home/cliuser/.local/bin/pipx install poetry 

# install all fairscape cli dependencies
RUN /home/cliuser/.local/bin/poetry install


# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
#CMD ["python", "fairscape_cli/main.py"]
