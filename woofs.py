#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Serve a single file one time over https.

see the README.
python 2 version.
"""

# note: branched after commit f8e9bea1916da34d07c0e1e039936e8edc1e759f to
# do a rewrite of the code

import argparse
import os
import random
import socket
import ssl
import sys
import time
#from http_server import HTTPServer

def err(err_message):
    sys.stderr.write('%s\n' % err_message)

# constants
confdir_base        = os.path.join('.config', 'woofs')

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
        self.wrapper += 'cert_reqs = ssl.CERT_NONE, ca_certs = self.certfile )'

        return True

    def run(self):
        while_cond = "True" if not self.maxdown else "downloads < self.maxdown"
        downloads  = 0

        while eval(while_cond):
            client, addr = self.sock.accept()
            if self.secure:
                try:
                    client   = eval(self.wrapper)
                except ssl.SSLError as e:
                    if e.errno == 1: continue
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



class woofs():
    
    conf_file       = None
    key             = None
    keyfile         = None
    cert            = None
    certfile        = None
    external        = None
    server          = None
    
    def __init__(self, config_file = None, hport = None, keyfile = None,
                 certfile = None, filename = None, external = False,
                 downloads = 0):
        
        if not filename:
            print 'need a filename!'
            sys.exit(1)
        
        if not hport:
            hport   = random.randint(8000, 9000)
        
        # initialise http server
        self.server = HTTPServer(port = hport, file = filename,
                                 max_downloads = downloads)
        # load keys - either via config file or key/cert files
        if not certfile and not keyfile and not certfile:
            # default case: use the default config file
            
            # build path and check permissions
            conf_file = os.path.join(os.path.expanduser('~'),
                                     '.config', 'woofs', 'config')
            if not self.__check_fperms__(conf_file):
                err('bad permissions on config file: %s!' % conf_file)
                sys.exit(1)
                
            keyfile, certfile = self.__load_config__(conf_file)
            self.keyfile, self.certfile = keyfile, certfile
            
            # not necessary right meow, ssl call requires filepaths, not
            # the file contents
            self.key, self.cert = self.__load_keys__(keyfile, certfile)
                
        elif config_file and not keyfile and not certfile:
            # config file passed in
            pass
        elif not config_file and keyfile and certfile:
            # key/cert filenames passed in
            pass
        else:
            err('Invalid initialisation options -- cannot initialise keys!')
            sys.exit(1)
    
        self.server.secure = True
        self.server.setup_ssl( keyfile = self.keyfile, certfile = self.certfile )

        print '[+] woofs listening on port %d...' % hport
        
    
    def __is_dir__(self, filename):
        # test if filename is a directory
        try:
            mode    = os.stat(filename)[0]
        except OSError, e:
            err(str(e))
            sys.exit(1)
            
        mode    = mode >> 14
        return mode & 1

    def __check_fperms__(self, filename):
        """
        Checks that the permissions on a file are secure.
        
        Returns True if permissions are secure and False otherwise.
        """
        
        # we use True/False to check whether we're using a directory or not
        # i.e., valid_modes[dir] where dir is a boolean that is True if filename
        # is a directory.
        valid_modes = { True: [ 40700, 040500 ], False: [ 0600, 0400] }
        dir         = self.__is_dir__(filename)
        
        try:
            mode    = os.stat(filename)[0]
            mode   %= 0100000
        except OSError, e:
            err(str(e))
            sys.exit(1)
        
        return mode in valid_modes[dir]
        
    def __load_config__(self, filename):
        """
        Load a configuration file, parsing out the key and cert options.
        
        Returns a string tuple of the keyfile path and cert file path.
        """
        
        cfg         = { }
        try:
            f       = open(filename)
            files   = f.read().split('\n')
            
            # attempt to load cert and key config options from file
            for line in files:
                # only split the first word because Windows uses the colon in
                # some pathnames
                config      = line.split(':', 1)
                config      = [ line.strip() for line in config ]
                
                # ensure we have a valid config value
                if not config[0] in [ 'key', 'cert' ]:
                    continue
                else:
                    cfg[config[0]] = config[1]
            
        
        except IOError, e:
            err('error reading config file! error returned was:')
            err(str(e))
            sys.exit(1)

        if not 'key' in cfg or not 'cert' in cfg:
            err('invalid config file - check the README!')
            sys.exit(1)
            
        # return the key and cert file paths
        return cfg['key'], cfg['cert']
        
    
    def __load_keys__(self, keyfile, certfile):
        try:
            k   = open(keyfile, 'rb').read()
            c   = open(certfile, 'rb').read()
        
        except IOError, e:
            err('unable to load key/cert! error was:')
            err(str(e))
            sys.exit(1)
        
        else:
            return k, c

    def run(self):
        self.server.run()
        self.server.shutdown()


def setup_default_config():
    """
    sets up a default configuration file. on success, prints a success message.
    on failure, exits the program.
    """
    conf_file   = os.path.join(os.path.expanduser('~'), confdir_base, 'config')
    
    if not os.access(os.path.basename(conf_file), os.W_OK):
        err('cannot write to %s' % os.path.basename(conf_file))
        
        os.makedirs(os.path.dirname(conf_file), 0700)
        if not os.access(os.path.dirname(conf_file), os.W_OK):
            err('\tdirectory creation failed!')
            sys.exit(1)

    try:
        f = open(conf_file, 'w')
        f.write('key: /etc/ssl/private/server.key\n')
        f.write('cert: /etc/ssl/server.crt\n')
        f.close()
    except OSError, e:
        err(str(e))
        sys.exit(1)
    
    print 'wrote configuration file at', conf_file,
    print 'with default key locations...'
    return



    
if __name__ == '__main__':
    pass
    
