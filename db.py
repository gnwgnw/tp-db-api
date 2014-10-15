import MySQLdb

from flask import Flask, request, jsonify, g

from settings import *
from utils import helper, db_queryes


app = Flask(__name__)
prefix = '/db/api'
sql_file_name = helper.rel('../conf/my_db.sql')


@app.before_request
def before_request():
    g.db = MySQLdb.connect(host=HOST_NAME, user=USER_NAME, passwd=USER_PASSWORD, db=DB_NAME, charset='utf8')
    g.cursor = g.db.cursor(MySQLdb.cursors.DictCursor)


@app.teardown_request
def teardown_request(exception):
    g.db.close()
    g.cursor.close()


@app.route(prefix + '/clear/', methods=['POST'])
def clear():
    sql = ''
    sql_file = open(sql_file_name)
    for line in sql_file:
        sql += line
        if ';' in line:
            g.cursor.execute(sql)
            g.db.commit()
            sql = ''

    sql_file.close()

    return jsonify(code=0, response='OK')


@app.route(prefix + '/user/create/', methods=['POST'])
def user_create():
    email = request.json.get('email', None)
    username = request.json.get('username', None)
    name = request.json.get('name', None)
    about = request.json.get('about', None)
    is_anonymous = request.json.get('isAnonymous', None)

    try:
        if is_anonymous:
            g.cursor.execute("""INSERT INTO `users` (`email`, `isAnonymous`) VALUE (%s, %s);""", (email, is_anonymous))
        else:
            g.cursor.execute("""INSERT INTO `users` (`username`, `about`, `name`, `email`) VALUE (%s, %s, %s, %s);""",
                             (username, about, name, email))
        g.db.commit()

    except MySQLdb.Error:
        g.db.rollback()
        return jsonify(code=5, response='User already exists')

    g.cursor.execute("""SELECT * FROM `users` WHERE `email` = %s""", email)
    user = g.cursor.fetchone()

    return jsonify(code=0, response=user)


@app.route(prefix + '/user/details/')
def user_details():
    email = request.args.get('user', None)

    user = db_queryes.user_details(email)

    return jsonify(code=0, response=user)


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


if __name__ == "__main__":
    app.run()
