import re
from setuptools import setup

INSTALL_REQUIRES = ["marshmallow>=2.7.0", "python-dotenv"]
DJANGO_REQUIRES = ["dj-database-url", "dj-email-url"]
EXTRAS_REQUIRE = {
    "django": DJANGO_REQUIRES,
    "tests": ["pytest"] + DJANGO_REQUIRES,
    "lint": ["flake8==3.7.7", "flake8-bugbear==19.3.0", "pre-commit~=1.17"],
}
EXTRAS_REQUIRE["dev"] = EXTRAS_REQUIRE["tests"] + EXTRAS_REQUIRE["lint"] + ["tox"]
PYTHON_REQUIRES = ">=3.5"


def find_version(fname):
    version = ""
    with open(fname, "r") as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError("Cannot find version information")
    return version


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name="environs",
    py_modules=["environs"],
    version=find_version("environs.py"),
    description="simplified environment variable parsing",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Steven Loria",
    author_email="sloria1@gmail.com",
    url="https://github.com/sloria/environs",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    license="MIT",
    zip_safe=False,
    python_requires=PYTHON_REQUIRES,
    keywords="environment variables parsing config configuration 12factor envvars",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    project_urls={
        "Issues": "https://github.com/sloria/environs/issues",
        "Changelog": "https://github.com/sloria/environs/blob/master/CHANGELOG.md",
    },
)
