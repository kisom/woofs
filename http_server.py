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
    index   = None
    
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
                print 'connected!'
                connected = True
                
        self.sock.listen(1)
        
        # load file to be served
        try:
            f           = open(file)
            self.data   = f.read()
            f.close()
            
            f           = open('index.tpl')
            self.index  = f.read()  % 'NOT SSL'
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
        if not data.startswith('GET /'):
            return
        elif data.startswith('GET /file'):
            print 'send file!'
            self.send_file(client, self.data)
        elif data.startswith('GET / '):
            print 'send index!'
            self.send_file(client, self.index)
        else:
            self.send_file(client, '404 - not found!')
        
    
    def send_file(self, client, file):
        for i in range(0, len(file), self.chunk):
            limit   = ( i + self.chunk if len(file[i:]) >= self.chunk
                                       else i + len(file[i:]) )
            client.send(file[i:limit])
        
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
    