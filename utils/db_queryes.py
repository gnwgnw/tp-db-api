import MySQLdb
from settings import db_connection

__author__ = 'gexogen'


def user_details(email):
    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""SELECT * FROM `users` WHERE `email` = %s;""", email)
    user = cursor.fetchone()

    if user is None:
        cursor.close()
        return None

    cursor.execute("""SELECT `followee` FROM `follower_followee` WHERE `follower` = %s;""", email)
    following = [i['followee'] for i in cursor.fetchall()]

    cursor.execute("""SELECT `follower` FROM `follower_followee` WHERE `followee` = %s;""", email)
    followers = [i['follower'] for i in cursor.fetchall()]

    cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", email)
    threads = [i['thread'] for i in cursor.fetchall()]

    user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    cursor.close()
    return user


def forum_details(short_name):
    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""SELECT * FROM `forums` WHERE `short_name` = %s;""", short_name)
    forum = cursor.fetchone()

    cursor.close()
    return forum


def thread_details(id):
    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""SELECT * FROM `threads` WHERE `id` = %s;""", id)
    thread = cursor.fetchone()

    if thread is None:
        cursor.close()
        return None

    thread.update({'date': str(thread['date'])})  # TODO: bad code

    cursor.close()
    return thread


def post_details(id):
    cursor = db_connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""SELECT * FROM `posts` WHERE `id` = %s;""", id)
    post = cursor.fetchone()

    if post is None:
        cursor.close()
        return None

    post.update({'date': str(post['date'])})  # TODO: bad code

    cursor.close()
    return post