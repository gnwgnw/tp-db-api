import MySQLdb

from flask import request, g, jsonify

from db_app import app
from settings import prefix
from utils import db_queryes


__author__ = 'gexogen'


@app.route(prefix + '/thread/create/', methods=['POST'])
def thread_create():
    is_deleted = request.json.get('isDeleted', False)
    forum = request.json.get('forum', None)
    title = request.json.get('title', None)
    is_closed = request.json.get('isClosed', False)
    user = request.json.get('user', None)
    date = request.json.get('date', None)
    message = request.json.get('message', None)
    slug = request.json.get('slug', None)

    try:
        g.cursor.execute("""INSERT INTO `threads`
                          (`isDeleted`, `forum`, `title`, `isClosed`, `user`, `date`, `message`, `slug`)
                          VALUE (%s, %s, %s, %s, %s, %s, %s, %s);""",
                         (is_deleted, forum, title, is_closed, user, date, message, slug))
        g.db.commit()

    except MySQLdb.Error:
        g.db.rollback()

    g.cursor.execute("""SELECT * FROM `threads` WHERE `slug` = %s""", slug)
    thread = g.cursor.fetchone()

    return jsonify(code=0, response=thread)


@app.route(prefix + '/thread/details/')
def thread_details():
    id = request.args.get('thread', None)
    related = request.args.getlist('related')

    if 'thread' in related:
        return jsonify(code=3, response='Error thread')

    thread = db_queryes.thread_details(id)

    if 'user' in related:
        user = db_queryes.user_details(thread['user'])
        thread.update({'user': user})

    if 'forum' in related:
        forum = db_queryes.forum_details(thread['forum'])
        thread.update({'forum': forum})

    return jsonify(code=0, response=thread)


@app.route(prefix + '/thread/list/')
def thread_list():
    forum = request.args.get('forum', None)
    user = request.args.get('user', None)  # TODO: bad code - if state
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    limit = long(limit)  # TODO: bad code

    if forum is not None:
        if order == 'desc':
            g.cursor.execute(
                """SELECT * FROM `threads` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                (forum, since, limit))
        else:
            g.cursor.execute(
                """SELECT * FROM `threads` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                (forum, since, limit))
    else:
        if order == 'desc':
            g.cursor.execute(
                """SELECT * FROM `threads` WHERE `user` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                (user, since, limit))
        else:
            g.cursor.execute(
                """SELECT * FROM `threads` WHERE `user` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                (user, since, limit))

    threads = [i for i in g.cursor.fetchall()]

    for thread in threads:
        thread.update({'date': str(thread['date'])})  # TODO: bad code

    return jsonify(code=0, response=threads)


@app.route(prefix + '/thread/listPosts/')
def thread_list_posts():
    thread = request.args.get('thread', None)
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    limit = long(limit)  # TODO: bad code
    thread = int(thread)  # TODO: bad code

    if order == 'desc':
        g.cursor.execute(
            """SELECT * FROM `posts` WHERE `thread` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
            (thread, since, limit))  # TODO: bad code - excess condition
    else:
        g.cursor.execute(
            """SELECT * FROM `posts` WHERE `thread` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
            (thread, since, limit))  # TODO: bad code - excess condition

    posts = [i for i in g.cursor.fetchall()]

    for post in posts:
        post.update({'date': str(post['date'])})  # TODO: bad code

    return jsonify(code=0, response=posts)


@app.route(prefix + '/thread/remove/', methods=['POST'])
def thread_remove():
    thread = request.json.get('thread', None)
    thread = int(thread)  # TODO: bad code

    try:
        g.cursor.execute("""UPDATE `threads` SET `isDeleted` = TRUE WHERE `id` = %s;""", thread)
        g.cursor.execute("""UPDATE `posts` SET `isDeleted` = TRUE WHERE `thread` = %s;""", thread)
        g.db.commit()

    except MySQLdb.Error:
        g.db.rollback()

    return jsonify(code=0, response={'thread': thread})


@app.route(prefix + '/thread/restore/', methods=['POST'])
def thread_restore():
    thread = request.json.get('thread', None)
    thread = int(thread)

    try:
        g.cursor.execute("""UPDATE `threads` SET `isDeleted` = FALSE WHERE `id` = %s;""", thread)  # TODO: make view
        g.cursor.execute("""UPDATE `posts` SET `isDeleted` = FALSE WHERE `thread` = %s;""", thread)
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    return jsonify(code=0, response={'thread': thread})


@app.route(prefix + '/thread/close/', methods=['POST'])
def thread_close():
    thread = request.json.get('thread', None)
    thread = int(thread)

    try:
        g.cursor.execute("""UPDATE `threads` SET `isClosed` = TRUE WHERE `id` = %s;""", thread)  # TODO: make view
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    return jsonify(code=0, response={'thread': thread})


@app.route(prefix + '/thread/open/', methods=['POST'])
def thread_open():
    thread = request.json.get('thread', None)
    thread = int(thread)

    try:
        g.cursor.execute("""UPDATE `threads` SET `isClosed` = FALSE WHERE `id` = %s;""", thread)  # TODO: make view
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    return jsonify(code=0, response={'thread': thread})


@app.route(prefix + '/thread/update/', methods=['POST'])
def thread_update():
    message = request.json.get('message', None)
    slug = request.json.get('slug', None)
    thread = request.json.get('thread', None)
    thread = int(thread)

    try:
        g.cursor.execute("""UPDATE `threads` SET `message` = %s, `slug` = %s WHERE `id` = %s;""",
                         (message, slug, thread))  # TODO: make view
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    thread = db_queryes.thread_details(thread)

    return jsonify(code=0, response={'thread': thread})


@app.route(prefix + '/thread/vote/', methods=['POST'])
def thread_vote():
    vote = request.json.get('vote', None)
    thread = request.json.get('thread', None)
    thread = int(thread)

    try:
        if vote == 1:
            g.cursor.execute("""UPDATE `threads` SET `likes` = `likes` + 1, `points` = `points` + 1 WHERE `id` = %s;""",
                             thread)
        else:
            g.cursor.execute(
                """UPDATE `threads` SET `dislikes` = `dislikes` + 1, `points` = `points` - 1 WHERE `id` = %s;""",
                thread)
        g.db.commit()

    except MySQLdb.Error:
        g.db.rollback()

    thread = db_queryes.thread_details(thread)

    return jsonify(code=0, response=thread)


@app.route(prefix + '/thread/subscribe/', methods=['POST'])
def thread_subscribe():
    user = request.json.get('user', None)
    thread = request.json.get('thread', None)

    try:
        g.cursor.execute("""INSERT INTO `users_threads` (`user`, `thread`) VALUE (%s, %s);""",
                         (user, thread))
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    return jsonify(code=0, response={'thread': thread, 'user': user})


@app.route(prefix + '/thread/unsubscribe/', methods=['POST'])
def thread_unsubscribe():
    user = request.json.get('user', None)
    thread = request.json.get('thread', None)

    try:
        g.cursor.execute("""DELETE FROM `users_threads` WHERE `user` = %s AND `thread` = %s;""", (user, thread))
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    return jsonify(code=0, response={'thread': thread, 'user': user})