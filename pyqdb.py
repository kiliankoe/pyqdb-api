import pymysql
import re

class Pyqdb:

    def __init__(self, host, port, user, passwd, db):
        self.conn = pymysql.connect(host=host, port=port, user=user, passwd=passwd, db=db)
        self.cur = self.conn.cursor()

    def close(self):
        self.cur.close()
        self.conn.close()

    def all_quotes(self):
        self.cur.execute('SELECT id, quote, rating, date FROM quotes;')
        return [self.process_quote(row) for row in self.cur]

    def find_by_id(self, id):
        self.cur.execute('SELECT id, quote, rating, date FROM quotes WHERE id = %s;' % id)
        return [self.process_quote(row) for row in self.cur][0]

    def find_by_ip(self, ip):
        self.cur.execute('SELECT id, quote, rating, date FROM quotes WHERE submitip = "%s"' % ip)
        return [self.process_quote(row) for row in self.cur]

    def filter_by_author(self, author, quotes):
        return [quote for quote in quotes if author in quote['authors']]

    def process_quote(self, quote):
        return {
            'id': quote[0],
            'quote': self.process_quote_string(quote[1]),
            'authors': self.process_authors(quote[1]),
            'rating': quote[2],
            'timestamp': quote[3]
        }

    def process_quote_string(self, quote):
        quote = quote.replace('&quot;','"')
        quote = quote.replace('&lt;','<')
        quote = quote.replace('&gt;','>')
        return quote

    def process_authors(self, quote):
        if '-' in quote:
            return [quote.split('-')[1][1:]]
        if '&lt;' in quote:
            return re.findall('(?<=&lt;)(.*?)(?=&gt;)', quote)
        else:
            return []
