#!/usr/bin/env python
#encoding=utf-8
"""
arthur: james.wen2@emc.com
"""
import re
from lib.remoteos.RemoteUnix import RemoteUnix
class RemoteLinux( RemoteUnix ):
    """
    Class for linux specific commands.
    """
    def __init__( self, connection):
        RemoteUnix.__init__(self,connection)
        self._type = 'Linux'
        self._version = None
        self._distribution = None
    def get_osbit( self):
        output=self._ssh.run_command("uname -p")
        if re.search(r"64", output[0]):
            return "64"
        else:
            return "32"
    def get_version( self ):
        if self._version : return self._version
        output=self._ssh.run_command("if [ -f '/etc/redhat-release' ]; then cat /etc/redhat-release; \
            elif [ -f '/etc/SuSE-release' ]; then cat /etc/SuSE-release; else uname -r; fi")
        stdout=output[0]
        m=re.match(r"(SUSE).*(VERSION\s*=\s*)(\d+).*(PATCHLEVEL\s*=\s*)(\d+)",stdout,re.DOTALL|re.IGNORECASE)
        if m:
            self._version="%s %s.%s" %(m.group(1),m.group(3),m.group(5))
            self._distribution=m.group(1);
        m=re.match(r"(CentOS)\D+([\d|.]+)",stdout,re.DOTALL|re.IGNORECASE)
        if m:
            self._version="%s %s" %(m.group(1),m.group(2))
            self._distribution=m.group(1);
        return self._version
    def get_distribution(self):
        self.get_version()
        return self._distribution
