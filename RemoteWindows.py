#!/usr/bin/env python
#encoding=utf-8
"""
arthur:
"""
from lib.base.SSHConnection import SSHConnection
from lib.base.RobotLogger import RobotLogger
class RemoteWindows( RobotLogger ):
    """
    Class for Windows specific commands. Do not implement this class.
    """
    def __init__( self, connection):
        self._type = 'Windows'
    def get_version( self):
        return "Windows7"
    def get_distribution( self):
        return "Windows7"
    def get_osbit( self):
        return "64"
