from flask import g, Flask

from settings import *
from views.clear import clear_api, clear
from views.forum import forum_api
from views.post import post_api
from views.thread import thread_api
from views.user import user_api


__author__ = 'gexogen'

app = Flask(__name__)

app.register_blueprint(user_api)
app.register_blueprint(forum_api)
app.register_blueprint(thread_api)
app.register_blueprint(post_api)
app.register_blueprint(clear_api)

if __name__ == "__main__":
    app.run()

# db_connection.close()