# -*- coding: utf-8 -*-
import re
from setuptools import setup

REQUIRES = [
    'marshmallow>=2.7.0',
    'read_env>=1.1.0',
]

def find_version(fname):
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
    py_modules=['environs'],
    version=__version__,
    description=('simplified environment variable parsing'),
    long_description=(read('README.rst') + '\n\n' +
                        read('CHANGELOG.rst')),
    author='Steven Loria',
    author_email='sloria1@gmail.com',
    url='https://github.com/sloria/environs',
    install_requires=REQUIRES,
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
