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
from label.lab.labmanager import LabManager

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
    @endpoint()
    def getLabelInfo(self, sample, name, source):
        '''
            获取候选标注结果
        '''
        return self.lab_manager.getLabelInfo(sample, name, source)

    @get('/lab/mark')
    @endpoint()
    def mark(self, sample, name, source, nsample = None, nname = None, method = None):
        '''
            标注标准词,
            @param sample: 待标注样本名称
            @param name: 待标注指标名称
            @param nsample: 标准词的样本名称
            @param nname: 标准词的指标名称
        '''
        result = []
        with self.getMongodb() as client:
            result = self.lab_manager.mark(sample, name, source, nsample, nname, method, client)
        return result

    @get('/lab/unmark')
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
            collection = client['label']['std_lab']
            for doc in collection.find():
                result.append(doc)
        return result

    @get('/lab/getdict')
    @endpoint()
    def getDict(self, source):
        '''
            获取字典
        '''

    @get('/lab/editstd')
    @endpoint()
    def editStdItem(self, sample, name, method = u'缺省', unit = None, range = None, qualitative_option = None):
        result = None
        with self.getMongodb() as client:
            result = self.lab_manager.editStdItem(client, sample, name, method = method,
                                unit = unit, range = range, qualitative_option = qualitative_option)
        return result.dump()


    @get('/lab/sample')
    @endpoint()
    def getSampleList(self):
        '''
            获取样本列表
        '''
        return self.lab_manager.getSampleList()
    
    @get('/lab/sample/add')
    @endpoint()
    def addSample(self, sample):
        '''
            增加样本
        '''
        result = None
        with self.getMongodb() as client:
            self.lab_manager.addSample(sample, client)
        result = self.lab_manager.getSampleList()
        return result

    @get('/lab/sample/addparent')
    @endpoint()
    def addSampleParent(self, sample, parent):
        '''
            给样本添加上位样本
        '''
        result = None
        with self.getMongodb() as client:
            result = self.lab_manager.addSampleParent(sample, parent, client)
        return result

    @get('/lab/sample/removeparent')
    @endpoint()
    def removeSampleParent(self, sample, parent):
        '''
            移除上位样本
        '''
        result = None
        with self.getMongodb() as client:
            return self.lab_manager.removeSampleParent(sample, parent, client)
        return result

    @get('/lab/getstd')
    @endpoint()
    def getStdItem(self, sample, name, method):
        '''
            获取标准词
        '''
        return self.lab_manager.getStdItem(sample, name, method)


