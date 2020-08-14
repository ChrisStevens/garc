import os
import re
import sys
import logging
import time
import requests
import datetime
from bs4 import BeautifulSoup
import html
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
        self.access_token = None



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
        max_id = ''
        while True:

            # url = "https://gab.com/api/search?q=%s&sort=%s&before=%s" % (q, search_type, num_gabs)
            url = "https://gab.com/api/v1/timelines/tag/%s?max_id=%s" % (q, max_id)
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
            posts = resp.json()

            # API seems to be more stable than previously and will not send 500
            # as it runs out of data, now returns empty results
            if not posts:
                logging.info("No more posts returned for search: %s", (q))
                break
            max_id = posts[-1]['id']
            for post in posts:
                yield post
            num_gabs += len(posts)
            if  (num_gabs > gabs and gabs != -1):
                break

    def pro_search(self, q,  gabs=-1,gabs_after=(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M")):
        """
        Pass in a query. 
        Searches the pro Gab timeline for posts which match query q
        Match is case insensitive
        """

        num_gabs = 0
        max_id = ''
        while True:
            url = "https://gab.com/api/v1/timelines/pro?limit=40&max_id=%s" % (max_id)  
            resp = self.get(url)
            # time.sleep(1)

            # We should probably implement some better error catching
            # not simply checking for a 500 to know we've gotten all the gabs possible
            if resp.status_code == 500:
                logging.error("search for %s failed, recieved 500 from Gab.com", (q))
                return
            elif resp.status_code == 429:
                logging.warn("rate limited, sleeping two minutes")
                time.sleep(100)
                break
            posts = resp.json()

            # API seems to be more stable than previously and will not send 500
            # as it runs out of data, now returns empty results
            if not posts:
                logging.info("No more posts returned for search: %s", (q))
                break

            for post in posts:
                if self.search_gab_text(post,q):
                    yield self.format_post(post)
                max_id = post['id']
                max_created_at = post['created_at']
            num_gabs += len(posts)
            if  (num_gabs > gabs and gabs != -1):
                logging.info("Number of gabs condition met: %s", (q))
                break

            # Check if first collected gab is after the date specified
            # The API returns strange results sometimes where gabs are not in date order, so ocassionally random dates pop up
            # But these never seem to appear at the start, so checking the first item keeps the function from prematurely ending
            # It does mean an additional call is made however
            if posts[0]['created_at'] < gabs_after:
                if posts[1]['created_at'] < gabs_after:
                    if posts[2]['created_at'] < gabs_after:
                        if posts[-1]['created_at'] < gabs_after:

                            logging.info("Gabs after condition met: %s", (q))

                            break





    def featured_search(self, q,  gabs=-1,gabs_after=(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M")):
        """
        Pass in a query. 
        Searches the various featured Gab timeline for posts which match query q
        Match is case insensitive
        """
        # As the feeds are non-exclusive there will be duplicates, so we need to filter
        seen_ids = []
        featured_urls = ["https://gab.com/api/v1/timelines/group_collection/featured?sort_by=hot&limit=40&max_id=","https://gab.com/api/v1/timelines/group_collection/featured?limit=40&max_id=" ,"https://gab.com/api/v1/timelines/group_collection/featured?sort_by=top_today&limit=40&max_id="]
        for url_raw in featured_urls:
            num_gabs = 0
            max_id = ''
            while True:
                url = url_raw + max_id


                resp = self.get(url)
                # time.sleep(1)

                # We should probably implement some better error catching
                # not simply checking for a 500 to know we've gotten all the gabs possible
                if resp.status_code == 500:
                    logging.error("search for %s failed, recieved 500 from Gab.com", (q))
                    return
                elif resp.status_code == 429:
                    logging.warn("rate limited, sleeping two minutes")
                    time.sleep(100)
                    break
                posts = resp.json()

                # API seems to be more stable than previously and will not send 500
                # as it runs out of data, now returns empty results
                if not posts:
                    logging.info("No more posts returned for search: %s", (q))
                    break

                for post in posts:
                    # filter for duplicates
                    post_id = post['id']
                    max_id = post_id
                    max_created_at = post['created_at']
                    if post_id in seen_ids:
                        continue
                    else:
                        seen_ids.append(post['id'])
                    if self.search_gab_text(post,q):
                        yield self.format_post(post)
                num_gabs += len(posts)
                if  (num_gabs > gabs and gabs != -1):
                    logging.info("Number of gabs condition met: %s", (q))
                    break

                # Check if first collected gab is after the date specified
                # The API returns strange results sometimes where gabs are not in date order, so ocassionally random dates pop up
                # But these never seem to appear at the start, so checking the first item keeps the function from prematurely ending
                # It does mean an additional call is made however
                # Each featured feed is only a few pages long as of 2020-08-14, so this is commented out for the time being
                # if posts[0]['created_at'] < gabs_after:
                #     if posts[1]['created_at'] < gabs_after:
                #         if posts[2]['created_at'] < gabs_after:
                #             if posts[-1]['created_at'] < gabs_after:

                #                 logging.info("Gabs after condition met: %s", (q))

                #                 break


    # def public_search(self, q,  gabs=-1,gabs_after=(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=20)).strftime("%Y-%m-%dT%H:%M")):
    #     """
    #     Pass in a query. 
    #     Searches the public Gab timeline for posts which match query q
    #     Match is case insensitive
    #     """

    #     num_gabs = 0
    #     max_id = ''
    #     while True:
    #         url = "https://gab.com/api/v1/timelines/group_collection/featured?sort_by=top_today&limit=40&max_id=%s" % (max_id)  
    #         resp = self.anonymous_get(url)
    #         # time.sleep(1)

    #         # We should probably implement some better error catching
    #         # not simply checking for a 500 to know we've gotten all the gabs possible
    #         if resp.status_code == 500:
    #             logging.error("search for %s failed, recieved 500 from Gab.com", (q))
    #             return
    #         elif resp.status_code == 429:
    #             logging.warn("rate limited, sleeping two minutes")
    #             time.sleep(100)
    #             break
    #         posts = resp.json()

    #         # API seems to be more stable than previously and will not send 500
    #         # as it runs out of data, now returns empty results
    #         if not posts:
    #             logging.info("No more posts returned for search: %s", (q))
    #             break

    #         for post in posts:
    #             if self.search_gab_text(post,q):
    #                 yield self.format_post(post)
    #             max_id = post['id']
    #             max_created_at = post['created_at']
    #         num_gabs += len(posts)
    #         if  (num_gabs > gabs and gabs != -1):
    #             logging.info("Number of gabs condition met: %s", (q))
    #             break

    #         # Check if first collected gab is after the date specified
    #         # The API returns strange results sometimes where gabs are not in date order, so ocassionally random dates pop up
    #         # But these never seem to appear at the start, so checking the first item keeps the function from prematurely ending
    #         # It does mean an additional call is made however
    #         # if posts[0]['created_at'] < gabs_after:
    #         #     if posts[1]['created_at'] < gabs_after:
    #         #         if posts[2]['created_at'] < gabs_after:
    #         #             if posts[-1]['created_at'] < gabs_after:

    #         #                 logging.info("Gabs after condition met: %s", (q))

    #         #                 break
    def user(self, q):
        """
        collect user json data
        """
        url = 'https://gab.com/api/v1/account_by_username/%s' % (q)
        resp = self.get(url)
        yield resp.json()


    def userposts(self, q, gabs=-1, gabs_after='2000-01-01'):
        """
        collect posts from a user feed
        """
        # We need to get the account id to collect statuses
        account_url = 'https://gab.com/api/v1/account_by_username/%s' % (q)
        account_id = self.get(account_url).json()['id']
        max_id = ''
        base_url = "https://gab.com/api/v1/accounts/%s/statuses?exclude_replies=true&max_id=" % (account_id)
        
        num_gabs = 0
        while True:
            url = base_url + max_id
            resp = self.get(url)
            posts = resp.json()
            if not posts:
                break
            last_published_date = posts[-1]['created_at']
            for post in posts:
                yield self.format_post(post)
                max_id = post['id']
            num_gabs += len(posts)
            if last_published_date < gabs_after:
                break
            if  (num_gabs > gabs and gabs != -1):
                break
    def usercomments(self, q):
        """
        collect comments from a users feed
        """
        # We need to get the account id to collect statuses
        account_url = 'https://gab.com/api/v1/account_by_username/%s' % (q)
        account_id = self.get(account_url).json()['id']
        max_id = ''
        base_url = "https://gab.com/api/v1/accounts/%s/statuses?only_comments=true&exclude_replies=false&max_id=" % (account_id)
        
        num_gabs = 0
        while True:
            url = base_url + max_id
            resp = self.get(url)
            posts = resp.json()
            if not posts:
                break
            last_published_date = posts[-1]['created_at']
            for post in posts:
                yield self.format_post(post)
                max_id = post['id']
            num_gabs += len(posts)

    def login(self):
        """
        Login to Gab to retrieve needed session token.
        """
        if not (self.user_account and self.user_password):
            raise RuntimeError("MissingAccountInfo")

        if self.cookie:
            logging.info("refreshing login cookie")

        url = "https://gab.com/auth/sign_in"
        input_token = requests.get(url)
        page_info = BeautifulSoup(input_token.content, "html.parser")
        token = page_info.select('meta[name=csrf-token]')[0]['content']
        self.access_token = token
        payload = {'user[email]':self.user_account, 'user[password]':self.user_password, 'authenticity_token':token}

        d = requests.request("POST", url, params=payload, cookies=input_token.cookies)
        self.cookie = d.cookies

    def followers(self,q):
        """
        find all followers of a specific user
        This is currently broken
        """
        num_followers = 0
        while True:
            url = "https://gab.com/users/%s/followers?before=%s" % (q,num_followers)
            resp = self.get(url)
            posts = resp.json()["data"]
            if not posts:
                break
            for post in posts:
                yield post
            num_followers += len(posts)

    def following(self,q):
        """
        This is currently broken
        """
        num_followers = 0
        while True:
            url = "https://gab.com/users/%s/following?before=%s" % (q,num_followers)
            resp = self.get(url)
            posts = resp.json()["data"]
            if not posts:
                break
            for post in posts:
                yield post
            num_followers += len(posts)



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
            # Maybe should implement allow_404 that stops retrying, ala twarc

            if r.status_code == 404:
                logging.warn("404 from Gab API! trying again")
                time.sleep(10)
                r = self.get(url, **kwargs)
            if r.status_code == 500:
                logging.warn("500 from Gab API! trying again")
                time.sleep(15)
                r = self.get(url, **kwargs)
            return r
        except requests.exceptions.ConnectionError as e:
            logging.warn("Connection Error from Gab API! trying again")
            time.sleep(15)

            self.get(url, **kwargs)
    def anonymous_get(self, url, **kwargs):
        """
        Perform an anonymous API request. Used for accessing public timelines.
        """

        connection_error_count = kwargs.pop('connection_error_count', 1)
        try:
            logging.info("getting %s %s", url, kwargs)

            r = requests.get(url)
            # Maybe should implement allow_404 that stops retrying, ala twarc

            if r.status_code == 404:
                logging.warn("404 from Gab API! trying again")
                time.sleep(15)
                r = self.anonymous_get(url, **kwargs)
            if r.status_code == 500:
                logging.warn("500 from Gab API! trying again")
                time.sleep(15)
                r = self.anonymous_get(url, **kwargs)
            return r
        except requests.exceptions.ConnectionError as e:
            logging.warn("Connection Error from Gab API! trying again")
            time.sleep(15)

            self.anonymous_get(url, **kwargs)



    def search_gab_text(self,gab,query):
        """
        Search if query exists within the text of a gab
        Return True if it does, False if not
        """
        if  re.search(query.lower(),gab['content'].lower()):
            match = True
        else:
            match = False

        return match

    def format_post(self,post):
        """
        Format post so that body field is inserted, this harmonizes new mastodon data with old gab data
        """
        body = BeautifulSoup(html.unescape(post['content']), features="html.parser").get_text()
        post['body'] = body
        return post


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
