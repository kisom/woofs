#!/usr/bin/env python
# -*- coding: utf-8 -*-
# file: http_server.py
# author: kyle isom <coder@kyleisom.net>
#
# simple fileserver that displays a line of text and a link to a file

import os
import socket
import sys

class Server():
    
    sock    = None
    port    = None
    
    def __init__(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('', port))
        self.sock.listen(1)
        
    def run(self):
        while True:
            client, addr = self.sock.accept()