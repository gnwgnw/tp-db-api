import MySQLdb

from flask import request, g, jsonify

from db_app import app
from settings import prefix
from utils import db_queryes
from utils.helper import extract_params


__author__ = 'gexogen'


@app.route(prefix + '/user/create/', methods=['POST'])
def user_create():
    params = ['email', 'username', 'name', 'about', 'isAnonymous']
    params = extract_params(request.json, params)
    # TODO: required params
    if params['isAnonymous'] is None:
        params['isAnonymous'] = False

    try:
        g.cursor.execute(
            """INSERT INTO `users` (`email`, `username`, `name`, `about`, `isAnonymous`) VALUE (%s, %s, %s, %s, %s);""",
            (params['email'], params['username'], params['name'], params['about'], params['isAnonymous']))
        g.db.commit()

    except MySQLdb.Error:
        g.db.rollback()
        return jsonify(code=5, response='User already exists')

    g.cursor.execute("""SELECT * FROM `users` WHERE `email` = %s""", params['email'])
    user = g.cursor.fetchone()

    return jsonify(code=0, response=user)


@app.route(prefix + '/user/details/')
def user_details():
    email = request.args.get('user', None)

    user = db_queryes.user_details(email)

    return jsonify(code=0, response=user)


@app.route(prefix + '/user/listPosts/')
def user_list_posts():
    user = request.args.get('user', None)
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    limit = long(limit)  # TODO: bad code

    if order == 'desc':
        g.cursor.execute("""SELECT * FROM `posts` WHERE `user` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                         (user, since, limit))  # TODO: bad code - excess condition
    else:
        g.cursor.execute("""SELECT * FROM `posts` WHERE `user` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                         (user, since, limit))  # TODO: bad code - excess condition

    posts = [i for i in g.cursor.fetchall()]

    for post in posts:
        post.update({'date': str(post['date'])})  # TODO: bad code

    return jsonify(code=0, response=posts)


@app.route(prefix + '/user/updateProfile/', methods=['POST'])
def user_update_profile():
    user = request.json.get('user', None)
    about = request.json.get('about', None)
    name = request.json.get('name', None)

    try:
        g.cursor.execute("""UPDATE `users` SET `about` = %s, `name` = %s WHERE `email` = %s;""", (about, name, user))
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    user = db_queryes.user_details(user)

    return jsonify(code=0, response=user)


@app.route(prefix + '/user/follow/', methods=['POST'])
def user_follow():
    follower = request.json.get('follower', None)
    followee = request.json.get('followee', None)

    try:
        g.cursor.execute("""INSERT INTO `follower_followee` (`follower`, `followee`) VALUE (%s, %s);""",
                         (follower, followee))
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    user = db_queryes.user_details(follower)

    return jsonify(code=0, response=user)


@app.route(prefix + '/user/listFollowers/')
def user_list_followers():
    user = request.args.get('user', None)
    since_id = request.args.get('since_id', 0)
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    limit = long(limit)  # TODO: bad code
    since_id = long(since_id)  # TODO: bad code

    if order == 'desc':
        g.cursor.execute(
            """SELECT DISTINCT * FROM `users` INNER JOIN `follower_followee` ON `email` = `follower`
            WHERE `followee` = %s AND `id` >= %s ORDER BY `name` DESC LIMIT %s;""",
            (user, since_id, limit))
    else:
        g.cursor.execute(
            """SELECT DISTINCT * FROM `users` INNER JOIN `follower_followee` ON `email` = `follower`
            WHERE `followee` = %s AND `id` >= %s ORDER BY `name` ASC LIMIT %s;""",
            (user, since_id, limit))

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


@app.route(prefix + '/user/listFollowing/')
def user_list_following():
    user = request.args.get('user', None)
    since_id = request.args.get('since_id', 0)
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    limit = long(limit)  # TODO: bad code
    since_id = long(since_id)  # TODO: bad code

    if order == 'desc':
        g.cursor.execute(
            """SELECT DISTINCT * FROM `users` INNER JOIN `follower_followee` ON `email` = `followee`
            WHERE `follower` = %s AND `id` >= %s ORDER BY `name` DESC LIMIT %s;""",
            (user, since_id, limit))
    else:
        g.cursor.execute(
            """SELECT DISTINCT * FROM `users` INNER JOIN `follower_followee` ON `email` = `followee`
            WHERE `follower` = %s AND `id` >= %s ORDER BY `name` ASC LIMIT %s;""",
            (user, since_id, limit))

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


@app.route(prefix + '/user/unfollow/', methods=['POST'])
def user_unfollow():
    follower = request.json.get('follower', None)
    followee = request.json.get('followee', None)

    try:
        g.cursor.execute("""DELETE FROM `follower_followee` WHERE `follower` = %s AND `followee` = %s;""",
                         (follower, followee))
        g.db.commit()
    except MySQLdb.Error:
        g.db.rollback()

    user = db_queryes.user_details(follower)

    return jsonify(code=0, response=user)