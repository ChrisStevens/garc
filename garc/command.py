from __future__ import print_function

import os
import re
import sys
import json
import signal
import codecs
import logging
import datetime
import argparse
import fileinput
from IPython import embed

from garc import __version__
from garc.client import Garc

if sys.version_info[:2] <= (2, 7):
    # Python 2
    get_input = raw_input
    str_type = unicode
    import ConfigParser as configparser
else:
    # Python 3
    get_input = input
    str_type = str
    import configparser


commands = [
    'configure',
    'help',
    'sample',
    'search',
]


def main():
    parser = get_argparser()
    args = parser.parse_args()

    command = args.command
    query = args.query or ""

    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # catch ctrl-c so users don't see a stack trace
    signal.signal(signal.SIGINT, lambda signal, frame: sys.exit(0))

    if command == "version":
        print("garc v%s" % __version__)
        sys.exit()
    elif command == "help" or not command:
        parser.print_help()
        print("\nPlease use one of the following commands:\n")
        for cmd in commands:
            print(" - %s" % cmd)
        print("\nFor example:\n\n    garc search make america great again")
        sys.exit(1)

    g = Garc(
        user_account = args.user_account,
        user_password = args.user_password,

        connection_errors=args.connection_errors,
        http_errors=args.http_errors,
        config=args.config,
        profile=args.profile    )

    # calls that return tweets
    if command == "search":
        things = g.search(
            query,
            search_type=args.search_type
        )

    elif command == "configure":
        g.input_keys()
        sys.exit()

    else:
        parser.print_help()
        print("\nPlease use one of the following commands:\n")
        for cmd in commands:
            print(" - %s" % cmd)
        print("\nFor example:\n\n    garc search make america great again")
        sys.exit(1)

    # get the output filehandle
    if args.output:
        fh = codecs.open(args.output, 'wb', 'utf8')
    else:
        fh = sys.stdout


    
    for thing in things:

        kind_of = type(thing)
        if 'post' in thing:
            # tweets and users
            if (args.format == "json"):
                print(json.dumps(thing), file=fh)
            elif (args.format == "csv"):
                csv_writer.writerow(get_row(thing))
            logging.info("archived %s", thing['id'])

def get_argparser():
    """
    Get the command line argument parser.
    """

    parser = argparse.ArgumentParser("garc")
    parser.add_argument('command', choices=commands)
    parser.add_argument('query', nargs='?', default=None)
    parser.add_argument("--log", dest="log",
                        default="garc.log", help="log file")
    parser.add_argument("--user_account",
                        default=None, help="Gab account name")
    parser.add_argument("--user_password",
                        default=None, help="Gab account password")
    parser.add_argument('--config',
                        help="Config file containing Gab account info")
    parser.add_argument('--profile', default='main',
                        help="Name of a profile in your configuration file")
    parser.add_argument('--warnings', action='store_true',
                        help="Include warning messages in output")
    parser.add_argument("--connection_errors", type=int, default="0",
                        help="Number of connection errors before giving up")
    parser.add_argument("--http_errors", type=int, default="0",
                        help="Number of http errors before giving up")
    parser.add_argument("--output", action="store", default=None,
                        dest="output", help="write output to file path")
    parser.add_argument("--format", action="store", default="json",
                        dest="format", choices=["json"],
                        help="set output format")



    return parser