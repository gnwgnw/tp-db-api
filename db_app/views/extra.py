import MySQLdb

from flask import g

from db_app import app
from settings import HOST_NAME, USER_NAME, USER_PASSWORD, DB_NAME


__author__ = 'gexogen'


@app.before_request
def before_request():
    g.db = MySQLdb.connect(host=HOST_NAME, user=USER_NAME, passwd=USER_PASSWORD, db=DB_NAME, charset='utf8')
    g.cursor = g.db.cursor(MySQLdb.cursors.DictCursor)


@app.teardown_request
def teardown_request(exception):
    g.db.close()
    g.cursor.close()
