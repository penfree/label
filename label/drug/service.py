#!/usr/bin/env python
#coding=utf8
"""
# Author: f
# Created Time : Tue 29 Dec 2015 03:16:32 PM CST

# File Name: service.py
# Description:

"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from unifiedrpc import endpoint, context
from unifiedrpc.errors import BadRequestError, NotFoundError
from unifiedrpc.adapters.web import get, post, put, delete

import logging
from label.base import ServiceBase
from label.drug import DrugManager

class DrugService(ServiceBase):
    """The diagnosis label service
    """
    logger = logging.getLogger('label.drug')

    def __init__(self, configs):
        """
            Create a new DiagnosisService
        """
        # Super
        super(DrugService, self).__init__('label-drug', configs)
        self.drug_manager = DrugManager()
        self.loadData()

    def loadData(self):
        with self.getMongodb() as client:
            self.drug_manager.loadData(client)

    @get('/drug')
    @endpoint()
    def getDrugList(self, source):
        '''
            获取标注列表
            @param source: 医院alias
        '''

        return self.drug_manager.getDrugList(source)


    @get('/drug/info')
    @endpoint()
    def getLabelInfo(self, key, source):
        '''
            获取标注信息
            @param key: 药品的key
            @param source: 来源医院
        '''
        return self.drug_manager.getLabelInfo(key, source)
    
    @get('/drug/mark')
    @endpoint()
    def mark(self, key, source, cname = None, pname = None):
        '''
            标注通用名或商品名
            @param key: 药品的key
            @param source: 来源医院
            @param cname: 通用名
            @param pname: 商品名
        '''
        result = None
        with self.getMongodb() as client:
            result = self.drug_manager.mark(key, source, cname, pname, client)
        return result
    
    @get('/drug/wikilist')
    @endpoint()
    def getWikiList(self, cname = None, pname = None):
        '''
            获取wiki列表
        '''
        result = None
        with self.getMongodb() as client:
            result = self.drug_manager.getWikiList(cname, pname, client)
        return result

    @get('/drug/wiki')
    @endpoint()
    def getWiki(self, key = None, pname = None):
        '''
            获取wiki页面
        '''
        if not key and not pname:
            raise BadRequestError()
        result = None
        with self.getMongodb() as client:
            result = self.drug_manager.getWiki(key, pname, client)
        return result
