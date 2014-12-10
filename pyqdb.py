import pymysql
import re


def process_authors(quote):
    """[Deprecated] Return a list of authors contained in a given quote."""
    if '-' in quote:
        return [quote.split('-')[1][1:]]
    if '&lt;' in quote:
        return re.findall('(?<=&lt;)(.*?)(?=&gt;)', quote)
    else:
        return []


def process_quote_string(quote):
    """Replace the typical HTML entities rash-qdb stores quotes with."""
    quote = quote.replace('&quot;', '"')
    quote = quote.replace('&lt;', '<')
    quote = quote.replace('&gt;', '>')
    return quote


def process_quote(quote):
    """Takes a row returned from the database and returns a quote dictionary."""
    return {
        'id': quote[0],
        'quote': process_quote_string(quote[1]),
        'authors': [],
        'rating': quote[2],
        'timestamp': quote[3]
    }


def check_list_occurrences(list1, list2):
    """Return true if all elements of list1 are contained in list2."""
    return len(list1) == len(set(list1).intersection(list2))


def filter_by_author(author, quotes):
    """Filter a list of quotes by a given author or multiple comma-separated authors."""
    if author != '':
        if len(author.split(',')) > 1:
            authors = author.split(',')
            return [quote for quote in quotes if check_list_occurrences(authors, quote['authors'])]
        else:
            return [quote for quote in quotes if author in quote['authors']]
    else:
        return quotes


def filter_by_rating(rating, quotes, direction='above'):
    """Filter a list of quotes by a given rating, return either anything above, equal or below."""
    if direction == 'above':
        return [quote for quote in quotes if quote['rating'] > int(rating)]
    elif direction == 'equal':
        if rating != -100:
            return [quote for quote in quotes if quote['rating'] == int(rating)]
        else:
            return quotes
    else:
        return [quote for quote in quotes if quote['rating'] < int(rating)]


def filter_by_timestamp(timestamp, quotes, direction='after'):
    """Filter a list of quotes by a given timestamp, return either anything before or after."""
    if direction == 'after':
        return [quote for quote in quotes if quote['timestamp'] > int(timestamp)]
    else:
        return [quote for quote in quotes if quote['timestamp'] < int(timestamp)]


class NameHandler():

    def __init__(self):
        # read names from file for author processing, regex magic just isn't enough for these kind of quotes
        file = open('names.txt', 'r')
        self.names = file.readlines()
        file.close()
        for i in range(len(self.names)):
            self.names[i] = self.names[i].replace('\n', '')

    def process_authors(self, quote):
        """Matches a list of names stored in Pyqdb() with a given quote to fill the quote's list of authors."""
        authors = []
        for name in self.names:
            if re.search('(\W|^)%s(\W|$)' % name.lower(), quote.lower()) is not None:
                authors.append(name)
        return authors


class Pyqdb:

    def __init__(self, host, port, user, passwd, db):
        self.conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db)
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()

    def all_quotes(self):
        """Get all quotes from the database."""
        self.cur.execute('SELECT id, quote, rating, date FROM quotes;')
        return [process_quote(row) for row in self.cur]

    def find_by_id(self, quote_id):
        """Get a single quote by its ID."""
        sql = 'SELECT id, quote, rating, date FROM quotes WHERE id = %s;'
        self.cur.execute(sql, (quote_id,))
        if self.cur.rowcount != 0:
            return [process_quote(row) for row in self.cur][0]
        else:
            return []

    def find_by_ip(self, ip):
        """Get quotes submitted by a specific IP."""
        if ip != '':
            sql = 'SELECT id, quote, rating, date FROM quotes WHERE submitip = "%s"'
            self.cur.execute(sql, (ip,))
            return [process_quote(row) for row in self.cur]
        else:
            return self.all_quotes()
