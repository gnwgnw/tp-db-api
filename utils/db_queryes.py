import MySQLdb
from settings import db_connection

__author__ = 'gexogen'


def list_following(cursor, user_id):
    cursor.execute("""SELECT `u1`.`email` FROM `users` AS `u1` IGNORE INDEX (PRIMARY)
                      INNER JOIN `follower_followee` AS `ff` ON `u1`.`id` = `ff`.`followee`
                      WHERE `ff`.`follower` = %s;""", user_id)
    following = [i['email'] for i in cursor.fetchall()]

    return following


def list_followers(cursor, user_id):
    cursor.execute("""SELECT `u1`.`email` FROM `users` AS `u1` IGNORE INDEX (PRIMARY)
                      INNER JOIN `follower_followee` AS `ff` ON `u1`.`id` = `ff`.`follower`
                      WHERE `ff`.`followee` = %s;""", user_id)
    followers = [i['email'] for i in cursor.fetchall()]

    return followers


def user_details(cursor, email):
    cursor.execute("""SELECT * FROM `users` WHERE `email` = %s;""", email)
    user = cursor.fetchone()

    if user is None:
        return None

    following = list_following(cursor, user['id'])
    followers = list_followers(cursor, user['id'])

    cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", email)
    threads = [i['thread'] for i in cursor.fetchall()]

    user.update({'following': following, 'followers': followers, 'subscriptions': threads})
    return user


def forum_details(cursor, short_name):
    cursor.execute("""SELECT * FROM `forums` WHERE `short_name` = %s;""", short_name)
    forum = cursor.fetchone()
    return forum


def thread_details(cursor, id):
    cursor.execute("""SELECT * FROM `threads` WHERE `id` = %s;""", id)
    thread = cursor.fetchone()

    if thread is None:
        return None

    thread.update({'date': str(thread['date'])})  # TODO: bad code
    return thread


def post_details(cursor, id):
    cursor.execute("""SELECT * FROM `posts` WHERE `id` = %s;""", id)
    post = cursor.fetchone()

    if post is None:
        return None

    post.update({'date': str(post['date'])})  # TODO: bad code
    return post