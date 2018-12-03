import sys
import os

from os.path import join
from setuptools import setup

__version__ = '1.2'


with open("README.md") as f:
    long_description = f.read()

if sys.version_info[0] < 3:
    dependencies = open(join('requirements', 'python2.txt')).read().split()
else:
    dependencies = open(join('requirements', 'python3.txt')).read().split()

if __name__ == "__main__":
    setup(
        name='garc',
        version=__version__,
        url='https://github.com/ChrisStevens/garc',
        author='Chris Stevens',
        author_email='chris.stevens@mail.utoronto.ca',
        packages=['garc',],
        description='Archive Gab.ai posts from the command line',
        long_description=long_description,
        long_description_content_type="text/markdown",
        install_requires=dependencies,
        setup_requires=['pytest-runner'],
        tests_require=['pytest'],
        entry_points={'console_scripts': ['garc = garc:main']}
    )