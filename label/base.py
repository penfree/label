#!/usr/bin/env python
#coding=utf8
"""
# Author: f
# Created Time : Mon 21 Dec 2015 08:02:02 PM CST

# File Name: base.py
# Description:

"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import logging

from contextlib import contextmanager

from unifiedrpc import Service, endpoint, context
from unifiedrpc.errors import BadRequestError, NotFoundError
from unifiedrpc.adapters.web import get, post, put, delete

class ServiceBase(Service):
    """The view service base
    """
    def __init__(self, name, configs):
        """Create a new ViewServiceBase
        """
        self.configs = configs
        # Super
        super(ServiceBase, self).__init__(name)

    @contextmanager
    def getMongodb(self):
        '''
            get mongodb client
        '''
        with self.configs['mongodb'].instance() as mongoClient:
            yield mongoClient
