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
STD_DIAGNOSIS_COLLECTION = 'disease_standard'
LABEL_DIAGNOSIS_COLLECTION = 'disease_label'
order_pat = re.compile(ur'^\d+[\.、)）]')

class DiagUtil(object):
    def __init__(self, url):
        self.client = MongoClient(url)
    
    def quan2ban(self, ustr):
        if not isinstance(ustr, unicode):
            ustr = unicode(ustr)

        rst = ''
        for ch in ustr:
            code = ord(ch)
            if 0xFF01 <= code <= 0xFF5E :
                code -= 0xFEE0
            elif code == 0x3000: # 空格
                code = 0x20
            rst += unichr(code)
        return rst 

    def filter(self, item):
        if item[0] == item[-1] and item[0] == '"':
            item = item[1:-1].strip().replace('\t', ' ')
        item = self.quan2ban(item)
        if '?' in item:
            return None
        if u'待查' in item:
            return None
        if u'查因' in item:
            return None
        if order_pat.match(item):
            return None
        return item.strip()

    def getStd(self, dict_path):
        with open(dict_path, 'w') as df:
            collection = self.client['label'][STD_DIAGNOSIS_COLLECTION]
            for doc in collection.find():
                df.write('%s\t%s\n' % (doc['_id'], doc['diagnosis']))

    def genDict(self, dict_path):
        with open(dict_path, 'w') as df:
            collection = self.client['label'][STD_DIAGNOSIS_COLLECTION]
            for doc in collection.find():
                for item in doc['items']:
                    if item == doc['diagnosis']:
                        continue
                    item = self.filter(item)
                    if not item:
                        continue
                    df.write('%s\t%s\n' % (item, doc['_id']))
                df.write('%s\t%s\n' % (doc['diagnosis'], doc['_id']))

    def init(self, group_file):
        gid = 0
        with open(group_file) as df:
            collection = self.client['label'][STD_DIAGNOSIS_COLLECTION]
            for line in df:
                obj = json.loads(line)
                collection.replace_one({'_id' : obj['_id']}, obj, upsert = True)

    def addLabelData(self, data_file, source):
        '''
            添加待标注数据
            @param data_file: 输入文件, 格式是"诊断名\t频次", 频次可省
            @param source: 来源医院
        '''
        collection = self.client['label'][LABEL_DIAGNOSIS_COLLECTION]
        with open(data_file) as df:
            for line in df:
                words = line.strip().split('\t')
                diagnosis = words[0].strip()
                diagnosis = self.filter(diagnosis)
                if not diagnosis:
                    continue
                if len(words) > 2:
                    continue
                if len(words) > 1:
                    count = string.atoi(words[1])
                    if count < 30:
                        continue
                obj = {'_id' : diagnosis}
                collection.update_one( { '_id': diagnosis }, { '$addToSet': { 'source': source }, '$inc' : {'freq' : count}}, upsert = True); 


def getArguments():
    """Get arguments
    """
    parser = ArgumentParser(description = 'label platform micro service')
    parser.add_argument('--host', dest = 'host', default = 'mongo', help = 'The mongodb server')
    parser.add_argument('--port', dest = 'port', type = int, default = 27017, help = 'The mongodb port')
    parser.add_argument('--file', '-f', dest = 'file', required = True, help = '')
    parser.add_argument('--cmd', '-c', dest = 'cmd',required = True, help = 'init|label|gen_dict')
    parser.add_argument('--source', '-s', dest = 'source')
    # Done
    return parser.parse_args()

if __name__=='__main__':
    args = getArguments()
    mongo_url = 'mongodb://%s:%d' % (args.host, args.port)
    tool = DiagUtil(mongo_url)

    if args.cmd == 'init':
        tool.init(args.file)
    elif args.cmd == 'label':
        if not args.source:
            raise ValueError('source must be specified')
        tool.addLabelData(args.file, args.source)
    elif args.cmd == 'gendict':
        tool.genDict(args.file)
    elif args.cmd == 'getstd':
        tool.getStd(args.file)
