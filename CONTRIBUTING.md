# Contributing

## Setting up for development

Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/), then:

```console
$ uv sync
```

### (Optional but recommended) Install the pre-commit hooks

The pre-commit CLI was installed by the above steps.

```console
$ uv run pre-commit install
```

## To run tests

```console
$ uv run pytest
```

## To run syntax checks

```console
$ uv run tox -e lint
```
