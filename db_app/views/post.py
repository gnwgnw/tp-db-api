import MySQLdb

from flask import request, g, jsonify

from db_app import app
from settings import prefix
from utils import db_queryes


__author__ = 'gexogen'


@app.route(prefix + '/post/create/', methods=['POST'])
def post_create():
    parent = request.json.get('parent', None)
    thread = request.json.get('thread', None)
    is_deleted = request.json.get('isDeleted', False)
    is_spam = request.json.get('isSpam', False)
    is_edited = request.json.get('isEdited', False)
    is_approved = request.json.get('isApproved', False)
    is_highlighted = request.json.get('isHighlighted', False)
    forum = request.json.get('forum', None)
    user = request.json.get('user', None)
    date = request.json.get('date', None)
    message = request.json.get('message', None)

    try:
        g.cursor.execute(
            """INSERT INTO `posts`
            (`parent`, `thread`, `isDeleted`, `isSpam`, `isEdited`, `isApproved`, `isHighlighted`, `forum`,
             `user`, `date`, `message`)
            VALUE (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);""",
            (parent, thread, is_deleted, is_spam, is_edited, is_approved, is_highlighted, forum, user, date, message))

        g.cursor.execute("""UPDATE `threads` SET `posts` = `posts` + 1 WHERE `id` = %s;""", thread)  # TODO: make view
        g.db.commit()

    except MySQLdb.Error:
        g.db.rollback()

    g.cursor.execute("""SELECT * FROM `posts` WHERE `user` = %s AND `date` = %s AND `message` = %s""",
                     (user, date, message))
    post = g.cursor.fetchone()

    return jsonify(code=0, response=post)


@app.route(prefix + '/post/details/')
def post_details():
    id = request.args.get('post', None)
    related = request.args.getlist('related')
    id = int(id)

    if id < 1:
        return jsonify(code=1, response='Error post detail')

    post = db_queryes.post_details(id)

    if 'user' in related:
        user = db_queryes.user_details(post['user'])
        post.update({'user': user})

    if 'forum' in related:
        forum = db_queryes.forum_details(post['forum'])
        post.update({'forum': forum})

    if 'thread' in related:
        thread = db_queryes.thread_details(post['thread'])
        post.update({'thread': thread})

    return jsonify(code=0, response=post)


@app.route(prefix + '/post/list/')
def post_list():
    forum = request.args.get('forum', None)
    thread = request.args.get('thread', None)  # TODO: bad code - if state
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    limit = long(limit)  # TODO: bad code

    if forum is not None:
        if order == 'desc':
            g.cursor.execute(
                """SELECT * FROM `posts` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                (forum, since, limit))
        else:
            g.cursor.execute(
                """SELECT * FROM `posts` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                (forum, since, limit))
    else:
        if order == 'desc':
            g.cursor.execute(
                """SELECT * FROM `posts` WHERE `thread` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                (thread, since, limit))
        else:
            g.cursor.execute(
                """SELECT * FROM `posts` WHERE `thread` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                (thread, since, limit))

    posts = [i for i in g.cursor.fetchall()]

    for post in posts:
        post.update({'date': str(post['date'])})  # TODO: bad code

    return jsonify(code=0, response=posts)


@app.route(prefix + '/post/remove/', methods=['POST'])
def post_remove():
    post = request.json.get('post', None)
    post = int(post)

    try:
        g.cursor.execute("""SELECT `thread` FROM `posts` WHERE `id` = %s;""", post)
        thread = g.cursor.fetchone()
        g.cursor.execute("""UPDATE `posts` SET `isDeleted` = TRUE WHERE `id` = %s;""", post)
        g.cursor.execute("""UPDATE `threads` SET `posts` = `posts` - 1 WHERE `id` = %s;""",
                         thread['thread'])  # TODO: make view
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    return jsonify(code=0, response={'post': post})


@app.route(prefix + '/post/restore/', methods=['POST'])
def post_restore():
    post = request.json.get('post', None)
    post = int(post)

    try:
        g.cursor.execute("""SELECT `thread` FROM `posts` WHERE `id` = %s;""", post)
        thread = g.cursor.fetchone()
        g.cursor.execute("""UPDATE `posts` SET `isDeleted` = FALSE WHERE `id` = %s;""", post)
        g.cursor.execute("""UPDATE `threads` SET `posts` = `posts` + 1 WHERE `id` = %s;""",
                         thread['thread'])  # TODO: make view
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    return jsonify(code=0, response={'post': post})


@app.route(prefix + '/post/update/', methods=['POST'])
def post_update():
    message = request.json.get('message', None)
    post = request.json.get('post', None)
    post = int(post)

    try:
        g.cursor.execute("""UPDATE `posts` SET `message` = %s WHERE `id` = %s;""", (post, message))
        g.db.commit()

    except MySQLdb.Error:
        g.db.rollback()

    post = db_queryes.post_details(post)

    return jsonify(code=0, response=post)


@app.route(prefix + '/post/vote/', methods=['POST'])
def post_vote():
    vote = request.json.get('vote', None)
    post = request.json.get('post', None)
    post = int(post)

    try:
        if vote == 1:
            g.cursor.execute("""UPDATE `posts` SET `likes` = `likes` + 1, `points` = `points` + 1 WHERE `id` = %s;""",
                             post)
        else:
            g.cursor.execute(
                """UPDATE `posts` SET `dislikes` = `dislikes` + 1, `points` = `points` - 1 WHERE `id` = %s;""", post)
        g.db.commit()

    except MySQLdb.Error:
        g.db.rollback()

    post = db_queryes.post_details(post)

    return jsonify(code=0, response=post)