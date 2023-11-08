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
