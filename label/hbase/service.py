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

class HBaseDebugService(ServiceBase):
    """The diagnosis label service
    """
    logger = logging.getLogger('label.hbase')

    def __init__(self, configs):
        """
            Create a new DiagnosisService
        """
        # Super
        super(HBaseDebugService, self).__init__('label-drug', configs)
        self.drug_manager = DrugManager()

