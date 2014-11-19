__author__ = 'gexogen'

import os


def rel(*x):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)


def extract_params(input_dict, keys_list):
    output_dict = dict()
    for key in keys_list:
        output_dict.update({key: input_dict.get(key, None)})
    return output_dict
