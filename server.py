from flask import Flask, request, make_response, abort, jsonify, json, url_for
from pyqdb import *
import time
# import json
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
    return 'Looking for the quotes? They\'re under <a href="' + url_for('get_quotes') + '">/quotes</a>.'


# TODO: Theoretically both routings for /quotes could be thrown into a single function
@app.route('/quotes', methods=['GET'])
# @auth_basic(check)
def get_quotes():
    """Get all quotes from the database and filter them with a few array parameters if needed."""
    p = connect_to_db()

    if p is None:
        return jsonify({'Error': 'Database Connection Error'}), 500

    if 'ip' in request.args:
        results = p.find_by_ip(request.args.get('ip'))
    else:
        results = p.all_quotes()

    # Process authors
    for i in range(len(results)):
        results[i]['authors'] = name_handler.process_authors(results[i]['quote'])

    if 'author' in request.args:
        results = filter_by_author(request.args.get('author'), results)
    if 'rating_above' in request.args:
        results = filter_by_rating(request.args.get('rating_above'), results)
    if 'rating' in request.args:
        results = filter_by_rating(request.args.get('rating'), results, direction='equal')
    if 'rating_below' in request.args:
        results = filter_by_rating(request.args.get('rating_below'), results, direction='below')
    if 'after' in request.args:
        results = filter_by_timestamp(request.args.get('after'), results)
    if 'before' in request.args:
        results = filter_by_timestamp(request.args.get('before'), results, direction='before')

    p.close()

    # apparently returning a straight list of dicts is unsupported due to security concerns
    # see http://flask.pocoo.org/docs/0.10/security/#json-security
    res = make_response(json.dumps(results))
    res.headers['Content-Type'] = 'application/json'
    return res


@app.route('/quotes', methods=['POST'])
# @auth_basic(check_post)
def post_new_quote():
    """Accept POST requests for adding new quotes"""
    p = connect_to_db()

    if p is None:
        return jsonify({'Error': 'Database Connection Error'}), 500

    quote = request.form['quote']
    # request.remote_addr is also a popular choice, but that seems to be containing the server's IP for some
    submitip = request.environ['REMOTE_ADDR']

    result = p.add_quote(quote, submitip)

    p.close()

    if result:
        return jsonify({'Status': 'Läuft'})
    else:
        return jsonify({'Error': 'Couldn\'t add quote to database'}), 500


@app.route('/quotes/twilio', methods=['POST'])
# @auth_basic(check_post)
def post_quote_from_sms():
    """A webhook for Twilio accepting new quotes via text message by approved senders."""
    p = connect_to_db()

    res = make_response()
    res.content_type = 'text/plain'

    quote = request.form['Body']
    sender = request.form['From']

    if sender not in name_handler.approved_numbers:
        # don't allow quotes from non-approved numbers
        return '', 403

    if p is None:
        res = make_response('Bäh, ein Datenbankfehler. Schreib\' bitte Kilian an.', 500)
        return res

    result = p.add_quote(quote, sender)
    if result:
        return ''
    else:
        res = make_response('Bäh, ein Datenbankfehler. Schreib\' bitte Kilian an.', 500)
        return res


@app.route('/quotes/<int:quote_id>')
# @auth_basic(check)
def get_quote_with_id(quote_id):
    """Get a specific quote directly by its ID."""
    p = connect_to_db()

    if p is None:
        return jsonify({'Error': 'Database Connection Error'}), 500

    quote = p.find_by_id(quote_id)
    if quote:
        quote['authors'] = name_handler.process_authors(quote['quote'])
    else:
        return jsonify({'Error': 'No such quote'}), 404

    p.close()

    return jsonify(quote)


@app.route('/quotes/lastweek')
# @auth_basic(check)
def get_last_week():
    """Return all quotes submitted within the last 7 days."""
    p = connect_to_db()

    if p is None:
        return jsonify({'Error': 'Database Connection Error'}), 500

    timestamp_last_week = int(time.time()) - 604800
    results = filter_by_timestamp(timestamp_last_week, p.all_quotes())
    for i in range(len(results)):
        results[i]['authors'] = name_handler.process_authors(results[i]['quote'])

    p.close()

    res = make_response(json.dumps(results))
    res.headers['Content-Type'] = 'application/json'

    return res


@app.route('/status')
def api_status():
    """Return the current server time and load averages."""
    return jsonify({'status': 'online', 'servertime': time.time(), 'load': os.getloadavg()})


@app.route('/coffee')
def make_coffee():
    """Answer to /coffee with the most important HTTP status code of all."""
    return jsonify({'Error': 'I\'m a teapot'}), 418


if os.getenv('env') == 'development':
    app.run(debug=True, host=config['Server']['host'], port=int(config['Server']['port']))
else:
    app.run(host=config['Server']['host'], port=int(config['Server']['port']))
