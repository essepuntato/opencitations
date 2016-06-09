#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'essepuntato'

import unicodedata
import re
import os
import shutil
from nltk.metrics import binary_distance as lev
from rdflib import Literal, RDF


def dict_get(d, key_list):
    if key_list:
        if type(d) is dict:
            k = key_list[0]
            if k in d:
                return dict_get(d[k], key_list[1:])
            else:
                return None
        elif type(d) is list:
            result = []
            for item in d:
                value = [dict_get(item, key_list)]
                if value is not None:
                    result += value
            return result
        else:
            return None
    else:
        return d


def dict_add(d):
    result = {}
    for k in d:
        value = d[k]
        if value is not None:
            result[k] = value
    return result


def normalise_ascii(string):
    return unicodedata.normalize('NFKD', string).encode("ASCII", "ignore")


def normalise_name(name):
    return re.sub("[^A-Za-z ]", "", normalise_ascii(name).lower())


def dict_list_get_by_value_ascii(l, k, v):
    result = []
    v_ascii = normalise_name(v)

    for item in l:
        if type(item) is dict and k in item:
            cur_v = item[k]
            if (type(cur_v) is str or type(cur_v) is unicode) and normalise_name(cur_v) == v_ascii:
                result += [item]

    return result


def list_from_idx(l, idx_l):
    result = []

    for idx in idx_l:
        result += [l[idx]]

    return result


def string_list_close_match(ls, m):
    final_result = []

    tmp_result = []
    m_ascii = normalise_name(m)
    f_letter = m_ascii[:1]
    for idx, s in enumerate(ls):
        if normalise_name(s)[:1] == f_letter:
            tmp_result += [idx]

    if tmp_result == 1:
        final_result = tmp_result
    elif tmp_result > 1:
        cur_lev = 10000000
        for idx in tmp_result:
            s = ls[idx]
            s_lev = lev(normalise_name(s), m_ascii)
            if s_lev <= cur_lev:
                if s_lev < cur_lev:
                    final_result = []
                final_result += [idx]
                cur_lev = s_lev

    return final_result


def move_file(src, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)
    shutil.move(src, dst)
    return dst + os.sep + os.path.basename(src)


def create_literal(g, res, p, s, dt=None):
    if isinstance(s, basestring):
        string = s
    else:
        string = str(s)
    if not is_string_empty(string):
        g.add((res, p, Literal(string, datatype=dt)))
        return True
    return False


def create_type(g, res, res_type):
    g.add((res, RDF.type, res_type))


def is_string_empty(string):
    return string is None or string.strip() == ""


def get_short_name(res):
    return re.sub("^.+/([a-z][a-z])(/[0-9]+)?$", "\\1", str(res))


def get_count(res):
    return re.sub("^.+/[a-z][a-z]/([0-9]+)$", "\\1", str(res))
