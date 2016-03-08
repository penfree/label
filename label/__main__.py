#!/usr/bin/env python
#coding=utf8
"""
# Author: f
# Created Time : Mon 21 Dec 2015 07:58:12 PM CST

# File Name: __main__.py
# Description:

"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from gevent import monkey
monkey.patch_all()

import logging

import os.path

import mime

from baselib.os import searchFile
from configmslib import ConfigRepository

from unifiedrpc import Server, CONFIG_RESPONSE_MIMETYPE, CONFIG_RESPONSE_CONTENT_CONTAINER
from unifiedrpc.content.container import APIContentContainer
from unifiedrpc.adapters.web import GeventWebAdapter

from argparse import ArgumentParser
from unifiedrpc import context

from diagnosis.service import DiagnosisService
from drug.service import DrugService
from lab.service import LabService

def getArguments():
    """Get arguments
    """
    parser = ArgumentParser(description = 'label platform micro service')
    parser.add_argument('--host', dest = 'host', default = '0.0.0.0', help = 'The binding host')
    parser.add_argument('--port', dest = 'port', type = int, default = 18001, help = 'The binding port')
    parser.add_argument('--debug', dest = 'debug', default = False, action = 'store_true', help = 'Enable debug')
    parser.add_argument('--config', dest = 'config', required = True, help = 'The config schema file')
    # Done
    return parser.parse_args()

def initResponse(self, context):
    """Initialize the response
    Parameters:
        context                             The Context object
    Returns:
        Nothing
    """
    context.response.mimeType = self.getResponseMimeType(context)
    context.response.encoding = self.getResponseEncoding(context)
    context.response.container = self.getResponseContainer(context)
    context.response.headers['Access-Control-Allow-Origin'] = '*'

def main():
    """The main entry
    """
    args = getArguments()
    # Set logging
    if args.debug:
        logging.basicConfig(format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s', level = logging.DEBUG)
    else:
        logging.basicConfig(format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s', level = logging.INFO)
    # Load config
    config_file = searchFile(args.config, [ os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs') ], False)
    if not config_file:
        logger.error('Config schema file [%s] not found', args.config)
        return 1
    configs = ConfigRepository()
    configs.loadSchema(config_file)
    # Create the server
    Server.initResponse = initResponse
    server = Server([DiagnosisService(configs), DrugService(configs)],
        **{
        CONFIG_RESPONSE_MIMETYPE: mime.APPLICATION_JSON,
        CONFIG_RESPONSE_CONTENT_CONTAINER: APIContentContainer
        })
        #server.addAdapter(GeventWebAdapter('web', args.host, args.port))
    # Add services
    #server.addService(DiagnosisService(configs))
    #server.addService(DrugService(configs))
    # Start server
    #server.start()
    server.start([ GeventWebAdapter('web', args.host, args.port) ], runtimeInitializer = lambda rt: addContextHandlers(rt))

try:
    sys.exit(main())
except KeyboardInterrupt:
    pass

