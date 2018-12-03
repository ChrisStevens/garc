import os
import re
import sys
import logging
import time
import requests
from bs4 import BeautifulSoup

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

class Garc(object):
    """
    Garc allows you retrieve data from the Gab API.
    """

    def __init__(self, user_account=None, user_password=None,
                 connection_errors=0, http_errors=0, profile='main', config=None):
        """
        Create a Garc instance. If account informaton isn't given it will search for them.
        """

        self.user_account = user_account
        self.user_password = user_password
        self.connection_errors = connection_errors
        self.http_errors = http_errors
        self.cookie = None
        self.profile = profile
        self.search_types = ['date']



        if config:
            self.config = config
        else:
            self.config = self.default_config()

        self.check_keys()

    def search(self, q, search_type='date', gabs=-1):
        """
        Pass in a query. Defaults to recent sort by date.
        Defaults to retrieving as many historical gabs as possible.
        """
        # This can be expanded to other Gab search types
        if search_type in self.search_types:
            search_type = search_type
        else:
            search_type = 'date'

        num_gabs = 0
        while True:

            url = "https://gab.com/api/search?q=%s&sort=%s&before=%s" % (q, search_type, num_gabs)

            resp = self.get(url)

            # We should probably implement some better error catching
            # not simply checking for a 500 to know we've gotten all the gabs possible
            if resp.status_code == 500:
                logging.error("search for %s failed, recieved 500 from Gab.com", (q))
                break
            elif resp.status_code == 429:
                logging.warn("rate limited, sleeping two minutes")
                time.sleep(100)
                continue

            posts = resp.json()['data']

            # API seems to be more stable than previously and will not send 500
            # as it runs out of data, now returns empty results
            if not posts:
                logging.info("No more posts returned for search: %s", (q))
                break

            for post in posts:
                yield post
            num_gabs += len(posts)
            if  (num_gabs > gabs and gabs != -1):
                break


    def user(self, q):
        """
        collect user json data
        """
        url = 'https://gab.com/users/%s' % (q)
        resp = self.get(url)
        yield resp.json()


    def userposts(self, q, gabs=-1, gabs_after='2000-01-01'):
        """
        collect posts from a user feed
        """
        base_url = "https://gab.com/api/feed/%s" % (q)
        url = base_url
        num_gabs = 0
        while True:
            resp = self.get(url)
            posts = resp.json()["data"]
            if not posts:
                break
            last_published_date = posts[-1]['published_at']

            url = base_url + '?before=%s' % (last_published_date)
            for post in posts:
                yield post
            num_gabs += len(posts)
            if last_published_date < gabs_after:
                break
            if  (num_gabs > gabs and gabs != -1):
                break

    def usercomments(self, q):
        """
        collect comments from a users feed
        """
        base_url = "https://gab.com/api/feed/%s/comments?includes=post.conversation_parent" % (q)
        url = base_url
        while True:

            resp = self.get(url)
            posts = resp.json()["data"]
            if not posts:
                break
            last_published_date = posts[-1]['published_at']
            url = base_url + '&before=%s' % (last_published_date)
            for post in posts:
                yield post

    def login(self):
        """
        Login to Gab to retrieve needed session token.
        """
        if not (self.user_account and self.user_password):
            raise RuntimeError("MissingAccountInfo")

        if self.cookie:
            logging.info("refreshing login cookie")

        url = "https://gab.com/auth/login"
        input_token = requests.get('https://gab.com/auth/login')
        page_info = BeautifulSoup(input_token.content, "html.parser")
        token = page_info.select('input[name=_token]')[0]['value']
        payload = {'username':self.user_account, 'password':self.user_password, '_token':token}

        d = requests.request("POST", url, params=payload, cookies=input_token.cookies)
        laravel_session = re.search('"id_token": "(.+)" }', d.content.decode('utf-8')).group(1)
        self.cookie = {'laravel_session': laravel_session}

    def get(self, url, **kwargs):
        """
        Perform the API requests
        """
        if not self.cookie:
            self.login()

        connection_error_count = kwargs.pop('connection_error_count', 1)
        try:
            logging.info("getting %s %s", url, kwargs)

            r = requests.get(url, cookies=self.cookie)
            # Maybe should implement allow_404 that stops retrying, ala twarcf

            if r.status_code == 404:
                logging.warn("404 from Gab API! trying again")
                time.sleep(10)
                r = self.get(url, **kwargs)
            return r
        except requests.exceptions.ConnectionError as e:
            connection_error_count += 1
            logging.error("caught connection error %s on %s try", e,
                          connection_error_count)
            if (self.connection_errors and
                    connection_error_count == self.connection_errors):
                logging.error("received too many connection errors")
                raise e
            else:
                self.connect()
                kwargs['connection_error_count'] = connection_error_count
                return self.get(url, **kwargs)

    def check_keys(self):
        """
        Get the Gab account info. Order of precedence is command line,
        environment, config file. Return True if all the keys were found
        and False if not.
        """
        env = os.environ.get
        if not self.user_account:
            self.user_account = env('GAB_ACCOUNT')
        if not self.user_password:
            self.user_password = env('GAB_PASSWORD')


        if self.config and not (self.user_account and
                                self.user_password):
            self.load_config()

        return self.user_password and self.user_password

    def load_config(self):
        """
        Attempt to load gab info from config file
        """
        path = self.config
        profile = self.profile
        logging.info("loading %s profile from config %s", profile, path)

        if not path or not os.path.isfile(path):
            return {}

        config = configparser.ConfigParser()
        config.read(self.config)
        data = {}
        for key in ['user_account', 'user_password']:
            try:
                setattr(self, key, config.get(profile, key))
            except configparser.NoSectionError:
                sys.exit("no such profile %s in %s" % (profile, path))
            except configparser.NoOptionError:
                sys.exit("missing %s from profile %s in %s" % (
                    key, profile, path))
        return data

    def save_config(self):
        """
        Save new config file
        """
        if not self.config:
            return
        config = configparser.ConfigParser()
        config.add_section(self.profile)
        config.set(self.profile, 'user_account', self.user_account)
        config.set(self.profile, 'user_password', self.user_password)
        with open(self.config, 'w') as config_file:
            config.write(config_file)

    def input_keys(self):
        """
        Create new config file with account info
        """
        print("\nPlease enter Gab account info.\n")

        def i(name):
            return get_input(name.replace('_', ' ') + ": ")

        self.user_account = i('user_account')
        self.user_password = i('password')
        self.save_config()

    def default_config(self):
        """
        Default config file path
        """
        return os.path.join(os.path.expanduser("~"), ".garc")
