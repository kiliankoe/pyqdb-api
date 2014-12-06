from pyqdb import *
from bottle import route, run, request, response, debug
import time
import json
import os

try:
    p = Pyqdb(host='127.0.0.1',port=3306,user='',
              passwd='',db='')
except pymysql.err.OperationalError as e:
    print('Error: ' + str(e))


@route('/quotes')
def get_quotes():
    response.content_type = 'text/json'
    if 'ip' in request.query:
        results = p.find_by_ip(request.query['ip'])
    else:
        results = p.all_quotes()

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
def get_quote_with_id(quote_id):
    response.content_type = 'text/json'
    return p.find_by_id(quote_id)


@route('/quotes/<author>')
def get_quote_from_author(author):
    response.content_type = 'text/json'
    return json.dumps(filter_by_author(author, p.all_quotes()))


@route('/status')
def api_status():
    return {'status': 'online', 'servertime': time.time(), 'load': os.getloadavg()}


if os.getenv('env') == 'development':
    debug(True)
    run(reloader=True)
else:
    run()


p.close()
