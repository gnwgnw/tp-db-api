import MySQLdb

from flask import request, g, jsonify

from db_app import app
from settings import prefix
from utils import db_queryes


__author__ = 'gexogen'


@app.route(prefix + '/forum/create/', methods=['POST'])
def forum_create():
    name = request.json.get('name', None)
    short_name = request.json.get('short_name', None)
    user = request.json.get('user', None)

    try:
        g.cursor.execute("""INSERT INTO `forums` (`name`, `short_name`, `user`) VALUE (%s, %s, %s);""",
                         (name, short_name, user))
        g.db.commit()

    except MySQLdb.Error:
        g.db.rollback()

    forum = db_queryes.forum_details(short_name)

    return jsonify(code=0, response=forum)


@app.route(prefix + '/forum/details/')
def forum_details():
    short_name = request.args.get('forum', None)
    related = request.args.get('related', [])

    forum = db_queryes.forum_details(short_name)

    if 'user' in related:
        user = db_queryes.user_details(forum['user'])
        forum.update({'user': user})

    return jsonify(code=0, response=forum)


@app.route(prefix + '/forum/listPosts/')
def forum_list_posts():
    forum = request.args.get('forum', None)
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')
    related = request.args.getlist('related')

    limit = long(limit)  # TODO: bad code

    if order == 'desc':
        g.cursor.execute("""SELECT * FROM `posts` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                         (forum, since, limit))  # TODO: bad code - excess condition
    else:
        g.cursor.execute("""SELECT * FROM `posts` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                         (forum, since, limit))  # TODO: bad code - excess condition

    posts = [i for i in g.cursor.fetchall()]

    for post in posts:
        if 'user' in related:
            user = db_queryes.user_details(post['user'])
            post.update({'user': user})

        if 'forum' in related:
            forum = db_queryes.forum_details(post['forum'])
            post.update({'forum': forum})

        if 'thread' in related:
            thread = db_queryes.thread_details(post['thread'])
            post.update({'thread': thread})

        post.update({'date': str(post['date'])})  # TODO: bad code

    return jsonify(code=0, response=posts)


@app.route(prefix + '/forum/listThreads/')
def forum_list_threads():
    forum = request.args.get('forum', None)
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')
    related = request.args.getlist('related')

    limit = long(limit)  # TODO: bad code

    if order == 'desc':
        g.cursor.execute(
            """SELECT * FROM `threads` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
            (forum, since, limit))  # TODO: bad code - excess condition
    else:
        g.cursor.execute(
            """SELECT * FROM `threads` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
            (forum, since, limit))  # TODO: bad code - excess condition

    threads = [i for i in g.cursor.fetchall()]

    for thread in threads:
        if 'user' in related:
            user = db_queryes.user_details(thread['user'])
            thread.update({'user': user})

        if 'forum' in related:
            forum = db_queryes.forum_details(thread['forum'])
            thread.update({'forum': forum})

        thread.update({'date': str(thread['date'])})  # TODO: bad code

    return jsonify(code=0, response=threads)


@app.route(prefix + '/forum/listUsers/')
def forum_list_users():
    forum = request.args.get('forum', None)
    since_id = request.args.get('since_id', 0)
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    limit = long(limit)  # TODO: bad code
    since_id = long(since_id)  # TODO: bad code

    if order == 'desc':
        g.cursor.execute(
            """SELECT DISTINCT `users`.`id`, `username`, `name`, `about`, `isAnonymous`, `email` FROM `users`
            INNER JOIN `posts` ON `user` = `email` WHERE `forum` = %s AND `users`.`id` >= %s
            ORDER BY `name` DESC LIMIT %s;""",
            (forum, since_id, limit))  # TODO: bad code - excess condition
    else:
        g.cursor.execute(
            """SELECT DISTINCT `users`.`id`, `username`, `name`, `about`, `isAnonymous`, `email` FROM `users`
            INNER JOIN `posts` ON `user` = `email` WHERE `forum` = %s AND `users`.`id` >= %s
            ORDER BY `name` ASC LIMIT %s;""",
            (forum, since_id, limit))  # TODO: bad code - excess condition

    users = [i for i in g.cursor.fetchall()]

    for user in users:
        g.cursor.execute("""SELECT `followee` FROM `follower_followee` WHERE `follower` = %s;""", user['email'])
        following = [i['followee'] for i in g.cursor.fetchall()]

        g.cursor.execute("""SELECT `follower` FROM `follower_followee` WHERE `followee` = %s;""", user['email'])
        followers = [i['follower'] for i in g.cursor.fetchall()]

        g.cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", user['email'])
        threads = [i['thread'] for i in g.cursor.fetchall()]

        user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    return jsonify(code=0, response=users)