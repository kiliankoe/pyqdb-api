## pyqdb-api

A small python webserver powered by bottle that plays the role of a json API for [rash-qdb](https://github.com/paxed/rash-qdb-fork).

It'll probably only work nicely with the rash-qdb server *we* have running, but let's throw it on GitHub nonetheless.

```sh
$ pip install requirements.txt
$ python server.py
```

Be sure to edit server.py with the credentials for your MySQL db first.

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

`/quotes?author=Notch` returns all quotes by a specific author. This is case-sensitive.

`/quotes?ip=127.0.0.1` returns all quotes submitted by a specific IP

`/quotes/1` returns the specific quote with that id
