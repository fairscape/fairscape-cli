# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11.4

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install pipx 
RUN python3 -m pipx ensurepath
RUN pipx install poetry 
RUN export PATH=":$PATH"

WORKDIR /fairscape_cli
COPY . /fairscape_cli

RUN /root/.local/bin/poetry install

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
#RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
#USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
#CMD ["python", "fairscape_cli/main.py"]