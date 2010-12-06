#!/usr/bin/env python
"""
Serve a single file one time over https.

python 2 version.
"""

import os
import ssl
import socket
import sys
import tarfile
import tempfile
import traceback

import httplib as client
import BaseHTTPServer as server

err     = sys.stderr.write

class woofs():
    confdir_base    = '.config/woofs/'
    file            = None
    config          = None
    cert            = None
    serv            = None
    sock_type       = None
    
    
    def __init__(self, filename = None, ipv6 = False, certificate = None, keyfile = None, confdir = None):

        # three valid cases:
        #   1. no args are passed to the class: use the configuration dir to
        #   get the server certficate and key.
        #   2. a configuration directory is passed but no certificate / key
        #   files are passed: use the specified configuration dir to get the
        #   certificate / key. Also checks permissions on files.
        #   3. keyfiles are passed but no configuration dir: use the keyfiles
        #   as the key files, no need for a configuration directory.
        #
        # case 1 - default call
        if not confdir and not certificate and not keyfile:
            home    = os.path.expanduser('~')
            confdir = home + '/' + confdir_base
            
            # ensure we have access to configuration directory
            if not self._check_file_perm(confdir, dir = True):
                try:
                    os.makedirs(confdir, 0700)
                    if not self._check_file_perm(confdir, dir = True):
                        err('(init) error creating configuration directory %s\n' % confdir)
                        sys.exit(1)
                except OSError, e:
                    err('%s\n' % e.strerror)
                    sys.exit(1)

            if not self._check_file_perm(confdir, dir = True):
                err('invalid permissions on %s - should be 0700 or 0500\n' % confdir)
                sys.exit(1)

            self.cert   = confdir + 'server.crt'
            self.key    = confdir + 'server.key'
            self._check_keys()
        # case 2: confdir specified
        elif confdir and not certificate and not keyfile:
            if not self._check_file_perm(confdir, dir = True):
                sys.exit(1)
        
        # case 3: keys specified
        elif not confdir and certificate and keyfile:
            self.cert = certificate
            self.key  = keyfile
            self._check_keys()
        
        # every other case is invalid
        else:
            err('invalid paramters to init - check the documentation!\n')
            sys.exit(1)
        
        # basic socket parameter setup
        if ipv6:
            self.sock_type  = socket.AF_INET6
        else:
            self.sock_type  = socket.AF_INET
        
        # load the file
        self.load_file(filename)
        
        # set up an SSL connection
        self._setup_SSL()
        
        # start the server
        self._start_listen( )

    
    def _is_dir(self, filename):
        mode    = os.stat(filename)[0]
        mode    = mode >> 14
        return mode & 1
                
    def _check_file_perm(self, filename):
        """
        Checks for the existance of a file / directory and that it has the proper
        permissions. Returns true if everything is good, otherwise returns false.
        """
        valid_modes =  { True: [ 040700, 040500 ], False: [ 0600, 0400 ] }
        if self._is_dir(filename):
            dir = True
        else:
            dir = False
        
        # basic access check
        if not dir:
            try:
                f   = open(filename)
            except IOError, e:
                err('%s\n' % e.strerror)
                return False
            else:
                f.close()
        else:
            if not os.access(filename, os.F_OK):
                err('%s doesn\'t exist!\n' % filename)
                return False
        
        # file / dir mode check - mod gives us rwx permissions as well as directory check
        try:
            mode    = os.stat()[0] % 0100000
        except OSError, e:
            err('%s\n' % e.strerror)
            sys.exit(1)
        
        return mode in valid_modes[dir]


    def _check_keys(self):
        if not self._check_file_perm(self.cert):
            err('invalid permissions on %s - should be 0600 or 0400\n' % self.cert)
            sys.exit(1)
            
        if not self._check_file_perm(self.key):
            err('invalid permissions on %s - should be 0600 or 0400\n' % self.key)
            sys.exit(1)


    def load_file(self, filename):
        if not os.access(filename, os.R_OK):
            err('could not open %s for reading!\n' % filename)
            sys.exit(1)
        if self._is_dir(filename):
            files   = os.listdir(filename)
            temp_f  = tempfile.NamedTemporaryFile()
            
            tarball = tarfile.open(temp_f.name, mode = 'w:gz')
            for f in files:
                tarball.add('%s/%s' % (filename, f))
            tarball.close()
            os.lseek(temp_f.fileno(), 0, os.SEEK_SET)
            
            f           = open(temp_f.name)
            self.file   = f.read()
            
            f.close()
            temp_f.close()
            
        else:
            try:
                f   = open(filename)
            except IOError, e:
                err('%s\n' % e.strmessage)
                sys.exit(1)
        
        self.file   = f.read( )
        f.close()
    
    def _setup_SSL(self):
        self.serv    = socket.socket( )
    
    def _start_listen(self):
        pass
    
