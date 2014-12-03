import MySQLdb
from flask import Blueprint, request, jsonify
from settings import prefix, db_connection
from utils import db_queryes

__author__ = 'gexogen'

post_api = Blueprint('post_api', __name__)


@post_api.route(prefix + '/post/create/', methods=['POST'])
def post_create():
    parent = request.json.get('parent', None)
    thread = request.json.get('thread', None)
    is_deleted = request.json.get('isDeleted', False)
    is_spam = request.json.get('isSpam', False)
    is_edited = request.json.get('isEdited', False)
    is_post_apiroved = request.json.get('isApproved', False)
    is_highlighted = request.json.get('isHighlighted', False)
    forum = request.json.get('forum', None)
    user = request.json.get('user', None)
    date = request.json.get('date', None)
    message = request.json.get('message', None)

    cursor = db_connection.cursor()

    try:
        cursor.execute(
            """INSERT INTO `posts`
            (`parent`, `thread`, `isDeleted`, `isSpam`, `isEdited`, `isApproved`, `isHighlighted`, `forum`,
             `user`, `date`, `message`)
            VALUE (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
            (parent, thread, is_deleted, is_spam, is_edited, is_post_apiroved, is_highlighted, forum, user, date,
             message))

        post_id = cursor.lastrowid

        cursor.execute("""UPDATE `threads` SET `posts` = `posts` + 1 WHERE `id` = %s;""", thread)  # TODO: make view
        db_connection.commit()

    except MySQLdb.Error:
        db_connection.rollback()

    cursor.close()

    post = {
        "date": date,
        "forum": forum,
        "id": post_id,
        "isApproved": is_post_apiroved,
        "isDeleted": is_deleted,
        "isEdited": is_edited,
        "isHighlighted": is_highlighted,
        "isSpam": is_spam,
        "message": message,
        "parent": parent,
        "thread": thread,
        "user": user
    }
    return jsonify(code=0, response=post)


@post_api.route(prefix + '/post/details/')
def post_details():
    id = request.args.get('post', None)
    related = request.args.getlist('related')

    if id is None:
        return jsonify(code=1, response="post_details error")  # TODO error code

    id = int(id)

    if id < 1:
        return jsonify(code=1, response='Error post detail')

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    post = db_queryes.post_details(cursor, id)

    if 'user' in related:
        user = db_queryes.user_details(cursor, post['user'])
        post.update({'user': user})

    if 'forum' in related:
        forum = db_queryes.forum_details(cursor, post['forum'])
        post.update({'forum': forum})

    if 'thread' in related:
        thread = db_queryes.thread_details(cursor, post['thread'])
        post.update({'thread': thread})

    cursor.close()
    return jsonify(code=0, response=post)


@post_api.route(prefix + '/post/list/')
def post_list():
    forum = request.args.get('forum', None)
    thread = request.args.get('thread', None)  # TODO: bad code - if state
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    if thread is None and forum is None:
        return jsonify(code=1, response="error")  # TODO error code

    limit = long(limit)  # TODO: bad code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    if forum is not None:
        if order == 'desc':
            cursor.execute(
                """SELECT * FROM `posts` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                (forum, since, limit))
        else:
            cursor.execute(
                """SELECT * FROM `posts` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                (forum, since, limit))
    else:
        if order == 'desc':
            cursor.execute(
                """SELECT * FROM `posts` WHERE `thread` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                (thread, since, limit))
        else:
            cursor.execute(
                """SELECT * FROM `posts` WHERE `thread` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                (thread, since, limit))

    posts = [i for i in cursor.fetchall()]
    cursor.close()

    for post in posts:
        post.update({'date': str(post['date'])})  # TODO: bad code

    return jsonify(code=0, response=posts)


@post_api.route(prefix + '/post/remove/', methods=['POST'])
def post_remove():
    post = request.json.get('post', None)
    post = int(post)

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""SELECT `thread` FROM `posts` WHERE `id` = %s;""", post)
        thread = cursor.fetchone()
        cursor.execute("""UPDATE `posts` SET `isDeleted` = TRUE WHERE `id` = %s;""", post)
        cursor.execute("""UPDATE `threads` SET `posts` = `posts` - 1 WHERE `id` = %s;""",
                       thread['thread'])  # TODO: make view
        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    cursor.close()
    return jsonify(code=0, response={'post': post})


@post_api.route(prefix + '/post/restore/', methods=['POST'])
def post_restore():
    post = request.json.get('post', None)
    post = int(post)
    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""SELECT `thread` FROM `posts` WHERE `id` = %s;""", post)
        thread = cursor.fetchone()
        cursor.execute("""UPDATE `posts` SET `isDeleted` = FALSE WHERE `id` = %s;""", post)
        cursor.execute("""UPDATE `threads` SET `posts` = `posts` + 1 WHERE `id` = %s;""",
                       thread['thread'])  # TODO: make view
        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    cursor.close()
    return jsonify(code=0, response={'post': post})


@post_api.route(prefix + '/post/update/', methods=['POST'])
def post_update():
    message = request.json.get('message', None)
    post = request.json.get('post', None)
    post = int(post)

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""UPDATE `posts` SET `message` = %s WHERE `id` = %s;""", (post, message))
        db_connection.commit()

    except MySQLdb.Error:
        db_connection.rollback()

    post = db_queryes.post_details(cursor, post)
    cursor.close()
    return jsonify(code=0, response=post)


@post_api.route(prefix + '/post/vote/', methods=['POST'])
def post_vote():
    vote = request.json.get('vote', None)
    post = request.json.get('post', None)
    post = int(post)
    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        if vote == 1:
            cursor.execute("""UPDATE `posts` SET `likes` = `likes` + 1, `points` = `points` + 1 WHERE `id` = %s;""",
                           post)
        else:
            cursor.execute(
                """UPDATE `posts` SET `dislikes` = `dislikes` + 1, `points` = `points` - 1 WHERE `id` = %s;""", post)
        db_connection.commit()

    except MySQLdb.Error:
        db_connection.rollback()

    post = db_queryes.post_details(cursor, post)

    cursor.close()
    return jsonify(code=0, response=post)