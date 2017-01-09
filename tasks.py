# -*- coding: utf-8 -*-
import sys
import webbrowser

from invoke import task, run

@task
def test(ctx, lint=True, watch=False, last_failing=False):
    import pytest
    if lint:
        flake(ctx)
    args = []
    if watch:
        args.append('-f')
    if last_failing:
        args.append('--lf')
    retcode = pytest.main(args)
    sys.exit(retcode)

@task(aliases=['lint'])
def flake(ctx):
    run('flake8 .', echo=True)

@task
def clean(ctx):
    run('rm -rf build')
    run('rm -rf dist')
    run('rm -rf environs.egg-info')
    print("Cleaned up.")

@task
def readme(ctx, browse=False):
    run('rst2html.py README.rst > README.html')
    if browse:
        webbrowser.open_new_tab('README.html')

@task
def publish(ctx, test=False):
    """Publish to the cheeseshop."""
    clean(ctx)
    if test:
        run('python setup.py register -r test sdist bdist_wheel', echo=True)
        run('twine upload dist/* -r test', echo=True)
    else:
        run('python setup.py register sdist bdist_wheel', echo=True)
        run('twine upload dist/*', echo=True)
