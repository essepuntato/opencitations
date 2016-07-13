#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'essepuntato'

import argparse
import csv
import json


def change(json_obj, key, repl, file_path, value=None):
    result = json_obj
    if key in result:
        if value is not None:
            v = result[key]
            if isinstance(v, list):
                cur_list = []
                for item in v:
                    if item == value:
                        cur_list += [repl]
                    else:
                        cur_list += [item]
                result[key] = cur_list
            elif v == value:
                result[key] = repl
        else:
            if repl not in result:
                v = result[key]
                del result[key]
                result[repl] = v
            else:
                print "WARNING: the key '%s' was already present in the file '%s'" % file_path

    for k, v in result.items():
        if isinstance(v, dict):
            result[k] = change(v, key, repl, file_path, value)
        elif isinstance(v, list):
            cur_list = []
            for item in v:
                if isinstance(item, dict):
                    cur_list += [change(item, key, repl, file_path, value)]
                else:
                    cur_list += [item]
            result[k] = cur_list

    return result

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("find.py")
    arg_parser.add_argument("-i", "--input_csv", dest="i", required=True,
                            help="The CSV containing the full paths of the file to change.")
    arg_parser.add_argument("-k", "--key", dest="k", required=True,
                            help="The keyword to replace or the key containing a value to replace "
                                 "if specified with --value.")
    arg_parser.add_argument("-v", "--value", dest="v",
                            help="The value to replace.")
    arg_parser.add_argument("-r", "--replacement", dest="r", required=True,
                            help="The new keyword.")
    args = arg_parser.parse_args()

    file_list = []
    with open(args.i) as f:
        for row in csv.reader(f):
            file_list += [row[0]]

    for file_path in file_list:
        cur_json = None
        with open(file_path, "r") as f:
            cur_json = change(json.load(f), args.k, args.r, file_path, args.v)
        if cur_json is not None:
            with open(file_path, "w") as f:
                json.dump(cur_json, f, indent=4)