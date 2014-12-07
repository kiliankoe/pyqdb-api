import pymysql
import re


def process_authors(quote):
    # this is rather error-prone and should not be used
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
        'authors': [],
        'rating': quote[2],
        'timestamp': quote[3]
    }


def check_list_occurrences(list1, list2):
    """Returns true if all elements of list1 are contained in list2"""
    return len(list1) == len(set(list1).intersection(list2))


def filter_by_author(author, quotes):
    if author != '':
        if len(author.split(',')) > 1:
            authors = author.split(',')
            return [quote for quote in quotes if check_list_occurrences(authors, quote['authors'])]
        else:
            return [quote for quote in quotes if author in quote['authors']]
    else:
        return quotes


def filter_by_rating(rating, quotes, direction='above'):
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
    if direction == 'after':
        return [quote for quote in quotes if quote['timestamp'] > int(timestamp)]
    else:
        return [quote for quote in quotes if quote['timestamp'] < int(timestamp)]


class Pyqdb:

    def __init__(self, host, port, user, passwd, db):
        self.conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db)
        self.cur = self.conn.cursor()

        # read names from file for author processing, everything else just doesn't work
        file = open('names.txt','r')
        self.names = file.readlines()
        file.close()
        for i in range(len(self.names)):
            self.names[i] = self.names[i].replace('\n', '')

    def close(self):
        self.cur.close()
        self.conn.close()

    def all_quotes(self):
        self.cur.execute('SELECT id, quote, rating, date FROM quotes;')
        return [process_quote(row) for row in self.cur]

    def find_by_id(self, quote_id):
        self.cur.execute('SELECT id, quote, rating, date FROM quotes WHERE id = %s;' % quote_id)
        return [process_quote(row) for row in self.cur][0]

    def find_by_ip(self, ip):
        if ip != '':
            self.cur.execute('SELECT id, quote, rating, date FROM quotes WHERE submitip = "%s"' % ip)
            return [process_quote(row) for row in self.cur]
        else:
            return self.all_quotes()

    def process_authors(self, quote):
        authors = []
        for name in self.names:
            if re.search('(\W|^)%s(\W|$)' % name.lower(), quote.lower()) is not None:
                authors.append(name)
        return authors
