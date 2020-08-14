from __future__ import print_function

import sys
import json
import signal
import codecs
import logging
import argparse
from garc import __version__
from garc.client import Garc
if sys.version_info[:2] <= (2, 7):
    # Python 2
    get_input = raw_input
    str_type = unicode
else:
    # Python 3
    get_input = input
    str_type = str


commands = [
    'configure',
    'help',
    'sample',
    'search',
    'user',
    'userposts',
    'usercomments',
    'followers',
    'following',
    'publicsearch',
    'prosearch',
    'featuredsearch'
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
        user_account=args.user_account,
        user_password=args.user_password,
        connection_errors=args.connection_errors,
        http_errors=args.http_errors,
        config=args.config,
        profile=args.profile)

    # calls that return gabs
    if command == "search":
        things = g.search(
            query,
            search_type=args.search_type,
            gabs=args.number_gabs
        )

    elif command == "configure":
        g.input_keys()
        sys.exit()
    elif command == 'user':
        things = g.user(query)

    elif command == 'userposts':
        things = g.userposts(
            query,
            gabs=args.number_gabs,
            gabs_after=args.gabs_after
        )
    elif command == 'usercomments':
        things = g.usercomments(query)
    elif command == 'followers':
        things = g.followers(query)
    elif command == 'following':
        things = g.following(query)
    elif command == 'publicsearch':
        things = g.public_search(
            query,
            gabs=args.number_gabs
        )
    elif command == 'prosearch':
        things = g.pro_search(
            query,
            gabs=args.number_gabs
        )
    elif command == 'featuredsearch':
        things = g.featured_search(
            query,
            gabs=args.number_gabs
        )
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
        if args.format == "json":
            print(json.dumps(thing), file=fh)
        logging.info("archived %s", thing['id'])

        # if 'post' in thing or 'username' in thing:
        #     # gabs and users
        #     if args.format == "json":
        #         print(json.dumps(thing), file=fh)
        #     logging.info("archived %s", thing['id'])

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
    parser.add_argument("--search_type", action="store", default="date",
                        dest="search_type", choices=["date"],
                        help="set search type")
    parser.add_argument("--number_gabs", action="store", type=int, default=-1,
                        dest="number_gabs",
                        help="approximate number of gabs to return")
    parser.add_argument("--gabs_after", action="store", default="2000-01-01",
                        dest="gabs_after",
                        help="approximate date of earliest gab you wish to collect")


    return parser
