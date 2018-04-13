#!/usr/bin/env python
# encoding=utf-8

import re
from lib.base.RobotLogger import LOG
from lib.server.AvServer import AvServer


class AtRestEncryption(AvServer):
    '''
    A class used for data-at-rest encryption related commands
    '''
    def __init__(self):
        '''
        Constructor
        '''
        pass

    def are_attach_ssh(self, ssh_connection):
        '''
        Attach the server's ssh connection to AtRestEncryption instance.
        @ssh_connection:  ssh connection to server, should be interactive
                          ssh connection.
        '''
        self.ssh = ssh_connection

    def set_password(self, password):
        '''
        Set a new password to access the salt table in the persistent store.
        @password:  The new salt table password. password can contain any
                    character (ASCII as well as multibyte character sets are
                    supported) and should be enclosed in single quotes.
                    Empty strings are not allowed.
        @return:    The command execution result.
        '''
        cmd = "avmaint atrestencryption --restpassword='%s' --ava" % password
        LOG.info('Execute command: %s' % cmd)
        std_out, std_err, ret_code = self.ssh.run_command(cmd)
        LOG.info('Output: %s, Error: %s, Return code: %s' % (std_out, std_err, ret_code))
        if ret_code == 0:
            if 'ERROR' in std_out.upper() or 'ERROR' in std_err.upper():
                return False
            return True
        else:
            return False

    def set_salt(self, salt):
        '''
        Set a new salt to create secure encryption key.
        @salt:      salt is a user-defined character string (salt), which is
                    used to create secure encryption key. salt can contain
                    any character (ASCII as well as multibyte character sets
                    are supported) and should be enclosed in single quotes.
                    Empty strings are not allowed.
        @return:    The command execution result.
        '''
        cmd = "avmaint atrestencryption --restsalt='%s' --ava" % salt
        LOG.info("Execute command: %s" % cmd)
        std_out, std_err, ret_code = self.ssh.run_command(cmd)
        LOG.info('Output: %s, Error: %s, Return code: %s' % (std_out, std_err, ret_code))
        if ret_code == 0:
            if 'ERROR' in std_out.upper() or 'ERROR' in std_err.upper():
                return False
            return True
        else:
            return False

    def check_status(self):
        '''
        Check data-at-rest encryption status.
        @return:    data-at-rest encryption status.
        '''
        cmd = 'avmaint nodelist --xmlperline=9999 | grep atrestencryption'
        LOG.info("Execute command: %s" % cmd)
        std_out, std_err, ret_code = self.ssh.run_command(cmd)
        LOG.info('Output: %s, Error: %s, Return code: %s' % (std_out, std_err, ret_code))
        if ret_code == 0:
            m = re.search('<atrestencryption-status enabled="(true|false)" nr-salts="(\d+)"/>', std_out)
            if m:
                return str(m.group(1)) == 'true', int(m.group(2))
            else:
                return False, -1
        else:
            return False, -1

    def enable_at_rest_encryption(self, password, salt):
        self.set_password(password)
        self.set_salt(salt)
        status = self.check_status()
        return status[0]
