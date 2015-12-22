#!/usr/bin/env python
#coding=utf8
"""
# Author: f
# Created Time : Mon 21 Dec 2015 07:32:05 PM CST

# File Name: service.py
# Description:

"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import logging

from unifiedrpc import endpoint, context
from unifiedrpc.errors import BadRequestError, NotFoundError
from unifiedrpc.adapters.web import get, post, put, delete

from label.base import ServiceBase
from label.diagnosis.diagnosismanager import DiagnosisManager


class DiagnosisService(ServiceBase):
    """The diagnosis label service
    """
    logger = logging.getLogger('label.diagnosis')

    def __init__(self, configs):
        """
            Create a new DiagnosisService
        """
        # Super
        super(DiagnosisService, self).__init__('label-diagnosis', configs)
        self.diag_manager = DiagnosisManager()
        self.loadData()
    
    def loadData(self):
        '''
            加载信息,待标注信息和已标注信息均从mongodb加载
        '''
        with self.getMongodb() as client:
            self.diag_manager.load(client)
        self.diag_manager.buildIndex()

    @get('/diagnosis/reload')
    @endpoint()
    def reload(self):
        try:
            self.loadData()
        except Exception,e:
            logging.exception(e)
            return {'ret_code' : str(e)}
        return {'ret_code' : 'succ'}

    @get('/diagnosis')
    @endpoint()
    def getDiagnosis(self, type = 'all'):
        '''
            get diagnosis to be label
            @param type: all | labeled | not_labeled
        '''
        return self.diag_manager.getDiagnosis(type)

    @get('/diagnosis/info')
    @endpoint()
    def getLabelInfo(self, key):
        '''
            获取一个诊断的标注信息, 即已标注信息和候选集合
            @param key: 诊断名称
        '''
        groups = self.diag_manager.getLabelInfo(key)
        result = {
            'groups' : [ group.dump() for group in groups ]
        }
        return result

    @get('/diagnosis/mark')
    @endpoint()
    def mark(self, diag, gid):
        '''
            标记诊断所属group
            @param diag: 诊断
            @param gid: 诊断分组id
        '''
        ret = 0
        with self.getMongodb() as client:
            ret = self.mark(diag, gid, client)
        result = {
            'ret_code' : ret        
        }
        return result

    @get('/diagnosis/markgroup')
    @endpoint()
    def markGroup(self, gid, name):
        '''
            标记诊断分组的代表诊断
            @param gid: 诊断分组id
            @param name: 诊断名称
        '''
        with self.getMongodb() as client:
            ret = self.diag_manager.markGroup(gid, name, client)
            return {'ret_code' : ret}

