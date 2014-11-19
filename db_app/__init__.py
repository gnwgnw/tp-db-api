from flask import Flask

app = Flask(__name__)

import views.extra, views.clear, views.forum, views.user, views.post, views.thread