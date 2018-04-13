#!/usr/bin/env python
#encoding=utf-8
"""
arthur: james.wen2@emc.com
"""
import re
from lib.base.SSHConnection import SSHConnection
from lib.base.RobotLogger import RobotLogger
from lib.remoteos import RemoteUnix,RemoteWindows,RemoteLinux,RemoteSunOS

class RemoteOS( ):
    """
    Class for encapsulate different OS command ,the entrace for RemoteOS Package.
    """
    def __init__( self, ssh ):
        self._ssh=ssh
        self._log=RobotLogger()
        output=ssh.run_command("uname")
        stdout=output[0]
        if output[2]:
            self._log.warn("uname command failed, suppose Windows platform")
            ros=RemoteWindows(ssh)
        elif re.match(r"Linux", stdout,re.IGNORECASE):
            ros=RemoteLinux(ssh)
        elif re.match(r"SunOS", stdout,re.IGNORECASE):
            ros=RemoteSunOS(ssh)
        else:
            ros=RemoteUnix(ssh)
        self._ros=ros
    def get_osbit(self):
        """
        Get OS bit
        @output "64" or "32"
        """
        return self._ros.get_osbit()
    def get_version(self):
        """
        Get OS version
        @output os version ,for example "SUSE11.3" or "CentOS 7.2.1511"
        """
        return self._ros.get_version()
    def get_distribution(self):
        """
        Get UNIX distribution
        @output distribution ,for example "SUSE" or "CentOS"
        """
        return self._ros.get_distribution()
    def getpwd(self):
        """
        Get current direcotry
        @output:current direcotry
        """
        return self._ros.getpwd()
    def createdir(self,dirpath):
        """
        create directory
        @output: Boolean
        """
        return self._ros.createdir(dirpath)
    def rmdir(self,dirpath):
        """
        remove directory
        @output: Boolean
        """
        return self._ros.rmdir(dirpath)

if __name__=="__main__":
    #ssh=SSHConnection("a4t81d8.datadomain.com","root","changeme",22)
    ssh=SSHConnection("10.110.228.122","root","changeme",22)
    ssh.login()
    ros=RemoteOS(ssh)
    print "client os_bit=%s" %(ros.get_osbit())
    print "client os_version=%s" %(ros.get_version())
    print "client pwd=%s" %(ros.getpwd())
    print "client distribution=%s" %(ros.get_distribution())
    print "creae return=%s" %(ros.createdir("/tmp/ab/dd/cc"))
    print "remove dir return = %s" %(ros.rmdir("/tmp/ab/dd/cc"))
    ssh.logout()
