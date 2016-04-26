# -*- coding: utf-8 -*-
import re
import sys
from setuptools import setup
from setuptools.command.test import test as TestCommand

TESTS_REQUIRE = ['pytest']

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--verbose']
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ''
    with open(fname, 'r') as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError('Cannot find version information')
    return version

__version__ = find_version('environs.py')


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content

setup(
    name='environs',
    version=__version__,
    description=('simplified environment variable parsing'),
    long_description=(read('README.rst') + '\n\n' +
                        read('CHANGELOG.rst')),
    author='Steven Loria',
    author_email='sloria1@gmail.com',
    url='https://github.com/sloria/environs',
    install_requires=['marshmallow'],
    license='MIT',
    zip_safe=False,
    keywords='environment variables parsing',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    py_modules=['environs'],
    tests_require=TESTS_REQUIRE,
    cmdclass={'test': PyTest}
)
