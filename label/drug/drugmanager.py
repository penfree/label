#!/usr/bin/env python
#coding=utf8
"""
# Author: f
# Created Time : Tue 29 Dec 2015 05:05:34 PM CST

# File Name: drugmanager.py
# Description:

"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import logging
from unifiedrpc.errors import BadRequestError, NotFoundError

class DrugInfo(object):
    def __init__(self, obj):
        self.cnname = obj.get('cnname')
        self.cname = obj.get('commonname')
        self.pname = obj.get('showname')

    def dump(self):
        return {
            'cnname' : self.cnname,
            'cname' : self.cname,
            'pname' : self.pname
        }

    def __eq__(self, obj):
        return self.cnname == obj.cnname and self.cname == obj.cname and self.pname == obj.pname

    def __hash(self):
        return hash('%s+%s+%s' % (self.cname, self.cnname, self.pname))

    def __ne__(self, obj):
        return not self.__eq__(obj)

def addIndex(index, key, item):
    if key not in index:
        index[key] = []
    index[key].append(item)

class DrugManager(object):
    def __init__(self):
        self.wiki_drug_list = set()
        self.wiki_id_index = {}
        self.wiki_cname_index = {}
        self.wiki_pname_index = {}
        self.wiki_cnname_index = {}
        self.drug_list = {}
        self.cname_index = {}
        self.pname_index = {}
        self.cnname_index = {}

    def unicode(self, s):
        if not s:
            return s
        if not isinstance(s, unicode):
            s = s.decode('utf-8')
        return s.strip()

    def loadData(self, mongo_client):
        #加载标准药品列表
        collection = mongo_client['wiki']['drug']
        for item in collection.find(projection = ['_id', 'commonname', 'showname', 'cnname']):
            drug = DrugInfo(item)
            self.wiki_drug_list.add(drug)
        logging.warn('wiki_drug_list:%d' % len(self.wiki_drug_list))

        for drug in self.wiki_drug_list:
            if drug.cnname:
                addIndex(self.wiki_cnname_index, drug.cnname, drug)
            if drug.cname:
                addIndex(self.wiki_cname_index, drug.cname, drug)
            if drug.pname:
                addIndex(self.wiki_pname_index, drug.pname, drug)
        logging.warn('wiki_pname_index:%d, wiki_cname_index:%d' % (len(self.wiki_pname_index), len(self.wiki_cname_index)))

        #加载待标注列表
        collection = mongo_client['label']['drug']
        for item in collection.find():
            code = item.get('code')
            source = item.get('source')
            self.drug_list[(code, source)] = item

        #中文名索引
        for key in self.wiki_cnname_index:
            for ch in key:
                if ch not in self.cnname_index:
                    self.cnname_index[ch] = set()
                self.cnname_index[ch].add(key)
        
        #商品名索引
        for key in self.wiki_pname_index:
            for ch in key:
                if ch not in self.pname_index:
                    self.pname_index[ch] = set()
                self.pname_index[ch].add(key)
        
        #通用名索引
        for key in self.wiki_cname_index:
            for ch in key:
                if ch not in self.cname_index:
                    self.cname_index[ch] = set()
                self.cname_index[ch].add(key)

        self.preMark(mongo_client)

    def preMark(self, mongo_client):
        '''
            对于药品名称是已知通用名的,直接标记上
        '''
        for item in self.drug_list.values():
            if item.get('cname'):
                continue
            if item['drug_name'] in self.wiki_cname_index:
                try:
                    self.mark(item['code'], item['source'], item['drug_name'], None, mongo_client, return_label_info = False)
                except Exception,e:
                    logging.exception(e)

    def getDrugList(self, source):
        result = []
        if not source:
            result = [item for item in  self.drug_list.value() ]
        else:
            result = [item for item in self.drug_list.values() if item.get('source') == source]
        result.sort(key = lambda a: -a.get('frequency', 0))
        return result

    def getLabelInfo(self, key, source):
        if not key or not source:
            raise NotFoundError

        if key and not isinstance(key, unicode):
            key = key.decode('utf-8')
        key = key.strip()
        label_drug = self.drug_list.get((key, source))
        if not label_drug:
            raise NotFoundError()

        drug_name = label_drug.get('drug_name', '')
        cname_count = {}
        cnname_count = {}
        pname_count = {}
        char_ratio = {u'药' : 0.2, u'片' : 0.2, u'液' : 0.2, u'注' : 0.2, u'射' : 0.2, u'剂' : 0.2, u'针' : 0.2}
        for ch in drug_name:
            ratio = char_ratio.get(ch, 1)
            if ch in self.cname_index:
                for item in self.cname_index[ch]:
                    if item not in cname_count:
                        cname_count[item] = 0
                    cname_count[item] += 1.0 / (len(drug_name) + len(item)) * ratio
            if ch in self.cnname_index:
                for item in self.cnname_index[ch]:
                    if item not in cnname_count:
                        cnname_count[item] = 0
                    cnname_count[item] += 1.0 / (len(drug_name) + len(item)) * ratio
            if ch in self.pname_index:
                for item in self.pname_index[ch]:
                    if item not in pname_count:
                        pname_count[item] = 0
                    pname_count[item] += 1.0 / (len(drug_name) + len(item)) * ratio

        logging.warn('cname_count:%d, pname_count:%d' % (len(cname_count), len(pname_count)))

        final_cname_count = {}
        final_pname_count = {}
        for item in self.wiki_drug_list:
            if item.cname:
                if item.cname not in final_cname_count:
                    final_cname_count[item.cname] = 0
                final_cname_count[item.cname] = max(cname_count.get(item.cname, 0), final_cname_count[item.cname])
                if item.cnname:
                    final_cname_count[item.cname] = max(cnname_count.get(item.cnname, 0), final_cname_count[item.cname])
                if item.pname:
                    final_cname_count[item.cname] = max(pname_count.get(item.pname, 0), final_cname_count[item.cname])
            if item.pname:
                if item.pname not in final_pname_count:
                    final_pname_count[item.pname] = 0
                final_pname_count[item.pname] = max(pname_count.get(item.pname, 0), final_pname_count[item.pname])
                if item.cnname:
                    final_pname_count[item.pname] = max(cnname_count.get(item.cnname, 0), final_pname_count[item.pname])
                if item.cname:
                    final_pname_count[item.pname] = max(cname_count.get(item.cname, 0), final_pname_count[item.pname])
        final_cname_count = sorted([(k, v) for k, v in final_cname_count.iteritems()], key = lambda a : -a[1])
        final_pname_count = sorted([(k, v) for k, v in final_pname_count.iteritems()], key = lambda a : -a[1])
        
        logging.warn('cname_count:%d, pname_count:%d' % (len(final_cname_count), len(final_pname_count)))
        
        marked_cname = label_drug.get('cname')
        marked_pname = label_drug.get('pname')
        result = {'cname_cand' : [], 'pname_cand' : []}
        #通用名候选
        if marked_cname:
            tmp = {'name' : marked_cname, 'info' : []}
            for item in self.wiki_cname_index.get(marked_cname, []):
                tmp['info'].append(item.dump())
            result['cname_cand'].append(tmp)

        for cname, _ in final_cname_count:
            if cname == marked_cname:
                continue
            tmp = {'name' : cname, 'info' : []}
            for item in self.wiki_cname_index.get(cname, []):
                tmp['info'].append(item.dump())
            result['cname_cand'].append(tmp)
            if len(result['cname_cand']) > 50:
                break
            
        #商品名候选
        if marked_pname:
            tmp = {'name' : marked_pname, 'info' : []}
            for item in self.wiki_pname_index.get(marked_pname, []):
                tmp['info'].append(item.dump())
            result['pname_cand'].append(tmp)

        for pname, _ in final_pname_count:
            if pname == marked_pname:
                continue
            tmp = {'name' : pname, 'info' : []}
            for item in self.wiki_pname_index.get(pname, []):
                tmp['info'].append(item.dump())
            result['pname_cand'].append(tmp)
            if len(result['pname_cand']) > 50:
                break
        
        result['label_drug'] = label_drug
        return result

    def getWikiList(self, cname, pname, mongo_client):
        collection = mongo_client['wiki']['drug']
        query = {}
        if cname:
            query['commonname'] = cname
        if pname:
            query['showname'] = pname
        if not query:
            raise NotFoundError
        result = []
        for doc in collection.find(query):
            result.append(doc)
        return result

    def getWiki(self, key, pname, mongo_client):
        key_map = { 
            "companyname": u"生产企业", 
            "component": u"成份",     
            "indication": u"适应症",  
            "dosage": u"用法用量",    
            "administration": u"服药与进食", 
            "druginteractions": u"药物相互作用", 
            "catename": u"药物分类",  
            "forensicclassification": u"药品监管分级", 
            "pack": u"包装",     
            "contraindications": u"禁忌", 
            "precautions": u"注意事项", 
            "adversereactions": u"不良反应", 
            "fda": u"fda妊娠药物分级", 
            "overdosage": u"药物过量", 
            "useinchildren": u"儿童用药", 
            "useinelderly": u"老年用药", 
            "useinpreglact": u"孕妇及哺乳期妇女用药",  
            "storage": u"贮藏", 
            "description": u"性状",   
            "mechanismaction": u"药理作用", 
            "poison": u"毒理研究",    
            "pharmacokinetics": u"药代动力学", 
            "cautions": u"用药须知",  
            "warnings": u"警告", 
            "picpath": u"药品图片",   
            "form": u"规格", 
            "chemical": u"化学成份",  
            "price": u"零售价", 
            "period": u"有效期", 
            "number": u"批准文号",    
            "standard": u"执行标准",  
            "modifydate": u"修改日期", 
            "approvedate": u"核准日期", 
            "cnname": u"商品名", 
            "commonname": u"通用名",  
            "engname": u"英文名",     
            "otc": u"是否otc", 
            "clinicaltrial": u"临床试验", 
            'showname' : u'药品名称',
        } 
        key = self.unicode(key)
        pname = self.unicode(pname)
        collection = mongo_client['wiki']['drug']
        doc = None
        if key:
            doc = collection.find_one({'_id' : key})
            if not doc:
                raise NotFoundError()
        elif pname:
            doc = collection.find_one({'showname' : pname})
            if not doc:
                raise NotFoundError()
        if doc:
            tmp = {}
            for k, v in doc.iteritems():
                if k in key_map:
                    tmp[key_map[k]] = v

            return tmp
        else:
            raise NotFoundError()

    def mark(self, key, source, cname, pname, mongo_client, return_label_info = True):
        key = self.unicode(key)
        source = self.unicode(source)
        cname = self.unicode(cname)
        pname = self.unicode(pname)
        label_drug = self.drug_list.get((key, source))
        if not label_drug:
            raise NotFoundError()
        if not pname and cname not in self.wiki_cname_index:
            raise NotFoundError()
        if not cname and 'cname' in label_drug:
            del label_drug['cname']
        if not pname and 'pname' in label_drug:
            del label_drug['pname']
        if cname:
            label_drug['cname'] = cname
        if pname:
            item_list = self.wiki_pname_index.get(pname)
            if not item_list:
                raise NotFoundError()
            label_drug['cname'] = item_list[0].cname
            label_drug['cnname'] = item_list[0].cnname
            label_drug['pname'] = pname

        collection = mongo_client['label']['drug']
        collection.replace_one({'_id' : label_drug['_id']}, label_drug)
        if return_label_info:
            return self.getLabelInfo(key, source)
        else:
            return None
