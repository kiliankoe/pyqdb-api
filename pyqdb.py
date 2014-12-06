import pymysql
import re


def process_authors(quote):
    if '-' in quote:
        return [quote.split('-')[1][1:]]
    if '&lt;' in quote:
        return re.findall('(?<=&lt;)(.*?)(?=&gt;)', quote)
    else:
        return []


def process_quote_string(quote):
    quote = quote.replace('&quot;', '"')
    quote = quote.replace('&lt;', '<')
    quote = quote.replace('&gt;', '>')
    return quote


def process_quote(quote):
    return {
        'id': quote[0],
        'quote': process_quote_string(quote[1]),
        'authors': process_authors(quote[1]),
        'rating': quote[2],
        'timestamp': quote[3]
    }


def filter_by_author(author, quotes):
    if len(author.split(',')) > 1:
        authors = author.split(',')
        return [quote for quote in quotes if compare_authors(authors, quote['authors'])]
    else:
        return [quote for quote in quotes if author in quote['authors']]


def compare_authors(list1, list2):
    """Returns true if all elements of list1 are contained in list2"""
    return len(list1) == len(set(list1).intersection(list2))


def filter_by_rating(rating, quotes):
    return [quote for quote in quotes if quote['rating'] > int(rating)]


def filter_by_timestamp(timestamp, quotes):
    return [quote for quote in quotes if quote['timestamp'] > int(timestamp)]


class Pyqdb:

    def __init__(self, host, port, user, passwd, db):
        self.conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db)
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()

    def all_quotes(self):
        self.cur.execute('SELECT id, quote, rating, date FROM quotes;')
        return [process_quote(row) for row in self.cur]

    def find_by_id(self, id):
        self.cur.execute('SELECT id, quote, rating, date FROM quotes WHERE id = %s;' % id)
        return [process_quote(row) for row in self.cur][0]

    def find_by_ip(self, ip):
        self.cur.execute('SELECT id, quote, rating, date FROM quotes WHERE submitip = "%s"' % ip)
        return [process_quote(row) for row in self.cur]
