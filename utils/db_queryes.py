from flask import g

__author__ = 'gexogen'


def user_details(email):
    g.cursor.execute("""SELECT * FROM `users` WHERE `email` = %s;""", email)
    user = g.cursor.fetchone()

    g.cursor.execute("""SELECT `followee` FROM `follower_followee` WHERE `follower` = %s;""", email)
    following = [i['followee'] for i in g.cursor.fetchall()]

    g.cursor.execute("""SELECT `follower` FROM `follower_followee` WHERE `followee` = %s;""", email)
    followers = [i['follower'] for i in g.cursor.fetchall()]

    g.cursor.execute("""SELECT `thread` FROM `users_threads` WHERE `user` = %s;""", email)
    threads = [i['thread'] for i in g.cursor.fetchall()]

    user.update({'following': following, 'followers': followers, 'subscriptions': threads})

    return user


def forum_details(short_name):
    g.cursor.execute("""SELECT * FROM `forums` WHERE `short_name` = %s;""", short_name)
    forum = g.cursor.fetchone()

    return forum


def thread_details(id):
    g.cursor.execute("""SELECT * FROM `threads` WHERE `id` = %s;""", id)
    thread = g.cursor.fetchone()

    thread.update({'date': str(thread['date'])})  # TODO: bad code

    return thread


def post_details(id):
    g.cursor.execute("""SELECT * FROM `posts` WHERE `id` = %s;""", id)
    post = g.cursor.fetchone()

    post.update({'date': str(post['date'])})  # TODO: bad code

    return post