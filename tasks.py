# -*- coding: utf-8 -*-
import sys
import webbrowser

from invoke import task, run

@task
def test(lint=True, watch=False, last_failing=False):
    import pytest
    if lint:
        flake()
    args = []
    if watch:
        args.append('-f')
    if last_failing:
        args.append('--lf')
    retcode = pytest.main(args)
    sys.exit(retcode)

@task(aliases=['lint'])
def flake():
    run('flake8 .', echo=True)

@task
def clean():
    run("rm -rf build")
    run("rm -rf dist")
    run("rm -rf environs.egg-info")
    print("Cleaned up.")

@task
def readme(browse=False):
    run("rst2html.py README.rst > README.html")
    if browse:
        webbrowser.open_new_tab('README.html')

@task
def publish(test=False):
    """Publish to the cheeseshop."""
    clean()
    if test:
        run('python setup.py register -r test sdist bdist_wheel', echo=True)
        run('twine upload dist/* -r test', echo=True)
    else:
        run('python setup.py register sdist bdist_wheel', echo=True)
        run('twine upload dist/*', echo=True)
