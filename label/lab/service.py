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
from unifiedrpc.helpers import paramtype
from unifiedrpc.errors import BadRequestError, NotFoundError
from unifiedrpc.adapters.web import get, post, put, delete

import logging
from label.base import ServiceBase
from label.lab.labmanager import LabManager, STD_LAB_COLLECTION, LABEL_LAB_COLLECTION

class LabService(ServiceBase):
    """The diagnosis label service
    """
    logger = logging.getLogger('label.lab')

    def __init__(self, configs):
        """
            Create a new DiagnosisService
        """
        # Super
        super(LabService, self).__init__('label-lab', configs)
        self.lab_manager = LabManager()
        self.loadData()

    def loadData(self):
        with self.getMongodb() as client:
            self.lab_manager.loadData(client)

    @get('/lab/reload')
    @endpoint()
    def reload(self):
        self.loadData()

    @get('/lab')
    @endpoint()
    def getLabList(self, source):
        '''
            获取待标注列表
        '''
        return self.lab_manager.getLabList(source)

    @get('/lab/info')
    @paramtype(sample = unicode, name = unicode)
    @endpoint()
    def getLabelInfo(self, sample, name, source):
        '''
            获取候选标注结果
        '''
        return self.lab_manager.getLabelInfo(sample, name, source)

    @get('/lab/mark')
    @paramtype(sample = unicode, name = unicode, nsample = unicode, nname = unicode, nmethod = unicode)
    @endpoint()
    def mark(self, sample, name, source, nid = None, nsample = None, nname = None, method = None):
        '''
            标注标准词,
            @param sample: 待标注样本名称
            @param name: 待标注指标名称
            @param nsample: 标准词的样本名称
            @param nname: 标准词的指标名称
        '''
        result = []
        with self.getMongodb() as client:
            result = self.lab_manager.mark(sample, name, source, nid, nsample, nname, method, client)
        return result

    @get('/lab/unmark')
    @paramtype(sample = unicode, name = unicode, method = unicode)
    @endpoint()
    def unmark(self, sample, name, source, nsample, nname, method = None):
        '''
            取消标注标准词,
            @param sample: 待标注样本名称
            @param name: 待标注指标名称
            @param nsample: 标准词的样本名称
            @param nname: 标准词的指标名称
        '''
        result = []
        with self.getMongodb() as client:
            result = self.lab_manager.unmark(sample, name, source, nsample, nname, method, client)
        return result

    @get('/lab/stdlist')
    @endpoint()
    def getStdItemList(self):
        '''
            获取标准词列表
        '''
        result = []
        with self.getMongodb() as client:
            result = self.lab_manager.getStdItemList(client)
        return result

    @get('/lab/getdict')
    @endpoint()
    def getDict(self, source):
        '''
            获取字典
        '''

    @get('/lab/editstd')
    @paramtype(sample = unicode, name = unicode, method = unicode, unit = unicode, range = unicode, qualitative_option = unicode)
    @endpoint()
    def editStdItem(self, **kwargs):
        result = None
        with self.getMongodb() as client:
            result = self.lab_manager.editStdItem(client, **kwargs)
        return result.dump()


    @get('/lab/getstd')
    @paramtype(sample = unicode, name = unicode, method = unicode, id = int)
    @endpoint()
    def getStdItem(self, sample = None, name = None, method = None, id = None):
        '''
            获取标准词
        '''
        return self.lab_manager.getStdItem(sample, name, method, id)

    @get('/lab/delstd')
    @paramtype(id = int)
    @endpoint()
    def delStdItem(self, id):
        with self.getMongodb() as client:
            self.lab_manager.delStdItem(id, client)

