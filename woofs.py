#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Serve a single file one time over https.

see the README.
python 2 version.
"""

# note: branched after commit f8e9bea1916da34d07c0e1e039936e8edc1e759f to
# do a rewrite of the code

import os
import random
import ssl
import sys
from http_server import HTTPServer

def err(err_message):
    sys.stderr.write('%s\n' % err_message)

# constants
confdir_base        = os.path.join('.config', 'woofs')

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
            print '[+] keyfile:', keyfile
            print '[+] certfile:', certfile
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
        print 'loading config from', filename
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
    w = woofs()
    
