#!/usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'essepuntato'
import argparse
import os


class Stopper(object):
    def __init__(self, target_dir):
        self.target_dir = target_dir
        self.stop_file = target_dir + os.sep + ".stop"

    def add(self):
        if self.can_proceed():
            if not os.path.exists(self.target_dir):
                os.makedirs(self.target_dir)
            open(self.stop_file, "w").close()

    def remove(self):
        if not self.can_proceed():
            os.remove(self.stop_file)

    def can_proceed(self):
        return not os.path.exists(self.stop_file)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser("stopper.py")
    arg_parser.add_argument("-t", "--target-dir", dest="target_dir", required=True,
                            help="The configuration file to access the ORCID API.")
    arg_parser.add_argument("--add", dest="add", default=True, action="store_true",
                            help="It will add a stop marker to the target directory.")
    arg_parser.add_argument("--remove", dest="remove", default=False, action="store_true",
                            help="It will remove the block marker from the target directory.")
    args = arg_parser.parse_args()

    stopper = Stopper(args.target_dir)
    if args.remove:
        stopper.remove()
        print "Stop marker removed from to '%s'" % args.target_dir
    else:
        stopper.add()
        print "Stop marker added to '%s'" % args.target_dir
