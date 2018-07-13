garc
=====

Garc is a python library and command line tool for collecting JSON data from Gab.ai

Garc is built based on the wonderful [twarc](https://github.com/DocNow/twarc) project published by the Documenting the Now project. Inspiration for structure, usage and outputs are from twarc, and garc is intended to be used for similar purposes.

Garc is still very much a work in progress, and is being constantly updated to add deeper functionality and as new features and changes are implemented by Gab.


## Warnings

Gab's api is relatively sparsely documented, so things may change without warning and break searches.

Please be respectful when using this and any data collection software, try not to make excessive searches and calls.


## Installation

Currently the garc package hasn't been uploaded to PIP (that is top of our next steps), so installation must be done directly from github.

This is done doing the following command `pip install git+git://github.com/ChrisStevens/garc.git`


## Usage


### Configure

First you need to give garc your account information:

    garc configure

You only need the username and password for your account created at Gab.ai. Without an account you won't be able to interact with the api, or get any results from garc.

### Search

Using the Gab search API you can collect posts based on a search term. As Gab's API is mostly undoumented it is hard to know exactly what the searches return (it is however the same data as appears on the Gab website for a search). Initial tests have found matches for the search term in both the post body and the users description, and the search uses some type of fuzzy matching or word stemming, as matches for not exact terms have shown up.

A simple call
    
    garc search maga

Will return as many historical gabs as are available (usually around 9000 irrespective of post dates).

You can also limit the number of returns with the --number_gabs parameter

    garc search maga --number_gabs=100

Which will return approxiately 100 of the most recent posts.



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
