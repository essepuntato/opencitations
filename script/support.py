#!/usr/bin/python
# -*- coding: utf-8 -*-
from requests.exceptions import ReadTimeout, ConnectTimeout
import json

__author__ = 'essepuntato'

import unicodedata
import re
import os
import shutil
from nltk.metrics import binary_distance as lev
from rdflib import Literal, RDF
from time import sleep
import requests
from urllib import quote
import sys


def encode_url(u):
    return quote(u, "://")


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


def normalise_id(id_string):
    return re.sub("[^A-Za-z0-9#]", "_", normalise_ascii(id_string).replace("/", "#").lower())


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


def get_data(max_iteration, sec_to_wait, get_url, headers, timeout, repok, reper, is_json=True):
    tentative = 0
    error_no_200 = False
    error_read = False
    error_connection = False
    error_generic = False
    errors = []
    while tentative < max_iteration:
        if tentative != 0:
            sleep(sec_to_wait)
        tentative += 1

        try:
            response = requests.get(get_url, headers=headers, timeout=timeout)
            if response.status_code == 200:
                repok.add_sentence("Data retrieved from '%s'." % get_url)
                if is_json:
                    return json.loads(response.text)
                else:
                    return response.text
            else:
                err_string = "We got an HTTP error when retrieving data (HTTP status code: %s)." % \
                             str(response.status_code)
                if not error_no_200:
                    error_no_200 = True
                if response.status_code == 404:
                    repok.add_sentence(err_string + " However, the process could continue anyway.")
                    # If the resource has not found, we can break the process immediately,
                    # by returning None so as to allow the callee to continue (or not) the process
                    return None
                else:
                    errors += [err_string]
        except ReadTimeout as e:
            if not error_read:
                error_read = True
                errors += ["A timeout error happened when reading results from the API "
                           "when retrieving data. %s" % e]
        except ConnectTimeout as e:
            if not error_connection:
                error_connection = True
                errors += ["A timeout error happened when connecting to the API "
                           "when retrieving data. %s" % e]
        except Exception as e:
            if not error_generic:
                error_generic = True
                errors += ["A generic error happened when trying to use the API "
                           "when retrieving data. %s" % sys.exc_info()[0]]

    # If the process comes here, no valid result has been returned
    reper.add_sentence(" | ".join(errors) + "\n\tRequested URL: " + get_url)
