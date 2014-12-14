from pyqdb import *
from bottle import route, run, request, response, auth_basic, debug
import time
import json
import os
import hashlib

f = open('secrets.json', 'r')
secrets = json.loads(f.read())
f.close()

name_handler = NameHandler()

db_host = secrets['db']['host']
db_port = int(secrets['db']['port'])
db_user = secrets['db']['user']
db_passwd = secrets['db']['pass']
db_default_db = secrets['db']['db']


def connect_to_db():
    """Instantiate a new database object by connecting to the database with the supplied credentials."""
    try:
        p = Pyqdb(host=db_host, port=db_port, user=db_user, passwd=db_passwd, db=db_default_db)
    except pymysql.OperationalError as e:
        print('Error: ' + str(e))
        p = None
    return p


def check(auth_user, auth_pw):
    """Check the default HTTP basic auth credentials."""
    return auth_user == secrets['http']['user'] \
        and hashlib.md5(auth_pw.encode('utf-8')).hexdigest() == secrets['http']['pass']


def check_post(auth_user, auth_pw):
    """Check the HTTP basic auth credentials for a POST request adding a quote."""
    return auth_user == '' and auth_pw == ''


@route('/')
def get_root():
    """Catch requests to the root of the API, so they don't show with errors."""
    response.content_type = 'text/plain'
    return 'Looking for the quotes? They\'re under /quotes'


@route('/quotes', 'GET')
@auth_basic(check)
def get_quotes():
    """Get all quotes from the database and filter them with a few array parameters if needed."""
    p = connect_to_db()

    response.content_type = 'application/json'

    if p is None:
        response.status = 500
        return {'Error': 'Database Connection Error'}

    if 'ip' in request.query:
        results = p.find_by_ip(request.query['ip'])
    else:
        results = p.all_quotes()

    # Authors aren't processed yet. This is done here because IntelliJ would error on
    # 'Can't access non static method from static context'
    for i in range(len(results)):
        results[i]['authors'] = name_handler.process_authors(results[i]['quote'])

    if 'author' in request.query:
        results = filter_by_author(request.query.author, results)
    if 'rating_above' in request.query:
        results = filter_by_rating(request.query.rating_above, results)
    if 'rating' in request.query:
        results = filter_by_rating(request.query.rating, results, 'equal')
    if 'rating_below' in request.query:
        results = filter_by_rating(request.query.rating_below, results, 'below')
    if 'after' in request.query:
        results = filter_by_timestamp(request.query.after, results)
    if 'before' in request.query:
        results = filter_by_timestamp(request.query.before, results, 'before')

    p.close()
    # apparently returning a straight list of dicts is unsupported due to security concerns
    # see http://flask.pocoo.org/docs/0.10/security/#json-security
    # but it's not like this tool has sensitive information... :D
    return json.dumps(results)


@route('/quotes', 'POST')
@auth_basic(check_post)
def post_new_quote():
    """Accept POST requests for adding new quotes"""
    p = connect_to_db()

    response.content_type = 'application/json'

    if p is None:
        response.status = 500
        return {'Error': 'Database Connection Error'}

    if 'quote' not in request.forms:
        response.status = 400
        return {'Error': 'Invalid data supplied. Needs `quote`.'}

    quote = request.forms.quote
    submitip = request.remote_addr

    result = p.add_quote(quote, submitip)

    p.close()

    if result:
        return {'Status': 'Läuft'}
    else:
        response.status = 500
        return {'Error': 'Couldn\'t add quote to database'}


@route('/quotes/twilio', 'POST')
def post_quote_from_sms():
    """A webhook for Twilio accepting new quotes via text message by approved senders."""
    p = connect_to_db()

    response.content_type = 'text/plain'

    approved_numbers = {'+49XXXXXXXXXXX': 'name',
                        '+49YYYYYYYYYYY': 'name'}

    if p is None:
        return 'Database error, couldn\'t add quote to database.'

    quote = request.forms.Body
    sender = request.forms.From

    if sender not in approved_numbers:
        return None

    result = p.add_quote(quote, '127.0.0.2')
    if result:
        return None
    else:
        return 'Database error, couldn\'t add quote to database.'


@route('/quotes/<quote_id:int>')
@auth_basic(check)
def get_quote_with_id(quote_id):
    """Get a specific quote directly by its ID."""
    p = connect_to_db()

    response.content_type = 'application/json'

    if p is None:
        response.status = 500
        return {'Error': 'Database Connection Error'}

    quote = p.find_by_id(quote_id)
    if quote:
        quote['authors'] = name_handler.process_authors(quote['quote'])
    else:
        response.status = 404
        return {'Error': 'No such quote'}

    p.close()

    return quote


@route('/quotes/lastweek')
@auth_basic(check)
def get_last_week():
    """Return all quotes submitted within the last 7 days."""
    p = connect_to_db()

    response.content_type = 'application/json'

    if p is None:
        response.status = 500
        return {'Error': 'Database Connection Error'}

    timestamp_last_week = int(time.time()) - 604800
    results = filter_by_timestamp(timestamp_last_week, p.all_quotes())
    for i in range(len(results)):
        results[i]['authors'] = name_handler.process_authors(results[i]['quote'])

    p.close()

    return json.dumps(results)


@route('/status')
def api_status():
    """Return the current server time and load averages."""
    return {'status': 'online', 'servertime': time.time(), 'load': os.getloadavg()}


@route('/coffee')
def make_coffee():
    """Answer to /coffee with the most important HTTP status code of all."""
    response.status = 418
    response.content_type = 'application/json'
    return {'Error': 'I\'m a teapot.'}


if os.getenv('env') == 'development':
    debug(True)
    run(reloader=True)
else:
    run()
