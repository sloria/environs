# Contributing

## Setting up for development

with `venv`:

```console
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -e '.[dev]'
```

with [`uv`](https://docs.astral.sh/uv/getting-started/installation/):

```console
$ uv sync --frozen --extra dev
$ source .venv/bin/activate
```

### (Optional but recommended) Install the pre-commit hooks

The pre-commit CLI was installed by the above steps

```console
$ pre-commit install
```

## To run tests

```console
$ pytest
```

## To run syntax checks

```console
$ tox -e lint
```
