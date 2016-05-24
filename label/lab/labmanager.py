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
STD_LAB_COLLECTION = 'bdmd_lab_standard'
LABEL_LAB_COLLECTION = 'bdmd_lab_label'

class StandardItem(object):
    '''
        检验指标标准词定义
        样本+指标名称+检查方法唯一确定一个检验项目
    '''
    def __init__(self,  **kwargs):
        #_id
        self._id = kwargs['_id']
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
        #一级分类
        self.class1 = kwargs.get('class1')
        #二级分类
        self.class2 = kwargs.get('class2')
        #英文名称
        self.english_name = kwargs.get('english_name')
        self.item_sets = kwargs.get('item_sets')

    def dump(self):
        obj = {}
        keys = ['_id', 'sample', 'name', 'method', 'unit', 'range', 'qualitative_option', 'class1', 'class2', 'english_name', 'item_sets']
        for key in keys:
            if self.__dict__.get(key) is not None:
                obj[key] = self.__dict__.get(key)
        return obj

class LabelItem(object):
    def __init__(self, doc):
        self._data = doc

    def setStdItem(self, normal_item):
        self._data['normal_id'] = normal_item._id

    def removeStdItem(self):
        '''
            删除标准词
        '''
        del self._data['normal_id']

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
        self.max_lab_id = -1

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

    def addStdItem(self, std_item):
        """
            @Brief addStdItem 添加标准词到内存索引
            @Param std_item:
        """
        if  std_item._id > self.max_lab_id:
            self.max_lab_id = std_item._id
        self.std_item_list[std_item._id] = std_item
        if std_item.name not in self.item_index:
            self.item_index[std_item.name] = []
            for ch in std_item.name:
                if ch not in self.char_index:
                    self.char_index[ch] = set()
                self.char_index[ch].add(std_item.name)
        self.item_index[std_item.name].append(std_item)
        self.std_item_map[std_item._id] = set()

    def newStdItem(self, mongo_client, sample, name, method = u'缺省', **kwargs):
        """
            @Brief newStdItem 创建新的标准词
            @Param mongo_client:
            @Param sample: 样本名称
            @Param name: 指标名称
        """
        self.max_lab_id += 1
        std_item = StandardItem(_id = self.max_lab_id, sample = sample, name = name, method = method, **kwargs)
        self.addStdItem(std_item)

        collection = mongo_client['label'][STD_LAB_COLLECTION]
        collection.replace_one({'_id' : std_item._id}, std_item.dump(), upsert = True)
        return std_item

    def findStdItem(self, sample, name, method = u'缺省'):
        """
            @Brief findStdItem 查找标准词
            @Param sample:
            @Param name:
            @Param method:
        """
        if name in self.item_index:
            for item in self.item_index.get(name):
                if item.sample == sample and item.method == method:
                    return item
        return None
    
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
        collection = client['label'][STD_LAB_COLLECTION]
        for doc in collection.find():
            std_item = StandardItem(**doc)
            self.addStdItem(std_item)
        collection = client['label'][LABEL_LAB_COLLECTION]
        for doc in collection.find():
            lab_item = LabelItem(doc)
            if not lab_item.sample or not lab_item.name:
                logging.error('sample and item_name is requried for items to label')
                continue
            key = (lab_item.sample, lab_item.name, lab_item.source)
            self.label_item_list[key] = lab_item
            if lab_item.normal_id is not None:
                self.std_item_map[lab_item.normal_id].add((lab_item.sample, lab_item.name, lab_item.source))

    def getLabList(self, source):
        '''
            获取待标注列表,根据频次排序
        '''
        result = []
        if not source:
            result = sorted([item.dump() for item in self.label_item_list.values() if not item.freq or item.freq > 50], key = lambda a:a.get('freq', 0), reverse = True)
        else:
            result = sorted([item.dump() for item in self.label_item_list.values() if item.source == source and (not item.freq or item.freq > 50) ], key = lambda a:a.get('freq', 0), reverse = True)
        for item in result:
            if item.get('normal_id') is not None:
                item['marked'] = True
            if len(item.get('item_sets', [])) > 10:
                item['item_sets'] = item['item_sets'][:10]
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
            if ch == '(' or ch == ')':
                continue
            if ch in self.char_index:
                for item in self.char_index[ch]:
                    if item not in item_count:
                        item_count[item] = 0
                    if ord(ch) > 0xff:
                        item_count[item] += 2.0 / (len(item) + len(item_name))
                    else:
                        item_count[item] += 1.0 / (len(item) + len(item_name))
        if label_item.normal_id is not None:
            item_count[self.std_item_list[label_item.normal_id].name] = 9999999
        item_count = sorted([(k, v) for k, v in item_count.iteritems()], key = lambda a: -a[1])[:50]
        result = []
        for item, _ in item_count:
            std_item_list = self.item_index.get(item, [])
            if not std_item_list:
                logging.error('%s is not a std item' % item)
                continue
            sample_list = sorted([(std_item.sample, std_item.method, self.calSim(sample, std_item.sample)) for std_item in std_item_list], key = lambda a:-a[2])
            sample_list = [{'sample' : a[0], 'method' : a[1]} for a in sample_list]
            if label_item.normal_id is not None:
                normal_item = self.std_item_list[label_item.normal_id]
                if normal_item.name == item:
                    for it in sample_list:
                        if it.get('sample') == normal_item.sample and it.get('method') == normal_item.method:
                            it['marked'] = True
            result.append({
                'name' : item,
                'info' : sample_list
            })
        result = {
            'cands' : result,
            'info' : label_item.dump()
        }
        if len(result['info'].get('item_sets', [])) > 10:
            result['info']['item_sets'] = sorted(result['info']['item_sets'], key = lambda a: -a[1] if a  and isinstance(a, tuple) else 0)[:20]

        return result

    def markLab(self, sample, item_name, source, nid, nsample, nitem_name, method, mongo_client):
        '''
            标记标准词
        '''
        nsample = self.unicode(nsample)
        nitem_name = self.unicode(nitem_name)
        method = self.unicode(method)
        if isinstance(nid, basestring):
            nid = string.atoi(nid)
        if not method:
            method = u'缺省'

        std_item = None
        #未指定标准词时创建标准词
        if nid is not None:
            std_item = self.std_item_list[nid]
        elif not nsample and not nitem_name:
            std_item = self.newStdItem(mongo_client, sample, item_name, u'缺省')
            nsample, nitem_name, method = std_item.sample, std_item.name, std_item.method
        else:
            #指定的标准词不存在时创建标准词
            std_item = self.findStdItem(nsample, nitem_name, method)
            if not std_item:
                std_item = self.newStdItem(mongo_client, nsample, nitem_name, method)
        if not sample or not item_name:
            raise ValueError('bad param')
        logging.info('mark %s (%s), source[%s] to %s (%s)(%s)' % (item_name, sample, source, std_item.name, std_item.sample, std_item.method))

        key = (sample, item_name, source)
        if key not in self.label_item_list:
            raise ValueError('key not found')
        label_item = self.label_item_list[key]
        self.setStdItem(label_item, std_item)
        self.updateLabel(label_item, mongo_client)

    def setStdItem(self, label_item, std_item):
        '''
            设置标准词
        '''
        if label_item.normal_id is None or label_item.normal_id == std_item._id:
            self.std_item_map[std_item._id].add((label_item.sample, label_item.name, label_item.source))
        else:
            self.std_item_map[label_item.normal_id].remove((label_item.sample, label_item.name, label_item.source))
            self.std_item_map[std_item._id].add((label_item.sample, label_item.name, label_item.source))
        label_item.setStdItem(std_item)
    
    def mark(self, sample, item_name, source, nid, nsample, nitem_name, method, mongo_client):
        self.markLab(sample, item_name, source, nid, nsample, nitem_name, method, mongo_client)
        return self.getLabelInfo(sample, item_name, source)

    def updateLabel(self, label_item, mongo_client):
        '''
            将标注结果写入mongodb
        '''
        collection = mongo_client['label'][LABEL_LAB_COLLECTION]
        collection.replace_one({'_id' : label_item._id}, label_item.dump(), upsert = True)

    def unmark(self, sample, item_name, source, nsample, nitem_name, method, mongo_client):
        '''
            取消标记
        '''
        if not sample or not item_name:
            raise ValueError('bad param')
        logging.info('unmark %s (%s),   %s-%s-%s' % (item_name, sample, nsample, nitem_name, method))

        key = (sample, item_name, source)
        if key not in self.label_item_list:
            raise ValueError('key not found')
        label_item = self.label_item_list[key]
        if label_item.normal_id is not None:
            self.std_item_map[label_item.normal_id].remove((label_item.sample, label_item.name, label_item.source))
        
        label_item.removeStdItem()
        self.updateLabel(label_item, mongo_client)
        return self.getLabelInfo(sample, item_name, source)

    def editStdItem(self, mongo_client, **kwargs):
        '''添加或编辑标准词
        '''
        if '_id' in kwargs:
            nid = kwargs['_id']
            if isinstance(nid, basestring):
                nid = string.atoi(nid)
        else:
            nid = None
        params = {}
        params.update(kwargs)
        if 'name' in params: params['name'] = self.quan2ban(params['name'])
        if nid is not None:
            std_item = self.std_item_list[nid]
        elif params.get('sample') and params.get('name'):
            std_item = self.findStdItem(params.get('sample'), params.get('name'),params.get('method', u'缺省'))
            if not std_item:
                std_item = self.newStdItem(mongo_client, params.get('sample'), 
                                params.get('name'), params.get('method', u'缺省'), **kwargs)
        else:
            raise ValueError('cannot find match item')
        name_changed = False
        if std_item:
            for k,v in kwargs.iteritems():
                if k == '_id':
                    continue
                if k == 'name' and v != std_item.name and nid is not None:
                    name_changed = True
                if v:
                    setattr(std_item, k, v)
        collection = mongo_client['label'][STD_LAB_COLLECTION]
        collection.replace_one({'_id' : std_item._id}, std_item.dump(), upsert = True)
        if name_changed:
            self.loadData(mongo_client)
        return std_item


    def delStdItem(self, id, mongo_client):
        """
            @Brief delStdItem 删除标准词
            @Param id:
            @Param mongo_client:
        """
        collection = mongo_client['label'][LABEL_LAB_COLLECTION]
        doc = collection.find_one({'normal_id' : id})
        if doc:
            raise ValueError('%s marked to this std item' % json.dumps(doc, ensure_ascii = False))
        collection = mongo_client['label'][STD_LAB_COLLECTION]
        collection.delete_one({'_id' : id})
        self.loadData(mongo_client)

    def getStdItem(self, sample, name, method, id = None):
        '''
            获取标准词及其属性
        '''
        if id is not None:
            std_item = self.std_item_list[id]
        elif not sample or not name or not method:
            raise ValueError('param error')
        else:
            std_item = self.findStdItem(sample, name, method)

        result = {}
        result['info'] = std_item.dump()
        result['items'] = []
        for item in self.std_item_map.get(std_item._id, []):
            label_item = self.label_item_list[item]
            obj = label_item.dump()
            obj['item_sets'] = sorted(obj['item_sets'], key = lambda a: -a[1] if a and isinstance(a, tuple) else 0)[:20]
            result['items'].append(obj)
        return result

    def getStdItemList(self, mongo_client):
        """
            @Brief getStdItemList 获取标准词列表
            @Param mongo_client:
        """
        result = []
        for id, item in self.std_item_list.iteritems():
            tmp = item.dump()
            tmp['marked'] = True if self.std_item_map.get(id) else False
            result.append(tmp)
        return result
