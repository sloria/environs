# -*- coding: utf-8 -*-
import sys

from invoke import task, run


@task
def test(ctx, lint=True, watch=False, last_failing=False):
    import pytest

    if lint:
        syntax(ctx)
    args = []
    if watch:
        args.append("-f")
    if last_failing:
        args.append("--lf")
    retcode = pytest.main(args)
    sys.exit(retcode)


@task
def syntax(ctx):
    """Run pre-commit hooks on codebase. Checks formatting and syntax."""
    ctx.run("pre-commit run --all-files --show-diff-on-failure", echo=True)


@task
def clean(ctx):
    run("rm -rf build")
    run("rm -rf dist")
    run("rm -rf environs.egg-info")
    print("Cleaned up.")
