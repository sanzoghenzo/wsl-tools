# Contributing

Your contribution is very welcome!
These are some guidelines to ensure that your changes are quickly accepted.

The goal is to write code that works, is secure and easy to read and understand.
To achieve that:

- limit the length of the lines of code to 80 chars
  (well, you don't need to worry about that as long as you use the [pre-commit check](#pre-commit-check));
- use typing annotation for all the functions and methods you write;
- document every public method and module using [google style docstring](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html);
- write `pytest` tests to ensure a 100% coverage.

## Setup

### Install development tools

Install `poetry`, and `pre-commit` in your default python (3.7+) distribution:

```shell
pip install poetry pre-commit
```

### clone the repository

Use `git` to clone the repo and enter the newly created directory:

```shell
git clone https://github.com/sanzoghenzo/wsl-tools
cd wsl-tools
```

### Initialize virtualenv

Simply run the following:

```shell
poetry install
```

It will create the virtualenv and install the dependencies.

<!-- prettier-ignore -->
!!! NOTE
    If you use conda, the command will use the currently active environment.

    To ensure an isolated environment,
    you should run `conda create -n wsl-tools python=3.7 poetry`
    and `conda activate wsl-tool` before `poetry install`.

### enable pre-commit hook

This will ensure that your code is checked before committing the changes:

```shell
pre-commit install
```

## Run tests

To run the test suite, simply run:

```shell
poetry run pytest
```

## Pre-commit check

You can manunally perform the checks that run before a commit via `pre commit --all-files`.

This will:

- auto-format code and docstrings;
- perform static and runtime type checking;
- run security check on the dependencies;
- run the tests and check there's 100% coverage.
