## Requirements

- [python 3.8+](https://www.python.org/downloads/release/python-380/)
- [Poetry](https://python-poetry.org/docs/#installation)
- [git](https://git-scm.com/downloads)

!!! note

    In order to ensure that poetry creates a [virtual environment](https://python-poetry.org/docs/configuration/#virtualenvsin-project) inside the project follow the steps below:

    Show the current poetry config:
    ``` console hl_lines="5"
    poetry config --list

    ...
    virtualenvs.create = true
    virtualenvs.in-project = false
    ...
    ```
    Set `virtualenvs.in-project` flag to `true`:
    ``` console 
    poetry config virtualenvs.in-project true
    ```
    The virtualenv will be created and expected in a folder named .venv within the root directory of the project


    


## Installation

- Clone the repository from Github 

    ```
    git clone https://github.com/fairscape/fairscape-cli.git
    ```

- Move to the directory

     ```
     cd fairscape-cli
     ```

- Install all the dependencies

    ```
    poetry install
    ```

- Activate virtual environment  

    ```
    source .venv/bin/activate
    ```

- Show all commands, arguments, and options

    ```
    fairscape-cli --help
    ```

    or 

    ```
    python fairscape_cli/main.py --help
    ```

Please see [Getting Started](getting-started.md) for further details.