#!/usr/bin/env python
#encoding=utf-8

'''
author: Avamar Core Qa
'''

from lib.base.RobotLogger import LOG

class CommonUtils():
    '''
    This class is used to describe the common function used in all the library
    '''
    def __init__(self):
        pass
        
    def generate_cmd(self, cmd, optionlist=[]):
        '''
        This function is used to generate command 
        '''
        if optionlist:
            for option in optionlist:
                    cmd = cmd + ' ' + option
            LOG.info("%s"%cmd)
        return cmd

    def generate_cmd_list(self,cmd,cmdlist='',empty=True):
        '''
        @cmd: command need to be added to command list
        @cmdlist: The command list which need to be returned
        This function is used to add command to a command list 
        '''
        if empty:
            cmdlist=[]
        cmdlist.append(cmd)
        return cmdlist
        