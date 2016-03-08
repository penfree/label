#!/usr/bin/env python
#coding=utf8
"""
# Author: f
# Created Time : Thu 07 Jan 2016 10:57:02 AM CST

# File Name: labutil.py
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

class LabUtil(object):
    def __init__(self, url):
        self.client = MongoClient(url)
    
    def genDict(self, data_file,source):
        collection = self.client['label']['lab']
        count = 0
        with open(data_file, 'w') as df:
            for item in collection.find({'source' : source}):
                if item.get('normal_name') and item.get('normal_sample') and item.get('method'):
                    tmp = {}
                    tmp['name'] = item['name']
                    tmp['sample'] = item['sample']
                    tmp['normal_name'] = item['normal_name']
                    tmp['normal_sample'] = item['normal_sample']
                    tmp['method'] = item['method']
                    df.write('%s\n' % json.dumps(tmp, ensure_ascii = False))
                    count += 1

        logging.info('%d item is dumped' % count)

    def genSampleDict(self, data_file):
        collection = self.client['label']['lab_sample']
        with open(data_file, 'w') as df:
            for item in collection.find():
                tmp = {'sample' : item['_id'], 'parent' : item.get('parent', [])}
                df.write('%s\n' % json.dumps(tmp, ensure_ascii = False))



    def addLabelData(self, data_file, source):
        '''
            添加标注数据
            @param data_file: 输入文件, 每行一个json
                              json需要包含sample, name, freq字段, 其他字段用于帮助标注
        '''
        collection = self.client['label']['lab']
        count = 0
        with open(data_file) as df:
            for line in df:
                obj = json.loads(line)
                data = {}
                for k in obj:
                    if isinstance(obj[k], basestring):
                        obj[k] = obj[k].strip()
                data.update(obj)
                data['source'] = source
                data['_id'] = '%s+%s+%s' % (obj['sample'], obj['name'], source)
                doc = collection.find_one({'sample' : obj['sample'], 'name' : obj['name'], 'normal_name' : {'$ne' : None}})
                if doc:
                    data['normal_name'] = doc['normal_name']
                    data['normal_sample'] = doc['normal_sample']
                    data['method'] = doc['method']
                collection.replace_one({'_id' : data['_id']}, data, upsert = True)
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
    parser.add_argument('--source', '-s', dest = 'source')
    # Done
    return parser.parse_args()

if __name__=='__main__':
    args = getArguments()
    mongo_url = 'mongodb://%s:%d' % (args.host, args.port)
    tool = LabUtil(mongo_url)

    if args.cmd == 'label':
        if not args.source:
            raise ValueError('source must be specified')
        tool.addLabelData(args.file, args.source)
    elif args.cmd == 'gendict':
        if not args.source:
            raise ValueError('source must be specified')
        tool.genDict(args.file, args.source)
    elif args.cmd == 'gensampledict':
        tool.genSampleDict(args.file)
