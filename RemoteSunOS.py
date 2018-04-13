#!/usr/bin/env python
#encoding=utf-8
"""
arthur: james.wen2@emc.com
"""
import re
from lib.remoteos.RemoteUnix import RemoteUnix
class RemoteSunOS( RemoteUnix ):
    """
    Class for SunOS specific commands.Do not implement this class
    """
    def __init__( self, connection):
        RemoteUnix.__init__(self,connection)
        self._type = 'SunOS'
