#!/usr/bin/env python
# -*- coding: utf-8 -*-
# file: http_server.py
# author: kyle isom <coder@kyleisom.net>
#
# simple fileserver that displays a line of text and a link to a file

import os
import socket
import sys
import time

class Server():
    
    sock    = None                              # server socket
    data    = None                              # stores the file to serve
    port    = None                              # port to listen on
    chunk   = 4096                              # number of bytes to send at a
                                                # time
    
    def __init__(self, port, file):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = False
        
        while not connected:
            try:
                self.sock.bind(('', port))
            except socket.error, e:
                print 'address in use -- delaying...'
                if e.errno == 98: time.sleep(1)
            else:
                connected = True
                
        self.sock.listen(1)
        
        # load file to be served
        try:
            f           = open(file)
            self.data   = f.read()
        except IOError, e:
            print e
            sys.exit(1)
        else:
            f.close()
        
    def run(self):
        while True:
            client, addr = self.sock.accept()
            self.serve(client, addr)
    
    def serve(self, client, addr):
        data    = client.recv(1024)
        
        print 'data:', data
        if not data.startswith('GET / '):
            return
        
        else:
            print 'data length:', len(self.data)
            print 'chunk size: ', self.chunk
            for i in range(0, len(self.data), self.chunk):
                limit   = ( i + self.chunk if len(self.data[i:]) >= self.chunk
                                           else i + len(self.data[i:]) )
                print i, limit
                client.send(self.data[i:limit])
        
        client.close()
    
    def shutdown(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        
        

if __name__ == '__main__':
    
    if not len(sys.argv) == 2: sys.exit(1)
    
    server  = Server(port = 8000, file = sys.argv[1])
    try:
        server.run()
    except KeyboardInterrupt:
        server.shutdown()
    