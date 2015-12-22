#!/usr/bin/env python
#coding=utf8
"""
# Author: f
# Created Time : Mon 21 Dec 2015 08:06:03 PM CST

# File Name: diagnosismanager.py
# Description:

"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class DiagnosisGroup(object):
    '''
        诊断分组,同一个组内的诊断是同义词
    '''
    def __init__(self, id, name, items):
        self.id = id
        self.name = name
        self.items = set(items)
    
    def add(self, diagnosis):
        self.items.add(diagnosis)

    def remove(self, diagnosis):
        self.items.remove(diagnosis)

    def setName(self, name):
        self.name = name

    def dump(self):
        obj = {
            '_id' : self.id,
            'diagnosis' : self.name,
            'items' : list(self.items)
        }
        return obj

class DiagnosisManager(object):
    def __init__(self):
        self.diagnosis_list = []
        self.diagnosis_groups = {}
        self.marked_diagnosis = {}
        self.max_group_id = -1
        self.diagIndex = {}

    def load(self, mongo_client):
        '''
            从mongodb加载数据
        '''
        self.diagIndex = {}
        self.diagnosis_list = []
        self.diagnosis_groups = {}
        self.marked_diagnosis = {}

        #获取待标注诊断列表
        collection = mongo_client['label']['diagnosis']
        for item in collection.find():
            self.diagnosis_list.append(item['_id'])

        collection = mongo_client['label']['diagnosis_group']
        for item in collection.find():
            group = DiagnosisGroup(item['_id'], item['diagnosis'], item['items'])
            self.diagnosis_groups[group.id] = group
            for diag in group.items:
                self.marked_diagnosis[diag] = group
            if group.id > self.max_group_id:
                self.max_group_id = group.id

    def buildIndex(self):
        '''
            按单词建索引
        '''
        for diag in self.diagnosis_list:
            for ch in diag:
                if ch not in self.diagIndex:
                    self.diagIndex[ch] = set()
                self.diagIndex[ch].add(diag)

    def mark(self, diagnosis, gid, mongo_client):
        '''
            标记诊断所属分组
            @param diagnosis: 诊断名称
            @param gid: 分组id
            @param mongo_client: mongodb client
        '''
        if not isinstance(diagnosis, unicode):
            diagnosis = diagnosis.decode('utf-8')

        try:
            #单独创建一个分组
            changed_groups = []
            if diagnosis in self.marked_diagnosis:
                marked_group = self.marked_diagnosis[diagnosis]
                marked_group.remove(diagnosis)
                changed_groups.append(marked_group)
            if gid is None:
                self.max_group_id += 1
                group = DiagnosisGroup(self.max_group_id, diagnosis, [diagnosis])
                self.diagnosis_groups[group.id] = group
                self.marked_diagnosis[diagnosis] = group
                changed_groups.append(group)
            else:
                self.diagnosis_group[gid].add(diagnosis)
                changed_groups.append(self.diagnosis_group[gid])
            self.update(changed_groups, mongo_client)
        except Exception,e:
            logging.exception(e)
            return str(e)
        return 'succ'

    def update(self, groups, mongo_client):
        for group in groups:
            mongo_client['label']['diagnosis_group'].insert_one(group.dump())

    def markGroup(self, gid, name, mongo_client):
        try:
            if gid in self.diagnosis_groups:
                group = self.diagnosis_groups[gid]
                group.name = name
                self.update([group], mongo_client)
                return 'succ'
            else:
                return 'undefined group'
        except Exception,e:
            logging.exception(e)
            return str(e)

    def getDiagnosis(self, type):
        if type == 'all':
            return {
                'labeled' : [ k for k in self.diagnosis_list if k in self.marked_diagnosis],
                'not_labeled' : [ k for k in self.diagnosis_list if k not in self.marked_diagnosis]
            }
        elif type == 'labeled':
            return {'labeled' : [ k for k in self.diagnosis_list if k in self.marked_diagnosis]}
        elif type == 'not_labeled':
            return {'not_labeled' : [ k for k in self.diagnosis_list if k not in self.marked_diagnosis]}

    def getLabelInfo(self, diagnosis):
        '''
            获取标注信息
        '''
        if not isinstance(diagnosis, unicode):
            diagnosis = diagnosis.decode('utf-8')
        rank_dict = {}
        for ch in diagnosis:
            for wd in self.diagIndex.get(ch,  []):
                if wd not in rank_dict:
                    rank_dict[wd] = 1
                else:
                    rank_dict[wd] += 1
        rank_list = sorted([(k, v) for k, v in rank_dict.iteritems()], key = lambda a:a[1], reverse = True)
        group_list = []
        for item in rank_list:
            if item[0] not in self.marked_diagnosis:
                continue
            group = self.marked_diagnosis[item[0]]
            if group not in group_list:
                group_list.append(group)
            if len(group_list) >= 20:
                break
        groups = group_list
        marked_group = self.marked_diagnosis.get(diagnosis)
        if marked_group:
            new_group = [marked_group.dump()]
            new_group[0]['marked'] = True
            for group in groups:
                if group.id == marked_group.id:
                    continue
                new_group.append(group.dump())
            groups = new_group
        else:
            groups = [ group.dump() for group in groups ]
        return groups


