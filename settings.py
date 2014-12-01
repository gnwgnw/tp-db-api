import MySQLdb
from utils import helper

HOST_NAME = "127.0.0.1"
USER_NAME = "my_user"
USER_PASSWORD = "my_password"
DB_NAME = "my_db"

prefix = '/db/api'
sql_file_name = helper.rel('../my_db.sql')

db_connection = MySQLdb.connect(host=HOST_NAME, user=USER_NAME, passwd=USER_PASSWORD, db=DB_NAME, charset='utf8')

