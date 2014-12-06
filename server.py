from pyqdb import *
from bottle import route, run, request, response, debug
import time
import json

try:
    p = Pyqdb(host='127.0.0.1',port=3306,user='',
              passwd='',db='')
except pymysql.err.OperationalError as e:
    print('Error: ' + str(e))

@route('/quotes')
def get_quotes():
    # apparently returning a straight list of dicts
    # is unsupported due to security concerns
    # see http://flask.pocoo.org/docs/0.10/security/#json-security
    # it's not like this tool has sensitive information... :D
    response.content_type = 'text/json'
    if 'author' in request.query:
        return json.dumps(p.find_by_author(request.query['author']))
    elif 'ip' in request.query:
        return json.dumps(p.find_by_ip(request.query['ip']))
    else:
        return json.dumps(p.all_quotes())

@route('/quotes/:id')
def get_quote_with_id(id):
    response.content_type = 'text/json'
    return p.find_by_id(id)

@route('/status')
def api_status():
    return {'status':'online', 'servertime':time.time()}

debug(True)
run()
