#!/usr/bin/env python
"""
Serve a single file one time over https.

python 2 version.
"""

import os
import ssl
import socket
import sys
import traceback

import httplib as client
import BaseHTTPServer as server

err     = sys.stderr.write

class woofs():
    confdir_base    = '.config/woofs/'
    file            = None
    config          = None
    cert            = None
    
    def __init__(self, certificate = None, keyfile = None, confdir = None):

        # three valid cases:
        #   1. no args are passed to the class: use the configuration dir to
        #   get the server certficate and key.
        #   2. a configuration directory is passed but no certificate / key
        #   files are passed: use the specified configuration dir to get the
        #   certificate / key. Also checks permissions on files.
        if not confdir and not certificate and not keyfile:
            home    = os.path.expanduser('~')
            confdir = home + '/' + confdir_base
            
            # ensure we have access to configuration directory
            if not os.access(confdir, os.F_OK):
                try:
                    os.makedirs(confdir, 0700)
                    if not os.access(confdir, os.F_OK):
                        err('(init) error creating configuration directory %s\n' % confdir)
                        sys.exit(1)
                except OSError, e:
                    err('%s\n' % e.strerror)
                    sys.exit(1)

            self.cert   = confdir + 'server.crt'
            self.key    = confdir + 'server.key'

    if not confdir and certficate and keyfile:
        pass


    def _check_file_perm(self, filename, dir = False):
        valid_modes =  { True: [ 0700, 0500 ], False: [ 0600, 0400 ] }
        
        # since we are only concerned with the first four digits in the mode,
        # we get rid of any values greater than 08888, which is 010000
        try:
            mode    = os.stat()[0] % 010000
        except OSError, e:
            err('%s\n' % e.strerror)
            sys.exit(1)
        
        return mode in valid_modes[dir]


    def load_file(self, filename):
        if not os.access(filename, os.R_OK):
            err('could not open %s for reading!\n' % filename)
            sys.exit(1)
    try:
        f   = open(filename)
    except IOError, e:
        err('%s\n' % e.strmessage)
        sys.exit(1)
    
    self.file   = f.read( )
    
