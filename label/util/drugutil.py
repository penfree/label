#!/usr/bin/env python
#coding=utf8
"""
# Author: f
# Created Time : Wed 30 Dec 2015 02:29:07 PM CST

# File Name: drugutil.py
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

class DrugUtil(object):
    def __init__(self, url):
        self.client = MongoClient(url)
    
    def genDict(self, data_file,source):
        collection = self.client['label']['drug']
        with open(data_file, 'w') as df:
            for item in collection.find({'source' : source}):
                if item.get('cname'):
                    tmp = {}
                    tmp.update(item)
                    del tmp['data']
                    df.write('%s\n' % json.dumps(tmp, ensure_ascii = False))


    def addLabelData(self, data_file, source, key_field = 'drug_code'):
        '''
            添加标注数据
            @param data_file: 输入文件, 每行一个json, 需要有一个主键字段通过key_field指定
                              json需要包含drug_name, frequency两个字段,frequency 小于100的直接过滤
        '''
        collection = self.client['label']['drug']
        count = 0
        with open(data_file) as df:
            for line in df:
                obj = json.loads(line)
                data = {}
                data['frequency'] = obj.get('frequency', 0)
                if data['frequency'] < 100:
                    continue
                data['code'] = obj[key_field]
                data['drug_name'] = obj['drug_name']
                data['source'] = source
                data['data'] = obj
                data['_id'] = '%s+%s' % ( obj[key_field], source)
                collection.replace_one({'code' : obj[key_field], 'source' : source}, data, upsert = True)
                count += 1
                print '\r%d' % count,
                sys.stdout.flush()

def getArguments():
    """Get arguments
    """
    parser = ArgumentParser(description = 'label platform micro service')
    parser.add_argument('--host', dest = 'host', default = 'storage0.jd-bdmd.com', help = 'The mongodb server')
    parser.add_argument('--port', dest = 'port', type = int, default = 27017, help = 'The mongodb port')
    parser.add_argument('--file', '-f', dest = 'file', required = True, help = '')
    parser.add_argument('--cmd', '-c', dest = 'cmd',required = True)
    parser.add_argument('--key', dest = 'key_field', default = 'drug_code')
    parser.add_argument('--source', '-s', dest = 'source')
    # Done
    return parser.parse_args()

if __name__=='__main__':
    args = getArguments()
    mongo_url = 'mongodb://%s:%d' % (args.host, args.port)
    tool = DrugUtil(mongo_url)

    if args.cmd == 'label':
        if not args.source:
            raise ValueError('source must be specified')
        tool.addLabelData(args.file, args.source, args.key_field)
    elif args.cmd == 'gen_dict':
        if not args.source:
            raise ValueError('source must be specified')
        tool.genDict(args.file, args.source)
