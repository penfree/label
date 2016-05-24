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
STD_LAB_COLLECTION = 'bdmd_lab_standard'
LABEL_LAB_COLLECTION = 'bdmd_lab_label'

class LabUtil(object):
    def __init__(self, url):
        self.client = MongoClient(url)

    def getStdItem(self, data_file):
        collection = self.client['label'][STD_LAB_COLLECTION]
        with open(data_file, 'w') as df:
            for doc in collection.find():
                print >>df, json.dumps(doc, ensure_ascii = False)
    
    def genDict(self, data_file):
        collection = self.client['label'][LABEL_LAB_COLLECTION]
        count = 0
        item_list = {}
        for item in collection.find():
            if item.get('normal_id'):
                item_list[(item['source'], item['name'], item['sample'])] = item['normal_id']
        collection = self.client['label'][STD_LAB_COLLECTION]
        with open(data_file, 'w') as df:
            for source, name, sample in item_list:
                normal_id = item_list[(source, name, sample)]
                doc = collection.find_one({'_id' : normal_id})
                if not doc:
                    logging.warn('normal_id[%d] not found' % normal_id)
                    continue
                else:
                    obj = {
                        'source' : source,
                        'name' : name,
                        'sample' : sample,
                        'normal_name' : doc['name'],
                        'normal_sample' : doc['sample'],
                        'method' : doc['method']
                    }
                    print >>df, json.dumps(obj, ensure_ascii = False)

    def addLabelData(self, data_file, source):
        '''
            添加标注数据
            @param data_file: 输入文件, 每行一个json
                              json需要包含sample, name, freq字段, 其他字段用于帮助标注
        '''
        collection = self.client['label'][LABEL_LAB_COLLECTION]
        count = 0
        with open(data_file) as df:
            for line in df:
                obj = json.loads(line)
                if obj.get('freq') < 50:
                    continue
                data = {}
                for k in obj:
                    if isinstance(obj[k], basestring):
                        obj[k] = obj[k].strip()
                data.update(obj)
                data['source'] = source
                data['_id'] = '%s+%s+%s' % (obj['sample'], obj['name'], source)
                doc = collection.find_one({'sample' : obj['sample'], 'name' : obj['name'], 'normal_id' : {'$exists' : True}})
                if doc:
                    data['normal_id'] = doc['normal_id']
                collection.replace_one({'_id' : data['_id']}, data, upsert = True)
                count += 1
                print '\r%d' % count,
                sys.stdout.flush()

def getArguments():
    """Get arguments
    """
    parser = ArgumentParser(description = 'label platform micro service')
    parser.add_argument('--host', dest = 'host', default = 'mongo', help = 'The mongodb server')
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
        tool.genDict(args.file)
    elif args.cmd == 'getstd':
        tool.getStdItem(args.file)
