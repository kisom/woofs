#!/usr/bin/env python
# -*- coding: utf-8 -*-
# file: http_server.py
# author: kyle isom <coder@kyleisom.net>
#
# simple fileserver that displays a line of text and a link to a file
# usage:
#   ./http_server <file to serve>


import getopt
import os
import socket
import sys
import time
import ssl


class HTTPServer():
    """
    This represents a very bare-bones HTTP server representing the entirety
    of the functionality required by woofs.
    """
    
    sock    = None                              # server socket
    data    = None                              # stores the file to serve
    port    = None                              # port to listen on
    chunk   = 4096                              # number of bytes to send at a
                                                # time
    index   = None                              # holds the index page
    secure  = False                             # using SSL?
    wrapper = None                              # the SSL wrapper function
    keyfile = None                              # private key filename
    certfile = None                             # certificate filename
    
    maxdown = None 

    # the index template
    indextpl= """
<!doctype html>
<html>
<head>
<meta charset = "utf-8">
<title>woofs file share</title>
</head>

<body>
    <p>SSL cert fingerprint: %s</p>
    <p>file: <a href="file/">download</a></p>
</body>
</html>
    """

    def __init__(self, port, file, max_downloads = 0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connected = False

        self.port = port

        if self.secure:
            self.keyfile    = None
            self.certfile   = None
            self.wrapper    = None
        
        while not connected:
            try:
                self.sock.bind(('', port))
            except socket.error, e:
                print '[!] socket error:', e
                time.sleep(1)
            else:
                print '[+] connected!'
                connected = True
                
        self.sock.listen(1)
        
        # load file to be served
        try:
            f           = open(file)
            self.data   = f.read()
            f.close()
            
        except IOError, e:
            print e
            sys.exit(1)
        else:
            f.close()
            
            if not self.secure:
                self.index = self.indextpl % 'NOT SSL'
            else:
                self.index = self.indextpl % self.get_ssl_fp()

        self.maxdown = max_downloads

    def setup_ssl(self, certfile = None, keyfile = None):
        if not self.secure or not certfile or not keyfile: return False

        self.certfile = certfile
        self.keyfile  = keyfile
        self.wrapper  = 'ssl.wrap_socket( client, server_side = True, '
        self.wrapper += 'certfile = self.certfile, keyfile = self.keyfile, '
        self.wrapper += 'ssl_version = ssl.PROTOCOL_TLSv1, '
        self.wrapper += 'cert_reqs = ssl.CERT_NONE )'

        return True

    def run(self):
        while_cond = "True" if not self.maxdown else "downloads < self.maxdown"
        downloads  = 0

        while eval(while_cond):
            client, addr = self.sock.accept()
            if self.secure:
                try:
                    client   = eval(self.wrapper)
                except:
                    # on error make sure the socket gets closed!
                    client.close()
                    print '[!] exception in ssl - closed socket and reraising!'
                    raise
                    
            if self.serve(client, addr): downloads += 1
    
    def serve(self, client, addr):
        data    = client.recv(1024)
        
        print 'data:', data
        if not data.startswith('GET /'):
            return False
        elif data.startswith('GET /file'):
            print '[+] send file!'
            self.send_file(client, self.data)
            return True
        elif data.startswith('GET / '):
            print '[+] send index!'
            self.send_file(client, self.index)
            return False
        else:
            self.send_file(client, '404 - not found!')
            return False
        
    
    def send_file(self, client, file):
        for i in range(0, len(file), self.chunk):
            limit   = ( i + self.chunk if len(file[i:]) >= self.chunk
                                       else i + len(file[i:]) )
            client.send(file[i:limit])
        
        client.close()
        
    
    def shutdown(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        
        

# test code
if __name__ == '__main__':
    
    downloads = 0

    opts, args = getopt.getopt(sys.argv[1:], 'n:')

    if not args: sys.exit(1)

    for opt, val in opts:
        opt = opt.lstrip('-')

        if 'n' is opt:                              # max number of downloads
            downloads = int(val)
    
    server  = HTTPServer(port = 8000, file = args[0],
                         max_downloads = downloads)
    try:
        server.run()
    except KeyboardInterrupt:
        server.shutdown()
    
