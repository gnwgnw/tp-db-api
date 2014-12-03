import MySQLdb
from flask import Blueprint, request, jsonify
from settings import prefix, db_connection
from utils import db_queryes

__author__ = 'gexogen'

thread_api = Blueprint('thread_api', __name__)


@thread_api.route(prefix + '/thread/create/', methods=['POST'])
def thread_create():
    is_deleted = request.json.get('isDeleted', False)
    forum = request.json.get('forum', None)
    title = request.json.get('title', None)
    is_closed = request.json.get('isClosed', False)
    user = request.json.get('user', None)
    date = request.json.get('date', None)
    message = request.json.get('message', None)
    slug = request.json.get('slug', None)

    cursor = db_connection.cursor()
    try:
        cursor.execute("""INSERT INTO `threads`
                          (`isDeleted`, `forum`, `title`, `isClosed`, `user`, `date`, `message`, `slug`)
                          VALUE (%s, %s, %s, %s, %s, %s, %s, %s);""",
                       (is_deleted, forum, title, is_closed, user, date, message, slug))

        thread_id = cursor.lastrowid

        db_connection.commit()

    except MySQLdb.Error:
        db_connection.rollback()

    cursor.close()

    thread = {
        "date": date,
        "forum": forum,
        "id": thread_id,
        "isClosed": is_closed,
        "isDeleted": is_deleted,
        "message": message,
        "slug": slug,
        "title": title,
        "user": user
    }
    return jsonify(code=0, response=thread)


@thread_api.route(prefix + '/thread/details/')
def thread_details():
    id = request.args.get('thread', None)
    related = request.args.getlist('related')
    id = int(id)

    if 'thread' in related:
        return jsonify(code=3, response='Error thread')

    if id is None or id < 1:
        return jsonify(code=1, response="thread_details error")  # TODO error code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    thread = db_queryes.thread_details(cursor, id)

    if 'user' in related:
        user = db_queryes.user_details(cursor, thread['user'])
        thread.update({'user': user})

    if 'forum' in related:
        forum = db_queryes.forum_details(cursor, thread['forum'])
        thread.update({'forum': forum})

    cursor.close()

    return jsonify(code=0, response=thread)


@thread_api.route(prefix + '/thread/list/')
def thread_list():
    forum = request.args.get('forum', None)
    user = request.args.get('user', None)  # TODO: bad code - if state
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    if user is None and forum is None:
        return jsonify(code=1, response="error")  # TODO error code

    limit = long(limit)  # TODO: bad code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
    if forum is not None:
        if order == 'desc':
            cursor.execute(
                """SELECT * FROM `threads` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                (forum, since, limit))
        else:
            cursor.execute(
                """SELECT * FROM `threads` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                (forum, since, limit))
    else:
        if order == 'desc':
            cursor.execute(
                """SELECT * FROM `threads` WHERE `user` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                (user, since, limit))
        else:
            cursor.execute(
                """SELECT * FROM `threads` WHERE `user` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                (user, since, limit))

    threads = [i for i in cursor.fetchall()]

    for thread in threads:
        thread.update({'date': str(thread['date'])})  # TODO: bad code

    cursor.close()
    return jsonify(code=0, response=threads)


@thread_api.route(prefix + '/thread/listPosts/')
def thread_list_posts():
    thread = request.args.get('thread', None)
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    if thread is None:
        return jsonify(code=1, response="thread_listPosts error")  # TODO error code

    limit = long(limit)  # TODO: bad code
    thread = int(thread)  # TODO: bad code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    if order == 'desc':
        cursor.execute(
            """SELECT * FROM `posts` WHERE `thread` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
            (thread, since, limit))  # TODO: bad code - excess condition
    else:
        cursor.execute(
            """SELECT * FROM `posts` WHERE `thread` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
            (thread, since, limit))  # TODO: bad code - excess condition

    posts = [i for i in cursor.fetchall()]

    for post in posts:
        post.update({'date': str(post['date'])})  # TODO: bad code

    cursor.close()
    return jsonify(code=0, response=posts)


@thread_api.route(prefix + '/thread/remove/', methods=['POST'])
def thread_remove():
    thread = request.json.get('thread', None)
    thread = int(thread)  # TODO: bad code

    cursor = db_connection.cursor()

    try:
        cursor.execute("""UPDATE `threads` SET `isDeleted` = TRUE, `posts` = 0 WHERE `id` = %s;""", thread)
        cursor.execute("""UPDATE `posts` SET `isDeleted` = TRUE WHERE `thread` = %s;""", thread)
        db_connection.commit()

    except MySQLdb.Error:
        db_connection.rollback()

    cursor.close()
    return jsonify(code=0, response={'thread': thread})


@thread_api.route(prefix + '/thread/restore/', methods=['POST'])
def thread_restore():
    thread = request.json.get('thread', None)
    thread = int(thread)

    cursor = db_connection.cursor()
    try:
        count = cursor.execute("""UPDATE `posts` SET `isDeleted` = FALSE WHERE `thread` = %s;""", thread)
        cursor.execute("""UPDATE `threads` SET `isDeleted` = FALSE, `posts` = %s WHERE `id` = %s;""", (count, thread))  # TODO: make view
        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    cursor.close()
    return jsonify(code=0, response={'thread': thread})


@thread_api.route(prefix + '/thread/close/', methods=['POST'])
def thread_close():
    thread = request.json.get('thread', None)
    thread = int(thread)

    cursor = db_connection.cursor()
    try:
        cursor.execute("""UPDATE `threads` SET `isClosed` = TRUE WHERE `id` = %s;""", thread)  # TODO: make view
        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    cursor.close()
    return jsonify(code=0, response={'thread': thread})


@thread_api.route(prefix + '/thread/open/', methods=['POST'])
def thread_open():
    thread = request.json.get('thread', None)
    thread = int(thread)

    cursor = db_connection.cursor()
    try:
        cursor.execute("""UPDATE `threads` SET `isClosed` = FALSE WHERE `id` = %s;""", thread)  # TODO: make view
        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    cursor.close()
    return jsonify(code=0, response={'thread': thread})


@thread_api.route(prefix + '/thread/update/', methods=['POST'])
def thread_update():
    message = request.json.get('message', None)
    slug = request.json.get('slug', None)
    thread = request.json.get('thread', None)
    thread = int(thread)

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""UPDATE `threads` SET `message` = %s, `slug` = %s WHERE `id` = %s;""",
                       (message, slug, thread))  # TODO: make view
        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    thread = db_queryes.thread_details(cursor, thread)

    cursor.close()
    return jsonify(code=0, response={'thread': thread})


@thread_api.route(prefix + '/thread/vote/', methods=['POST'])
def thread_vote():
    vote = request.json.get('vote', None)
    thread = request.json.get('thread', None)
    thread = int(thread)

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        if vote == 1:
            cursor.execute("""UPDATE `threads` SET `likes` = `likes` + 1, `points` = `points` + 1 WHERE `id` = %s;""",
                             thread)
        else:
            cursor.execute(
                """UPDATE `threads` SET `dislikes` = `dislikes` + 1, `points` = `points` - 1 WHERE `id` = %s;""",
                thread)
        db_connection.commit()

    except MySQLdb.Error:
        db_connection.rollback()

    thread = db_queryes.thread_details(cursor, thread)

    cursor.close()
    return jsonify(code=0, response=thread)


@thread_api.route(prefix + '/thread/subscribe/', methods=['POST'])
def thread_subscribe():
    user = request.json.get('user', None)
    thread = request.json.get('thread', None)
    cursor = db_connection.cursor()

    try:
        cursor.execute("""INSERT INTO `users_threads` (`user`, `thread`) VALUE (%s, %s);""",
                         (user, thread))
        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    cursor.close()
    return jsonify(code=0, response={'thread': thread, 'user': user})


@thread_api.route(prefix + '/thread/unsubscribe/', methods=['POST'])
def thread_unsubscribe():
    user = request.json.get('user', None)
    thread = request.json.get('thread', None)
    cursor = db_connection.cursor()

    try:
        cursor.execute("""DELETE FROM `users_threads` WHERE `user` = %s AND `thread` = %s;""", (user, thread))
        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    cursor.close()
    return jsonify(code=0, response={'thread': thread, 'user': user})