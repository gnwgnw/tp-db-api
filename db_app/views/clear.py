from flask import jsonify, g

from db_app import app
from settings import prefix, sql_file_name


__author__ = 'gexogen'


@app.route(prefix + '/clear/', methods=['POST'])
def clear():
    sql = ''
    sql_file = open(sql_file_name)
    for line in sql_file:
        sql += line
        if ';' in line:
            g.cursor.execute(sql)
            g.db.commit()
            sql = ''

    sql_file.close()

    return jsonify(code=0, response='OK')
