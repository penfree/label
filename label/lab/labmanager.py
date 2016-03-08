#!/usr/bin/env python
#coding=utf8
"""
# Author: f
# Created Time : Tue 05 Jan 2016 08:34:10 PM CST

# File Name: labmanager.py
# Description:

"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import json
import string
import logging

class StandardItem(object):
    '''
        检验指标标准词定义
        样本+指标名称+检查方法唯一确定一个检验项目
    '''
    def __init__(self,  **kwargs):
        #样本名称
        self.sample = kwargs.get('sample')
        #指标名称
        self.name = kwargs.get('name')
        if not self.sample or not self.name:
            raise ValueError('sample and name is required')
        #检查方法
        self.method = kwargs.get('method', u'缺省')
        #单位
        self.unit = kwargs.get('unit')
        #正常范围,可以细化成高值/低值
        self.range = kwargs.get('range')
        #可选的定性描述取值
        self.qualitative_option = kwargs.get('qualitative_option')

    def getKey(self):
        key = '%s^%s^%s' % (self.sample, self.name, self.method)
        return key

    def dump(self):
        keys = ['sample', 'name', 'method', 'unit', 'range', 'qualitative_option']
        obj = {"_id" : self.getKey()}
        for key in keys:
            if self.__dict__.get(key) is not None:
                obj[key] = self.__dict__.get(key)
        return obj

class LabelItem(object):
    def __init__(self, doc):
        self._data = doc

    def setStdItem(self, sample, name, method):
        '''
            添加可归一的标准词
        '''
        if self.normal_name == name and self.method == method:
            if sample not in self.normal_sample:
                self._data['normal_sample'].append(sample)
        else:
            self._data['normal_sample'] = [sample]
            self._data['normal_name'] = name
            self._data['method'] = method

    def removeStdItem(self, sample, name, method):
        '''
            删除标准词
        '''
        if self.normal_name == name and self.method == method:
            self._data['normal_sample'].remove(sample)
            if not self._data['normal_sample']:
                del self._data['normal_name']
                del self._data['method']
        else:
            raise ValueError('normal name not matched')
        

    def dump(self):
        tmp = {}
        tmp.update(self._data)
        return tmp

    def __getattr__(self, key):
        return self._data.get(key)


class LabManager(object):
    def __init__(self):
        '''
            
        '''
        #标准词根据指标名称建立的索引
        self.item_index = {}
        #标准指标名称根据字符建立的索引
        self.char_index = {}
        #标准词列表
        self.std_item_list = {}
        #待标注列表,根据(sample, item_name)建立索引
        self.label_item_list = {}
        #样本
        self.sample_list = {}
        #标准词到已标注项的映射
        self.std_item_map = {}

    def unicode(self, s):
        if not s:
            return s
        if not isinstance(s, unicode):
            s = s.decode('utf-8')
        s = s.strip()
        return s

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
    
    def loadData(self, client):
        '''
            加载数据
        '''
        #标准词根据指标名称建立的索引
        self.item_index = {}
        #标准指标名称根据字符建立的索引
        self.char_index = {}
        #标准词列表
        self.std_item_list = {}
        #待标注列表,根据(sample, item_name)建立索引
        self.label_item_list = {}
        #样本
        self.sample_list = {}
        #标准词到已标注项的映射
        self.std_item_map = {}
        collection = client['label']['lab']
        for doc in collection.find():
            lab_item = LabelItem(doc)
            if not lab_item.sample or not lab_item.name:
                logging.error('sample and item_name is requried for items to label')
                continue
            key = (lab_item.sample, lab_item.name, lab_item.source)
            self.label_item_list[key] = lab_item
            if lab_item.normal_name and lab_item.method:
                for sample in lab_item.normal_sample:
                    key = '%s^%s^%s' % (sample, lab_item.normal_name, lab_item.method)
                    if key not in self.std_item_map:
                        self.std_item_map[key] = set()
                    self.std_item_map[key].add((lab_item.sample, lab_item.name, lab_item.source))

        collection = client['label']['std_lab']
        for doc in collection.find():
            std_item = StandardItem(**doc)
            key = std_item.getKey()
            if key not in self.std_item_map:
                self.delStdItem(std_item, client)
                continue
            self.std_item_list[key] = std_item
            if std_item.name not in self.item_index:
                self.item_index[std_item.name] = []
            self.item_index[std_item.name].append(std_item)

        for item_name in self.item_index:
            for ch in item_name:
                if ch not in self.char_index:
                    self.char_index[ch] = set()
                self.char_index[ch].add(item_name)


        collection = client['label']['lab_sample']
        for doc in collection.find():
            sample = doc['_id']
            self.sample_list[sample] = doc


    def getLabList(self, source):
        '''
            获取待标注列表,根据频次排序
        '''
        result = []
        if not source:
            result = sorted([item.dump() for item in self.label_item_list.values()], key = lambda a:a.get('freq', 0), reverse = True)
        else:
            result = sorted([item.dump() for item in self.label_item_list.values() if item.source == source], key = lambda a:a.get('freq', 0), reverse = True)
        for item in result:
            if item.get('normal_name'):
                item['marked'] = True
        return result

    def calSim(self, s1, s2):
        '''
            计算相似度
        '''
        char_s1 = set(s1)
        char_s2 = set(s2)
        inter = char_s1 & char_s2
        sim = len(inter) * 1.0 / (len(char_s1) + len(char_s2))
        return sim
        

    def getLabelInfo(self, sample, item_name, source):
        '''
            获取候选标注列表
        '''
        sample = self.unicode(sample)
        item_name = self.unicode(item_name)
        if not sample or not item_name or not source:
            raise ValueError('sample and item_name cannot be empty')
        label_item = self.label_item_list.get((sample, item_name, source))
        if not label_item:
            raise ValueError("label_item not found")

        item_count = {}
        for ch in item_name:
            if ch in self.char_index:
                for item in self.char_index[ch]:
                    if item not in item_count:
                        item_count[item] = 0
                    else:
                        item_count[item] += 1.0 / (len(item) + len(item_name))
        if label_item.normal_name:
            item_count[label_item.normal_name] = 9999999
        item_count = sorted([(k, v) for k, v in item_count.iteritems()], key = lambda a: -a[1])[:50]
        result = []
        for item, _ in item_count:
            std_item_list = self.item_index.get(item, [])
            if not std_item_list:
                logging.error('%s is not a std item' % item)
                continue
            sample_list = sorted([(std_item.sample, std_item.method, self.calSim(sample, std_item.sample)) for std_item in std_item_list], key = lambda a:-a[2])
            sample_list = [{'sample' : a[0], 'method' : a[1]} for a in sample_list]
            if label_item.normal_name == item:
                for it in sample_list:
                    if it.get('sample') in label_item.normal_sample and it.get('method') == label_item.method:
                        it['marked'] = True
            result.append({
                'name' : item,
                'info' : sample_list
            })
        result = {
            'cands' : result,
            'info' : label_item.dump()
        }

        return result

    def markLab(self, sample, item_name, source, nsample, nitem_name, method, mongo_client):
        '''
            标记标准词
        '''
        sample = self.unicode(sample)
        item_name = self.unicode(item_name)
        nsample = self.unicode(nsample)
        nitem_name = self.unicode(nitem_name)
        method = self.unicode(method)
        if not method:
            method = u'缺省'

        std_item = None
        if not nsample and not nitem_name:
            std_item = self.editStdItem(mongo_client, sample, item_name, u'缺省')
            nsample, nitem_name, method = std_item.sample, std_item.name, std_item.method
        else:
            key = '%s^%s^%s' % (nsample, nitem_name, method)
            if key not in self.std_item_list:
                std_item = self.editStdItem(mongo_client, nsample, nitem_name, method)
                nsample, nitem_name, method = std_item.sample, std_item.name, std_item.method
            else:
                std_item = self.std_item_list[key]

        if nsample and nsample not in self.sample_list:
            self.addSample(nsample, mongo_client)

        if not sample or not item_name or not nsample or not nitem_name or not method:
            raise ValueError('bad param')
        logging.info('mark %s (%s), source[%s] to %s (%s)(%s)' % (item_name, sample, source, nitem_name, nsample, method))

        key = (sample, item_name, source)
        if key not in self.label_item_list:
            raise ValueError('key not found')
        label_item = self.label_item_list[key]
        self.setStdItem(label_item, std_item)
        self.updateLabel(label_item, mongo_client)
        logging.info('parent of [%s]: %s' % (nsample, ','.join(self.sample_list[nsample].get('parent', []))))
        for item in self.sample_list[nsample].get('parent', []):
            #若父样本组成的指标存在,则也标记到父样本上
            #if item not in label_item.normal_sample and (item, nitem_name, method) in self.std_item_list:
            #同时标记到父样本上
            logging.info('label_item.normal_sample:%s' % ','.join(label_item.normal_sample))
            if item not in label_item.normal_sample:
                self.markLab(sample, item_name, source, item, nitem_name, method, mongo_client)

    def setStdItem(self, label_item, std_item):
        '''
            设置标准词
        '''
        if label_item.normal_name == std_item.name and label_item.method == std_item.method:
            self.std_item_map[std_item.getKey()].add((label_item.sample, label_item.name, label_item.source))
        elif not label_item.normal_name or not label_item.normal_sample:
            self.std_item_map[std_item.getKey()].add((label_item.sample, label_item.name, label_item.source))
        else:
            for sample in label_item.normal_sample:
                key = '%s^%s^%s' % (sample, label_item.normal_name, label_item.method)
                self.std_item_map[key].remove((label_item.sample, label_item.name, label_item.source))
            self.std_item_map[std_item.getKey()].add((label_item.sample, label_item.name, label_item.source))
        label_item.setStdItem(std_item.sample, std_item.name, std_item.method)
    
    def addSample(self, sample, mongo_client):
        '''
            添加新样本
        '''
        sample = self.unicode(sample)
        doc = {'_id' : sample, 'parent' : []}
        self.sample_list[sample] = doc
        collection = mongo_client['label']['lab_sample']
        collection.insert_one(doc)

    def mark(self, sample, item_name, source, nsample, nitem_name, method, mongo_client):
        self.markLab(sample, item_name, source, nsample, nitem_name, method, mongo_client)
        return self.getLabelInfo(sample, item_name, source)

    def updateLabel(self, label_item, mongo_client):
        '''
            将标注结果写入mongodb
        '''
        collection = mongo_client['label']['lab']
        collection.replace_one({'_id' : label_item._id}, label_item.dump(), upsert = True)

    def unmark(self, sample, item_name, source, nsample, nitem_name, method, mongo_client):
        '''
            取消标记
        '''
        sample = self.unicode(sample)
        item_name = self.unicode(item_name)
        nsample = self.unicode(nsample)
        nitem_name = self.unicode(nitem_name)
        method = self.unicode(method)

        if not sample or not item_name or not nsample or not nitem_name or not method:
            raise ValueError('bad param')
        logging.info('unmark %s (%s),   %s-%s-%s' % (item_name, sample, nsample, nitem_name, method))

        key = (sample, item_name, source)
        if key not in self.label_item_list:
            raise ValueError('key not found')
        label_item = self.label_item_list[key]
        label_item.removeStdItem(nsample, nitem_name, method)
        self.updateLabel(label_item, mongo_client)
        return self.getLabelInfo(sample, item_name, source)

    def editStdItem(self, mongo_client, sample, name, method, **kwargs):
        '''添加或编辑标准词
        '''
        sample = self.unicode(sample)
        name = self.unicode(name)
        method = self.unicode(method)
        if not method:
            method = u'缺省'
        name = self.quan2ban(name)
        key = '%s^%s^%s' % (sample, name, method)
        if key not in self.std_item_map:
            self.std_item_map[key] = set()
        if key in self.std_item_list:
            std_item = self.std_item_list[key]
            for k,v in kwargs.iteritems():
                if k in ['sample', 'name', 'method']:
                    continue
                if v:
                    setattr(std_item, k, v)
        else:
            std_item = StandardItem(sample = sample, name = name, method = method, **kwargs)
            if std_item.name not in self.item_index:
                self.item_index[std_item.name] = [std_item]
            else:
                self.item_index[std_item.name].append(std_item)
            for ch in name:
                if ch not in self.char_index:
                    self.char_index[ch] = set()
                self.char_index[ch].add(name)
            self.std_item_list[key] = std_item
        collection = mongo_client['label']['std_lab']
        collection.replace_one({'_id' : key}, std_item.dump(), upsert = True)
        return std_item

    def addSampleParent(self, sample, parent, mongo_client):
        '''
            添加上位样本
        '''
        sample = self.unicode(sample)
        parent = self.unicode(parent)
        collection = mongo_client['label']['lab_sample']
        if sample not in self.sample_list:
            self.addSample(sample, mongo_client)
        if parent not in self.sample_list[sample]['parent']:
            self.sample_list[sample]['parent'].append(parent)
            collection.update_one({'_id' : sample}, { '$addToSet': { 'parent': parent }}, upsert = True);
        return self.getSampleList()

    def removeSampleParent(self, sample, parent, mongo_client):
        '''
            移除上位样本
        '''
        sample = self.unicode(sample)
        parent = self.unicode(parent)
        collection = mongo_client['label']['lab_sample']
        if sample not in self.sample_list:
            return
        if parent in self.sample_list[sample]['parent']:
            self.sample_list[sample]['parent'].remove(parent)
            collection.replace_one({'_id' : sample}, self.sample_list[sample]['parent'], upsert = True);
        return self.getSampleList()

    def getSampleList(self):
        '''
            获取样本列表
        '''
        sample_list = [{'sample' : item['_id'], 'parent' : item['parent']} for item in self.sample_list.values()]
        revert_list = {}
        for item in sample_list:
            for parent in item['parent']:
                if parent not in revert_list:
                    revert_list[parent] = {'sample' : parent, 'children' : []}
                if item['sample'] not in revert_list[parent]['children']: revert_list[parent]['children'].append(item['sample'])
        for item in sample_list:
            item['children'] = revert_list.get(item['sample'], {}).get('children', [])
        return sample_list

    def delStdItem(self, std_item, mongo_client):
        collection = mongo_client['label']['std_lab']
        key = std_item.getKey()
        collection.delete_one({'_id' : key})

    def getStdItem(self, sample, name, method):
        '''
            获取标准词及其属性
        '''
        sample = self.unicode(sample)
        name = self.unicode(name)
        method = self.unicode(method)

        if not sample or not name or not method:
            raise ValueError('param error')

        key = '%s^%s^%s' % (sample, name, method)
        if key not in self.std_item_list:
            raise ValueError('cannot find item')

        result = {}
        result['info'] = self.std_item_list[key].dump()
        result['items'] = []
        for item in self.std_item_map.get(key, []):
            label_item = self.label_item_list[item]
            result['items'].append(label_item.dump())
        return result
