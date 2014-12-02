import MySQLdb
from flask import Blueprint, request, jsonify
from settings import prefix, db_connection
from utils import db_queryes
from utils.db_queryes import list_following
from utils.db_queryes import list_followers

__author__ = 'gexogen'
forum_api = Blueprint('forum_api', __name__)


@forum_api.route(prefix + '/forum/create/', methods=['POST'])
def forum_create():
    name = request.json.get('name', None)
    short_name = request.json.get('short_name', None)
    user = request.json.get('user', None)

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""INSERT INTO `forums` (`name`, `short_name`, `user`) VALUE (%s, %s, %s);""",
                       (name, short_name, user))
        db_connection.commit()

    except MySQLdb.Error:
        db_connection.rollback()

    forum = db_queryes.forum_details(cursor, short_name)

    cursor.close()
    return jsonify(code=0, response=forum)


@forum_api.route(prefix + '/forum/details/')
def forum_details():
    short_name = request.args.get('forum', None)
    related = request.args.get('related', [])

    if short_name is None:
        return jsonify(code=1, response="forum_details error")  # TODO error code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    forum = db_queryes.forum_details(cursor, short_name)

    if 'user' in related:
        user = db_queryes.user_details(cursor, forum['user'])
        forum.update({'user': user})

    cursor.close()
    return jsonify(code=0, response=forum)


@forum_api.route(prefix + '/forum/listPosts/')
def forum_list_posts():
    forum = request.args.get('forum', None)
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')
    related = request.args.getlist('related')

    if forum is None:
        return jsonify(code=1, response="error")  # TODO error code

    limit = long(limit)  # TODO: bad code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
    if order == 'desc':
        cursor.execute("""SELECT * FROM `posts` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                       (forum, since, limit))  # TODO: bad code - excess condition
    else:
        cursor.execute("""SELECT * FROM `posts` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                       (forum, since, limit))  # TODO: bad code - excess condition

    posts = [i for i in cursor.fetchall()]

    for post in posts:
        if 'user' in related:
            user = db_queryes.user_details(cursor, post['user'])
            post.update({'user': user})

        if 'forum' in related:
            forum = db_queryes.forum_details(cursor, post['forum'])
            post.update({'forum': forum})

        if 'thread' in related:
            thread = db_queryes.thread_details(cursor, post['thread'])
            post.update({'thread': thread})

        post.update({'date': str(post['date'])})  # TODO: bad code

    cursor.close()
    return jsonify(code=0, response=posts)


@forum_api.route(prefix + '/forum/listThreads/')
def forum_list_threads():
    forum = request.args.get('forum', None)
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')
    related = request.args.getlist('related')

    if forum is None:
        return jsonify(code=1, response="error")  # TODO error code

    limit = long(limit)  # TODO: bad code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    if order == 'desc':
        cursor.execute(
            """SELECT * FROM `threads` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
            (forum, since, limit))  # TODO: bad code - excess condition
    else:
        cursor.execute(
            """SELECT * FROM `threads` WHERE `forum` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
            (forum, since, limit))  # TODO: bad code - excess condition

    threads = [i for i in cursor.fetchall()]

    for thread in threads:
        if 'user' in related:
            user = db_queryes.user_details(cursor, thread['user'])
            thread.update({'user': user})

        if 'forum' in related:
            forum = db_queryes.forum_details(cursor, thread['forum'])
            thread.update({'forum': forum})

        thread.update({'date': str(thread['date'])})  # TODO: bad code

    cursor.close()
    return jsonify(code=0, response=threads)


@forum_api.route(prefix + '/forum/listUsers/')
def forum_list_users():
    forum = request.args.get('forum', None)
    since_id = request.args.get('since_id', 0)
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    if forum is None:
        return jsonify(code=1, response="error")  # TODO error code

    limit = long(limit)  # TODO: bad code
    since_id = long(since_id)  # TODO: bad code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
    if order == 'desc':
        cursor.execute(
            """SELECT DISTINCT `users`.`id`, `username`, `name`, `about`, `isAnonymous`, `email` FROM `users`
            INNER JOIN `posts` ON `user` = `email` WHERE `forum` = %s AND `users`.`id` >= %s
            ORDER BY `name` DESC LIMIT %s;""",
            (forum, since_id, limit))  # TODO: bad code - excess condition
    else:
        cursor.execute(
            """SELECT DISTINCT `users`.`id`, `username`, `name`, `about`, `isAnonymous`, `email` FROM `users`
            INNER JOIN `posts` ON `user` = `email` WHERE `forum` = %s AND `users`.`id` >= %s
            ORDER BY `name` ASC LIMIT %s;""",
            (forum, since_id, limit))  # TODO: bad code - excess condition

    users = [i for i in cursor.fetchall()]

    for user in users:
        following = list_following(cursor, user['id'])
        followers = list_followers(cursor, user['id'])

        cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", user['email'])
        threads = [i['thread'] for i in cursor.fetchall()]

        user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    cursor.close()
    return jsonify(code=0, response=users)