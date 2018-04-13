#!/usr/bin/env python
#encoding=utf-8
"""
arthur: james.wen2@emc.com
"""
from lib.base.SSHConnection import SSHConnection
from lib.base.RobotLogger  import RobotLogger
class RemoteUnix( ):
    """
    Base class for general unix commands
    """
    def __init__( self, ssh ):
        self._ssh=ssh
        self._log=RobotLogger()
    def createdir(self, dirpath):
        output=self._ssh.run_command("mkdir -p %s" % (dirpath))
        return not output[2]
    def rmdir(self, dirpath):
        output=self._ssh.run_command("rm -rf %s" % (dirpath))
        return not  output[2]
    def getpwd(self):
        output=self._ssh.run_command("pwd")
        return output[0]
