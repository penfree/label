#!/usr/bin/env python
#coding=utf8
"""
# Author: f
# Created Time : Tue 22 Dec 2015 01:11:19 PM CST

# File Name: diagutil.py
# Description:

"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from pymongo import MongoClient
from argparse import ArgumentParser
import json
import string
import logging

class DiagUtil(object):
    def __init__(self, url):
        self.client = MongoClient(url)

    def genDict(self, dict_path):
        with open(dict_path, 'w') as df:
            collection = self.client['label']['diagnosis_group']
            for doc in collection.find():
                for item in doc['items']:
                    if item == doc['diagnosis']:
                        continue
                    df.write('%s\t%s\n' % (item, doc['diagnosis']))

    def init(self, group_file):
        gid = 0
        with open(group_file) as df:
            collection = self.client['label']['diagnosis_group']
            for line in df:
                obj = json.loads(line)
                obj['_id'] = gid
                collection.replace_one({'_id' : gid}, obj, upsert = True)
                gid += 1

    def addLabelData(self, data_file):
        collection = self.client['label']['diagnosis']
        with open(data_file) as df:
            for line in df:
                words = line.strip().split('\t')
                diagnosis = words[0]
                if len(words) > 1:
                    count = string.atoi(words[1])
                    if count < 30:
                        continue
                obj = {'_id' : diagnosis}
                try:
                    collection.insert_one(obj)
                except:
                    continue


def getArguments():
    """Get arguments
    """
    parser = ArgumentParser(description = 'label platform micro service')
    parser.add_argument('--host', dest = 'host', default = 'mongo0.dev-bdmd.com', help = 'The mongodb server')
    parser.add_argument('--port', dest = 'port', type = int, default = 27015, help = 'The mongodb port')
    parser.add_argument('--file', '-f', dest = 'file', required = True, help = '')
    parser.add_argument('--cmd', '-c', dest = 'cmd',required = True)
    # Done
    return parser.parse_args()

if __name__=='__main__':
    args = getArguments()
    mongo_url = 'mongodb://%s:%d' % (args.host, args.port)
    tool = DiagUtil(mongo_url)

    if args.cmd == 'init':
        tool.init(args.file)
    elif args.cmd == 'label':
        tool.addLabelData(args.file)
    elif args.cmd == 'gen_dict':
        tool.genDict(args.file)
