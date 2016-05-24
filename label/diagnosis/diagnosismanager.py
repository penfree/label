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
import logging
import json
import re
import string
STD_DIAGNOSIS_COLLECTION = 'disease_standard'
LABEL_DIAGNOSIS_COLLECTION = 'disease_label'

order_pat = re.compile(ur'^\d+[\.、)）]')
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
        if diagnosis == self.name:
            if self.items:
                self.name = next(iter(self.items))
            else:
                self.name = ''
        if not self.items:
            self.name = ''

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
        self.diagnosis_list = {}
        self.diagnosis_groups = {}
        self.marked_diagnosis = {}
        self.max_group_id = -1
        self.diagIndex = {}

    def load(self, mongo_client):
        '''
            从mongodb加载数据
        '''
        self.diagIndex = {}
        self.diagnosis_list = {}
        self.diagnosis_groups = {}
        self.marked_diagnosis = {}

        #获取待标注诊断列表
        collection = mongo_client['label'][LABEL_DIAGNOSIS_COLLECTION]
        for item in collection.find():
            self.diagnosis_list[item['_id']] = item

        collection = mongo_client['label'][STD_DIAGNOSIS_COLLECTION]
        for item in collection.find():
            group = DiagnosisGroup(item['_id'], item['diagnosis'], item['items'])
            self.diagnosis_groups[group.id] = group
            for diag in group.items:
                self.marked_diagnosis[diag] = group
        print 'diagnosis_group:%d' % len(self.diagnosis_groups)
    
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
            return True
        if u'待查' in item:
            return True
        if u'查因' in item:
            return True
        if order_pat.match(item):
            return True
        return False

    def buildIndex(self):
        '''
            按单词建索引
        '''
        for diag in self.diagnosis_list:
            for ch in diag:
                if ch not in self.diagIndex:
                    self.diagIndex[ch] = set()
                self.diagIndex[ch].add(diag)
        for diag in self.marked_diagnosis:
            for ch in diag:
                if ch not in self.diagIndex:
                    self.diagIndex[ch] = set()
                self.diagIndex[ch].add(diag)


    def mark(self, diagnosis, source, gid, syn_diag, mongo_client):
        '''
            标记诊断所属分组
            @param diagnosis: 诊断名称
            @param gid: 分组id
            @param mongo_client: mongodb client
        '''
        if not isinstance(diagnosis, unicode):
            diagnosis = diagnosis.decode('utf-8')
        diagnosis = diagnosis.strip()
        logging.info('mark [%s] to group[%s], syn_diag[%s]' % (diagnosis, gid, syn_diag))
        if syn_diag:
            if not isinstance(syn_diag, unicode):
                syn_diag = syn_diag.decode('utf-8')
            syn_diag = syn_diag.strip()
            if syn_diag not in self.diagnosis_list and syn_diag not in self.marked_diagnosis:
                logging.warn('syn_diag not found')
                return "syn_diag not found"
        try:
            #单独创建一个分组
            changed_groups = []  #发生更新过的分组
            if diagnosis in self.marked_diagnosis:
                marked_group = self.marked_diagnosis[diagnosis]
                marked_group.remove(diagnosis)
                changed_groups.append(marked_group)
            if gid is not None:
                ngid = gid
                self.diagnosis_groups[ngid].add(diagnosis)
                changed_groups.append(self.diagnosis_groups[ngid])
                self.marked_diagnosis[diagnosis] = self.diagnosis_groups[ngid]
            elif syn_diag is not None:
                if syn_diag in self.marked_diagnosis:
                    group = self.marked_diagnosis[syn_diag]
                    self.marked_diagnosis[diagnosis] = group
                    group.add(diagnosis)
                    changed_groups.append(group)
                else:
                    raise ValueError("target group is not specified")
            else:
                raise ValueError('target group is not specified')
            self.update(changed_groups, mongo_client)
            mongo_client['label'][LABEL_DIAGNOSIS_COLLECTION].update_one({'_id' : diagnosis}, {'$set' : {'mark_source' : source}})
        except Exception,e:
            logging.exception(e)
            return str(e)
        return 'succ'

    def update(self, groups, mongo_client):
        for group in groups:
            if not group.items:
                mongo_client['label'][STD_DIAGNOSIS_COLLECTION].delete_one({'_id' : group.id})
                del self.diagnosis_groups[group.id]
                logging.info('delete group[%s] from mongodb' % group.id)
            else:
                mongo_client['label'][STD_DIAGNOSIS_COLLECTION].replace_one({'_id' : group.id}, group.dump(), upsert = True)
                logging.info('update group[%s] to mongodb[%s]' % (group.id, json.dumps(group.dump(), ensure_ascii = False)))

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

    def getDiagnosis(self, type, source = 'all'):
        tmp = {}
        for diag in self.diagnosis_list:
            if source != 'all' and source not in self.diagnosis_list.get(diag, {}).get('source', []):
                continue
            if self.filter(diag):
                continue
            tmp[diag] = {}
            tmp[diag].update(self.diagnosis_list[diag])
            if diag in self.marked_diagnosis:
                tmp[diag]['marked'] = True
        tmp = sorted([v for v in tmp.values()], key = lambda a: a.get('freq', 0), reverse = True)
        return tmp

    def getLabelInfo(self, diagnosis, mongo_client):
        '''
            获取标注信息
        '''
        if not isinstance(diagnosis, unicode):
            diagnosis = diagnosis.decode('utf-8')
        diagnosis = diagnosis.strip()
        tmp_diagnosis = diagnosis.replace('(未特指)', '').replace('（未特指）', '').replace('NOS', '')
        rank_dict = {}
        for ch in tmp_diagnosis:
            for wd in self.diagIndex.get(ch,  []):
                if wd not in rank_dict:
                    rank_dict[wd] = 1.0 / (len(wd) + len(tmp_diagnosis))
                else:
                    rank_dict[wd] += 1.0 / (len(wd) + len(tmp_diagnosis))
        rank_list = sorted([(k, v) for k, v in rank_dict.iteritems()], key = lambda a:a[1], reverse = True)
        group_list = []
        for item in rank_list:
            if item[0] not in self.marked_diagnosis:
                continue
            group = self.marked_diagnosis[item[0]]
            if group not in group_list:
                group_list.append(group)
            if len(group_list) >= 50:
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
        
        result = {
            'key' : diagnosis,
            'groups' : groups,
            'source' : self.diagnosis_list.get(diagnosis, {}).get('source', []),
            'marked' : diagnosis in self.marked_diagnosis
        }
        if result['marked']:
            doc = mongo_client['label'][LABEL_DIAGNOSIS_COLLECTION].find_one({'_id' : diagnosis})
            if doc and doc.get('mark_source'):
                result['mark_source'] = doc['mark_source']
        return result

    def delete(self, diagnosis, mongo_client):
        if not isinstance(diagnosis, unicode):
            diagnosis  = diagnosis.decode('utf-8')
        diagnosis = diagnosis.strip()
        changed_groups = []
        if diagnosis in self.marked_diagnosis:
            group = self.marked_diagnosis[diagnosis]
            group.remove(diagnosis)
            changed_groups.append(group)
            del self.marked_diagnosis[diagnosis]
        if diagnosis in self.diagnosis_list:
            del self.diagnosis_list[diagnosis]

            collection = mongo_client['label'][LABEL_DIAGNOSIS_COLLECTION]
            collection.delete_one({'_id' : diagnosis})
        self.update(changed_groups, mongo_client)
        return {'ret_code' : 'succ'}

