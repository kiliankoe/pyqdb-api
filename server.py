from pyqdb import *
from bottle import route, run, request, response, auth_basic, debug
import time
import json
import os
import hashlib

try:
    p = Pyqdb(host='127.0.0.1',port=3306,user='',
              passwd='',db='')
except pymysql.err.OperationalError as e:
    print('Error: ' + str(e))


def check(user, pw):
    return user == '' and hashlib.md5(pw.encode('utf-8')).hexdigest() == ''


@route('/quotes')
@auth_basic(check)
def get_quotes():
    if not p.test_db():
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

    # apparently returning a straight list of dicts is unsupported due to security concerns
    # see http://flask.pocoo.org/docs/0.10/security/#json-security
    # but it's not like this tool has sensitive information... :D
    return json.dumps(results)


@route('/quotes/<quote_id:int>')
@auth_basic(check)
def get_quote_with_id(quote_id):
    if not p.test_db():
        return {'Error': 'Database Connection Error'}
    response.content_type = 'application/json'
    quote = p.find_by_id(quote_id)
    quote['authors'] = p.process_authors(quote['quote'])
    return quote


@route('/quotes/lastweek')
@auth_basic(check)
def get_last_week():
    if not p.test_db():
        return {'Error': 'Database Connection Error'}
    ctime = int(time.time()) - 604800
    response.content_type = 'application/json'
    results = filter_by_timestamp(ctime, p.all_quotes())
    for i in range(len(results)):
        results[i]['authors'] = p.process_authors(results[i]['quote'])
    return json.dumps(results)


@route('/status')
def api_status():
    return {'status': 'online', 'servertime': time.time(), 'load': os.getloadavg()}


if os.getenv('env') == 'development':
    debug(True)
    run(reloader=True)
else:
    run()


p.close()
