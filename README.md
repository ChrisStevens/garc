garc
=====

Garc is a python library and command line tool for collecting JSON data from Gab.ai

Garc is built based on the wonderful [twarc](https://github.com/DocNow/twarc) project published by the Documneting the Now project. Inspiration for structure, usage and outputs are from twarc, and garc is intended to be used for similar purposes.

Garc is still very much a work in progress, and is being constantly updated to add deeper functionality and as new features and changes are implemented by Gab.


## Warnings

Gab's api is relatively sparsely documented, so things may change without warning and break searches.

Please be respectful when using this and any data collection software, try not to make excessive searches and calls.


## Installation

Currently the garc package hasn't been uploaded to PIP (that is top of our next steps), so installation must be done directly from github.

This is done doing the following command `pip install git+git://github.com/ChrisStevens/garc.git`


## Usage

First you need to give garc your account information:

    garc configure

You can then try out any search, for example:

    garc search maga

