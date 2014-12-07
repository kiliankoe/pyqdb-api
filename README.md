## pyqdb-api

A small python webserver powered by bottle that plays the role of a json API for [rash-qdb](https://github.com/paxed/rash-qdb-fork).

It'll probably only work nicely with the rash-qdb server *we* have running, but let's throw it on GitHub nonetheless.

```sh
$ pip install requirements.txt
$ python server.py
```

Be sure to edit server.py with your MySQL db and basic auth credentials first.

Then you can access the following routes from your app/browser/whatever.

`/quotes` returns all quotes in the db like this:
```js
[{
    "rating": -8,
    "quote": "\"Niemand hat die Absicht, Minecraft zu spielen\" - Notch",
    "authors": ["Notch"],
    "id": 1,
    "timestamp": 1389883016
},{...}
]
```

You can filter this quote listing with a few different parameters, all of these can be used together as well.

#### Filter by author

`/quotes?author=Notch` returns all quotes by a random guy called Notch.

`/quotes?author=Notch,Jeb` multiple, comma-separated authors are also accepted. This would return all quotes where both of them are listed as authors, not all of both their quotes.

Note that the author is case-sensitive.

#### Filter by rating

`/quotes?rating_above=10` returns only quotes with a rating above 10.

`/quotes?rating=10` gives you quotes with an exact rating of 10.

`/quotes?rating_below=-10` returns... You can guess it.

#### Filter by timestamp

`/quotes?after=1417388408` returns only quotes submitted after the given unix timestamp.

`/quotes?before=1390000000` does it the other way around.

#### Filter by submitter IP

Rash-qdb saves the IP of a quote submitter. You can filter by this as well, but the IPs are never included in the output.

`/quotes?ip=127.0.0.1` returns all quotes submitted by localhost.

#### Specific pages

`/quotes/1` returns only the very first quote.

`/quotes/lastweek` returns all quotes submitted within the last 7 days
