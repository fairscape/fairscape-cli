The CLI is compatible with Python 3.8+. Installation of the CLI requires `pip` to be installed. In order to install from the 
source `git` is required.

- [python 3.8+](https://www.python.org/downloads/release/python-380/)
- [pip](https://pip.pypa.io/en/stable/installation/)
- [git](https://git-scm.com/downloads)

---
## Installation
---
`fairscape-cli` can be installed by any of the following three options:

### Install with `pip`

`fairscape-cli` is available on [PyPi](https://pypi.org/project/fairscape-cli/). Installation using pip is simple: 
  
  ```bash
  pip install fairscape-cli
  ```


### Install from the source

Clone the repository from Github 

  ```bash
  git clone https://github.com/fairscape/fairscape-cli.git
  ```

Go to the repository

  ```bash
  cd fairscape-cli
  ```

Install using `pip`

  ```bash
  python3 -m pip install .
  ```

---
## Test the CLI
---
Show all commands, arguments, and options

  ```bash
  fairscape-cli --help
  ```
  
  or if you cloned the repository

  ```bash
  python3 fairscape_cli/__main__.py --help
  ```

---

To use `fairscape-cli` go to the page [Getting Started](getting-started.md).