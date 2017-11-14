import sys
import os

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.md') as changelog_file:
    changelog = changelog_file.read()

config = {
    'name': 'reportek',
    'version': '0.0.1',
    'description': 'EIONET national repository',
    'long_description': readme + '\n\n' + changelog,
    'author': 'Eau de Web',
    'url': 'https://github.com/eea/reportek.git',
    'download_url': 'https://github.com/eea/kraken.git',
    'author_email': 'something@somewhere.eu',
    'setup_requires': pytest_runner,
    'tests_require': ['pytest'],
    'packages': find_packages(),
    'scripts': [],
    'entry_points': {
        'console_scripts': []
    }
}

setup(**config)
