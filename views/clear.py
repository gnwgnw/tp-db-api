import MySQLdb
from flask import jsonify, Blueprint, g
from settings import prefix, sql_file_name, db_connection


__author__ = 'gexogen'

clear_api = Blueprint('clear_api', __name__)


@clear_api.route(prefix + '/clear/', methods=['POST'])
def clear():
    cursor = db_connection.cursor()
    sql = ''
    sql_file = open(sql_file_name)
    for line in sql_file:
        sql += line
        if ';' in line:
            cursor.execute(sql)
            db_connection.commit()
            sql = ''

    sql_file.close()
    cursor.close()

    return jsonify(code=0, response='OK')
