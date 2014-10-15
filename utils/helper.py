__author__ = 'gexogen'

import os


def rel(*x):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)