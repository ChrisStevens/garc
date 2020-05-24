garc: Python and Command-Line Interface for Gab.com API
=====



Garc is a python library and command line tool for collecting JSON data from Gab.com. In July 2019, Gab switched its platform to a fork of Mastodon, this package was origionally written prior to this switch, but has been updated to work as well as possible with the new functionality of Mastodon.

Garc is built based on the wonderful [twarc](https://github.com/DocNow/twarc) project published by the Documenting the Now project. Inspiration for structure, usage and outputs are from twarc, and garc is intended to be used for similar purposes.

Garc is still very much a work in progress, and is being constantly updated to add deeper functionality and as new features and changes are implemented by Gab.

Please use your own judgement as to the usage of garc and whether you are adhearing to both Gab's Terms of Service and robots.txt.


## Warnings

Gab's API was historically relatively sparsely documented, so things may change without warning and break searches. This current version relies on these potentially unreliable API routes. 

Please be respectful when using this and any data collection software, try not to make excessive searches and calls.


## Installation

There are two options for installing garc. 

1. From pypi the official python package repository, which will always have the most stable release:
    `pip install garc`
2. Directly from Github, which will have the newest release:
    `pip install git+git://github.com/ChrisStevens/garc.git`


## Usage


### Configure

First you need to give garc your account information:

    garc configure

You only need the username and password for your account created at Gab.ai. Without an account you won't be able to interact with the api, or get any results from garc.

### Search

Using the Gab search API you can collect posts based on a hashtag. Unfortunately with how Gab's Mastodon instance is set up, you can't perform text searches. To simulate a text search use the Public Search function, which searches the public timeline for gabs matching your term. 

A simple call
    
    garc search maga

Will return as many historical gabs as are available in the hashtag search.

You can also limit the number of returns with the --number_gabs parameter

    garc search maga --number_gabs=100

Which will return approxiately 100 of the most recent posts.


### Public Search

Using the public timeline function of Mastodon this will query all new posts and return those which match the given search term. This is a time intensive process, and by default only returns posts for the last 15 minutes. It is also not entirely precise, as posts are not necessarily returned in order, so ocassionally the search will be terminated prior to collecting all posts in the given timeframe.

A simple call
    
    garc publicsearch maga

Will return as many historical posts as are available matching the search term in the last 15 minutes.

You can also limit the number of returns with the --number_gabs parameter

    garc publicsearch maga --number_gabs=100

Which will return approxiately 100 of the most recent posts.

You can also simply return all posts for the given time period by calling
	
    garc publicsearch



### User Posts

Another way to collect posts is by collecting all the posts made by a single user

    garc userposts fakeusername

As some users have a large number of posts this can take a long time to collect the entirey of a users timeline. Additional there are both number and time filters you can pass to limit the number of posts.

    garc userposts fakeusername --number_gabs=100

Will return aproximately 100 posts from the top of a users timeline

    garc userposts fakeusername --gabs_after=2018-05-12

Will return all gabs from after 2018-05-12


### User info

You can also collect the information of a user

    garc user fakeusername

Which will return a json object of information about the user
