from flask import Flask, request
from pyqdb import *
import time
import json
import os
import configparser

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

name_handler = NameHandler()

db_host = config['Database']['host']
db_port = int(config['Database']['port'])
db_user = config['Database']['user']
db_passwd = config['Database']['password']
db_default_db = config['Database']['default_db']


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
    return auth_user == config['HTTP Auth']['user'] and auth_pw == config['HTTP Auth']['password']


def check_post(auth_user, auth_pw):
    """Check the HTTP basic auth credentials for a POST request adding a quote."""
    return auth_user == config['HTTP Auth POST']['user'] and auth_pw == config['HTTP Auth POST']['password']


@app.route('/')
def get_root():
    """Catch requests to the root of the API, so they don't show with errors."""
    response.content_type = 'text/plain'
    return 'Looking for the quotes? They\'re under /quotes'


@app.route('/quotes', 'GET')
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


@app.route('/quotes', methods=['POST'])
@auth_basic(check_post)
def post_new_quote():
    """Accept POST requests for adding new quotes"""
    p = connect_to_db()

    response.content_type = 'application/json'

    if p is None:
        response.status = 500
        return {'Error': 'Database Connection Error'}

    if 'quote' not in request.form:
        response.status = 400
        return {'Error': 'Invalid data supplied. Needs `quote`.'}

    quote = request.form.quote
    submitip = request.remote_addr

    result = p.add_quote(quote, submitip)

    p.close()

    if result:
        return {'Status': 'Läuft'}
    else:
        response.status = 500
        return {'Error': 'Couldn\'t add quote to database'}


@app.route('/quotes/twilio', 'POST')
@auth_basic(check_post)
def post_quote_from_sms():
    """A webhook for Twilio accepting new quotes via text message by approved senders."""
    p = connect_to_db()

    response.content_type = 'text/plain'

    if 'Body' not in request.form or 'From' not in request.form:
        # this shouldn't happen with Twilio, but catch it just in case
        response.status = 400
        return None

    quote = request.form.Body
    sender = request.form.From

    if sender not in name_handler.approved_numbers:
        # don't allow quotes from non-approved numbers
        response.status = 403
        return None

    if p is None:
        response.status = 500
        return 'Bäh, ein Datenbankfehler. Schreib\' bitte Kilian an.'

    result = p.add_quote(quote, sender)
    if result:
        return None
    else:
        response.status = 500
        return 'Bäh, ein Datenbankfehler. Schreib\' bitte Kilian an.'


@app.route('/quotes/<int:quote_id>')
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


@app.route('/quotes/lastweek')
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


@app.route('/status')
def api_status():
    """Return the current server time and load averages."""
    return {'status': 'online', 'servertime': time.time(), 'load': os.getloadavg()}


@app.route('/coffee')
def make_coffee():
    """Answer to /coffee with the most important HTTP status code of all."""
    response.status = 418
    response.content_type = 'application/json'
    return {'Error': 'I\'m a teapot.'}


if os.getenv('env') == 'development':
    app.run(debug=True, host=config['Server']['host'], port=config['Server']['port'])
else:
    app.run(host=config['Server']['host'], port=config['Server']['port'])
