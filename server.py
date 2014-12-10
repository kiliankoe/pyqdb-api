from pyqdb import *
from bottle import route, run, request, response, auth_basic, debug
import time
import json
import os
import hashlib

f = open('secrets.json', 'r')
secrets = json.loads(f.read())
f.close()

db_host = secrets['db']['host']
db_port = int(secrets['db']['port'])
db_user = secrets['db']['user']
db_passwd = secrets['db']['pass']
db_default_db = secrets['db']['db']


def connect_to_db():
    try:
        p = Pyqdb(host=db_host, port=db_port, user=db_user, passwd=db_passwd, db=db_default_db)
    except pymysql.OperationalError as e:
        print('Error: ' + str(e))
        p = None
    return p


def check(auth_user, auth_pw):
    return auth_user == secrets['http']['user'] \
        and hashlib.md5(auth_pw.encode('utf-8')).hexdigest() == secrets['http']['pass']


@route('/')
def get_root():
    response.content_type = 'text/plain'
    return 'Looking for the quotes? They\'re under /quotes'


@route('/quotes')
@auth_basic(check)
def get_quotes():
    p = connect_to_db()

    if p is None:
        return {'Error': 'Database Connection Error'}

    response.content_type = 'application/json'
    if 'ip' in request.query:
        results = p.find_by_ip(request.query['ip'])
    else:
        results = p.all_quotes()

    # Authors aren't processed yet. This is done here because IntelliJ would error on
    # 'Can't access non static method from static context'
    for i in range(len(results)):
        results[i]['authors'] = p.process_authors(results[i]['quote'])

    if 'author' in request.query:
        results = filter_by_author(request.query['author'], results)
    if 'rating_above' in request.query:
        results = filter_by_rating(request.query['rating_above'], results)
    if 'rating' in request.query:
        results = filter_by_rating(request.query['rating'], results, 'equal')
    if 'rating_below' in request.query:
        results = filter_by_rating(request.query['rating_below'], results, 'below')
    if 'after' in request.query:
        results = filter_by_timestamp(request.query['after'], results)
    if 'before' in request.query:
        results = filter_by_timestamp(request.query['before'], results, 'before')

    p.close()
    # apparently returning a straight list of dicts is unsupported due to security concerns
    # see http://flask.pocoo.org/docs/0.10/security/#json-security
    # but it's not like this tool has sensitive information... :D
    return json.dumps(results)


@route('/quotes/<quote_id:int>')
@auth_basic(check)
def get_quote_with_id(quote_id):
    p = connect_to_db()

    if p is None:
        return {'Error': 'Database Connection Error'}

    response.content_type = 'application/json'

    quote = p.find_by_id(quote_id)
    if quote:
        quote['authors'] = p.process_authors(quote['quote'])
    else:
        return {'Error': 'No such quote'}

    p.close()

    return quote


@route('/quotes/lastweek')
@auth_basic(check)
def get_last_week():
    p = connect_to_db()

    if p is None:
        return {'Error': 'Database Connection Error'}

    ctime = int(time.time()) - 604800
    response.content_type = 'application/json'
    results = filter_by_timestamp(ctime, p.all_quotes())
    for i in range(len(results)):
        results[i]['authors'] = p.process_authors(results[i]['quote'])

    p.close()

    return json.dumps(results)


@route('/status')
def api_status():
    return {'status': 'online', 'servertime': time.time(), 'load': os.getloadavg()}


if os.getenv('env') == 'development':
    debug(True)
    run(reloader=True)
else:
    run()
