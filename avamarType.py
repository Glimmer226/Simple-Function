#!/usr/bin/env python
#encoding=utf-8
"""
authur: kevin.zou@emc.com
"""
import re
from lib.base.RobotLogger import LOG
class avamarType():
    def __init__(self,ssh=None):
        self.__ssh=ssh
    
    def attach_ssh(self,ssh):
        self.__ssh=ssh
        
    def getAvamarType(self):
        """
        Get Avamar type, first check whether it's a physical node, if it's a AVE, check config file node.cfg
        Valid types: gen4/gen4s/gen4t/vmware ave/kvm ave/hyperv ave/azure ave/aws ave
        """
        if not self.__ssh:
            LOG.error("No ssh connection attached")
            return ""
        physical_machine_check_command_list={"gen4":"cat /proc/cpuinfo  | grep -q 5504",
                            "gen4s":"sudo dmidecode | grep -q S2600G",
                            "gen4t":"/sbin/div_cli -r 2>/dev/null| grep -q GEN4T"}
        try:
            for physical_type,cmd in physical_machine_check_command_list.items():
                res=self.__ssh.run_command(cmd)
                if res[2]==0:
                    return physical_type
            #If not physical machines, check whether it's AVE
            ave_type_file="/usr/local/avamar/etc/node.cfg"
            res=self.__ssh.run_command("ls %s"%ave_type_file)
            #Check whether node.cfg exited
            if res[2]==0:
                res=self.__ssh.run_command("cat %s"%ave_type_file)
                if res[2]==0:
                    #Try to find AVE type
                    node_type_content=res[0]
                    for line in node_type_content.split("\n"):
                        if re.match("ave type=\s*(.*)", line):
                            ave_type= re.search("ave type=\s*(.*)", line).group(1)
                            return ave_type+" ave"
        except Exception,e:
            LOG.error(str(e))
        return ""

if __name__=="__main__":
    from lib.base.SSHConnection import SSHConnection
    at=avamarType()
    interactive_ssh=SSHConnection("10.62.227.66","admin","Chang3M3Now.",22,30,"")
    interactive_ssh.login()
    at.attach_ssh(interactive_ssh)
    print at.getAvamarType()