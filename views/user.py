import MySQLdb
from flask import Blueprint, request, jsonify
from settings import prefix, db_connection
from utils import db_queryes
from utils.db_queryes import list_followers, list_following
from utils.helper import extract_params

__author__ = 'gexogen'

user_api = Blueprint('user_api', __name__)


@user_api.route(prefix + '/user/create/', methods=['POST'])
def user_create():
    params = ['email', 'username', 'name', 'about', 'isAnonymous']
    params = extract_params(request.json, params)
    # TODO: required params
    if params['isAnonymous'] is None:
        params['isAnonymous'] = False

    cursor = db_connection.cursor()
    try:

        cursor.execute(
            """INSERT INTO `users` (`email`, `username`, `name`, `about`, `isAnonymous`) VALUE (%s, %s, %s, %s, %s);""",
            (params['email'], params['username'], params['name'], params['about'], params['isAnonymous']))

        user_id = cursor.lastrowid

        db_connection.commit()

    except MySQLdb.Error:
        db_connection.rollback()
        cursor.close()
        return jsonify(code=5, response='User already exists')

    cursor.close()

    user = params
    user.update({'id': user_id})

    return jsonify(code=0, response=user)


@user_api.route(prefix + '/user/details/')
def user_details():
    email = request.args.get('user', None)

    if email is None:
        return jsonify(code=1, response="user_details error")  # TODO error code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
    user = db_queryes.user_details(cursor, email)
    cursor.close()

    return jsonify(code=0, response=user)


@user_api.route(prefix + '/user/listPosts/')
def user_list_posts():
    user = request.args.get('user', None)
    since = request.args.get('since', '0000-00-00 00:00:00')
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    if user is None:
        return jsonify(code=1, response="user_listPosts error")  # TODO error code

    limit = long(limit)  # TODO: bad code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    if order == 'desc':
        cursor.execute("""SELECT * FROM `posts` WHERE `user` = %s AND `date` >= %s ORDER BY `date` DESC LIMIT %s;""",
                       (user, since, limit))  # TODO: bad code - excess condition
    else:
        cursor.execute("""SELECT * FROM `posts` WHERE `user` = %s AND `date` >= %s ORDER BY `date` ASC LIMIT %s;""",
                       (user, since, limit))  # TODO: bad code - excess condition

    posts = [i for i in cursor.fetchall()]

    cursor.close()

    for post in posts:
        post.update({'date': str(post['date'])})  # TODO: bad code

    return jsonify(code=0, response=posts)


@user_api.route(prefix + '/user/updateProfile/', methods=['POST'])
def user_update_profile():
    user = request.json.get('user', None)
    about = request.json.get('about', None)
    name = request.json.get('name', None)

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""UPDATE `users` SET `about` = %s, `name` = %s WHERE `email` = %s;""", (about, name, user))
        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    user = db_queryes.user_details(cursor, user)
    cursor.close()

    return jsonify(code=0, response=user)


@user_api.route(prefix + '/user/follow/', methods=['POST'])
def user_follow():
    follower = request.json.get('follower', None)
    followee = request.json.get('followee', None)

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    try:
        cursor.execute("""INSERT INTO `follower_followee` (`follower`, `followee`)
                          SELECT `u1`.`id`, `u2`.`id` FROM `users` AS `u1`
                          JOIN `users` AS `u2` ON `u1`.`email` = %s AND `u2`.`email` = %s;""", (follower, followee))

        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    user = db_queryes.user_details(cursor, follower)
    cursor.close()

    return jsonify(code=0, response=user)


@user_api.route(prefix + '/user/listFollowers/')
def user_list_followers():
    user = request.args.get('user', None)
    since_id = request.args.get('since_id', 0)
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    if user is None:
        return jsonify(code=1, response="user_listPosts error")  # TODO error code

    limit = long(limit)  # TODO: bad code
    since_id = long(since_id)  # TODO: bad code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    if order == 'desc':
        cursor.execute("""SELECT DISTINCT `u1`.* FROM `users` AS `u1`
                          JOIN `follower_followee` AS `ff` ON `u1`.`id` = `ff`.`follower`
                          JOIN `users` AS `u2` ON `ff`.`followee` = `u2`.`id`
                          WHERE `u2`.`email` = %s AND `u1`.`id` >= %s ORDER BY `name` DESC LIMIT %s;""",
                       (user, since_id, limit))
    else:
        cursor.execute("""SELECT DISTINCT `u1`.* FROM `users` AS `u1`
                          JOIN `follower_followee` AS `ff` ON `u1`.`id` = `ff`.`follower`
                          JOIN `users` AS `u2` ON `ff`.`followee` = `u2`.`id`
                          WHERE `u2`.`email` = %s AND `u1`.`id` >= %s ORDER BY `name` ASC LIMIT %s;""",
                       (user, since_id, limit))

    users = [i for i in cursor.fetchall()]

    for user in users:
        following = list_following(cursor, user['id'])
        followers = list_followers(cursor, user['id'])

        cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", user['email'])
        threads = [i['thread'] for i in cursor.fetchall()]

        user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    cursor.close()

    return jsonify(code=0, response=users)


@user_api.route(prefix + '/user/listFollowing/')
def user_list_following():
    user = request.args.get('user', None)
    since_id = request.args.get('since_id', 0)
    limit = request.args.get('limit', 18446744073709551615)  # TODO: hard code
    order = request.args.get('order', 'desc')

    if user is None:
        return jsonify(code=1, response="user_listPosts error")  # TODO error code

    limit = long(limit)  # TODO: bad code
    since_id = long(since_id)  # TODO: bad code

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    if order == 'desc':
        cursor.execute("""SELECT DISTINCT `u1`.* FROM `users` AS `u1`
                          JOIN `follower_followee` AS `ff` ON `u1`.`id` = `ff`.`followee`
                          JOIN `users` AS `u2` ON `ff`.`follower` = `u2`.`id`
                          WHERE `u2`.`email` = %s AND `u1`.`id` >= %s ORDER BY `name` DESC LIMIT %s;""",
                       (user, since_id, limit))
    else:
        cursor.execute("""SELECT DISTINCT `u1`.* FROM `users` AS `u1`
                          JOIN `follower_followee` AS `ff` ON `u1`.`id` = `ff`.`followee`
                          JOIN `users` AS `u2` ON `ff`.`follower` = `u2`.`id`
                          WHERE `u2`.`email` = %s AND `u1`.`id` >= %s ORDER BY `name` ASC LIMIT %s;""",
                       (user, since_id, limit))

    users = [i for i in cursor.fetchall()]

    for user in users:
        following = list_following(cursor, user['id'])
        followers = list_followers(cursor, user['id'])

        cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", user['email'])
        threads = [i['thread'] for i in cursor.fetchall()]

        user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    cursor.close()
    return jsonify(code=0, response=users)


@user_api.route(prefix + '/user/unfollow/', methods=['POST'])
def user_unfollow():
    follower = request.json.get('follower', None)
    followee = request.json.get('followee', None)

    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""SELECT `u1`.`id`, `u2`.`id` FROM `users` AS `u1`
                      INNER JOIN `users` AS `u2` ON `u1`.`email` = %s AND `u2`.`email` = %s;""", (follower, followee))
        f_er_id, f_ee_id = cursor.fetchone().values()

        cursor.execute("""DELETE FROM `follower_followee` WHERE `follower` = %s AND `followee` = %s;""",
                       (f_er_id, f_ee_id))
        db_connection.commit()
    except MySQLdb.Error:
        db_connection.rollback()

    user = db_queryes.user_details(cursor, follower)
    cursor.close()
    return jsonify(code=0, response=user)