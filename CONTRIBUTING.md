# Contributing

## Setting up for development

- Create and activate a new Python 3 virtual environment
- `pip install -e '.[dev]'`
- (Optional but recommended) Install the pre-commit hooks, which will
  format and lint your git staged files:

```
# The pre-commit CLI was installed above
pre-commit install
```

- To run tests:

```
pytest
```

- To run syntax checks:

```
tox -e lint
```

- (Optional) To run tests on Python 3.5, 3.6, and 3.7 virtual environments (must have each interpreter installed):

```
tox
```
