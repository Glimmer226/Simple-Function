#!/usr/bin/env python
# encoding=utf-8

from lib.base.RobotLogger import LOG
from lib.server.AvServer import AvServer

class HardwareInfo(AvServer):
    '''
    Class used to query hardware information
    '''
    def __init__(self, ssh=None):
        '''
        Constructor
        '''
        super(self.__class__, self).__init__(ssh)
        self.ssh = ssh
        self.__classname = self.__class__.__name__
        
    def get_memory_total(self):
        '''
        Get total memory size from /proc/meminfo, convert unit to GB
        '''
        cmd  = "cat /proc/meminfo|grep MemTotal|awk '{print $2}'"
        result = self.ssh.run_command(cmd)
        if result[2]:
            LOG.error('Failed with return code:%s, stdout:[%s], stderr:[%s]'
                      % (result[2], result[0], result[1]))
            return -1
        else:
            size = float(result[0]) / 1024 / 1024
            LOG.info('Total memory size: %s' % size)
            return size
