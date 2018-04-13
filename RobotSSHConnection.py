#!/usr/bin/env python
#encoding=utf-8
"""
authur: james.wen2@emc.com
"""
from SSHLibrary import SSHLibrary
from SSHConnection import SSHConnection
from InteractiveShell import InteractiveShell
from lib.base.RobotLogger import LOG
from robot.libraries.BuiltIn import BuiltIn


def attach_ssh( ssh, class_name):
    '''
    Attch ssh to instance with specific class name
    @class_name : the specific class name 
    @output:None. throw exception if failed
    '''
    instance = BuiltIn().get_library_instance(class_name)
    instance.ssh=ssh
    '''
    try:
        instance = BuiltIn().get_library_instance(class_name)
        instance.ssh=ssh
    except Exception,e:
        LOG.error("Get instance by class failed.%s:%s" %(class_name,str(e)))
        return False
    '''
def attach_ssh_instance( ssh, instance):
    '''
    Attch ssh to instance with instance name
    @class_name : the specific class name 
    @output:None.
    '''
    instance.ssh=ssh
def attch_ssh_avall( ssh ):
    '''
    Attch ssh to all instances in class list
    @output:None. throw exception if failed
    '''
    clist=['AvCP','AvGC','AvDpn','AvHfs','AvTier','AvMaint','AvReplication','AvTierPlugin']
    instances = BuiltIn().get_library_instance(all=True)
    for (cls,ins) in  instances.items():
        if cls in clist:
            LOG.debug( "Attch ssh to [%s]" %(cls))
            attach_ssh_instance(ssh,ins)
def interactive_ssh_connect_to(hostname,username,password,port=22,timeout=60,prompt=""):
    """
    Login to remote ssh server using InteractiveShell object
    """
    ssh=InteractiveShell(hostname,username,password,port,timeout,prompt)
    ssh.login()
    return ssh

#def ssh_connect_to(hostname,username,password,port=22,timeout=60,prompt="#"):
def ssh_connect_to(hostname,username,password,port=22,timeout=60,prompt=""):
    """
    Login to remote ssh server
    """
    ssh=SSHConnection(hostname,username,password,port,timeout,prompt)
    ssh.login()
    return ssh
def ssh_disconnect(ssh):
    """
    Logout remote ssh server
    """
    ssh.logout()
def ssh_change_to_root(ssh,password):
    ssh.change_to_root_user(password)

def run_cmd(ssh,cmd):
    re=ssh.execute_command(cmd)
    return re
def check_admin_password_complexity(ssh,command,password):
    re = ssh.admin_password_complexity_check(command,password)
    return re
def ssh_change_admin_password(ssh,command,new_password,default_password):
    re = ssh.change_admin_password(command,new_password,default_password)
    return re

def handleRootAccess(ssh, passwd, action='enable'):
    # can only use 'admin' account to enable 'root' account
    ssh.login()
    ssh.write("su -")
    ssh.read_until_regexp("Password")
    ssh.write(passwd)
    output = ssh.read_until_regexp("/#:")
    if action == 'enable':
        cmd = "sed -i s/^'PermitRootLogin no'/'PermitRootLogin yes'/\
               /etc/ssh/sshd_config"
    else:
        cmd = "sed -i s/^'PermitRootLogin yes'/'PermitRootLogin no'/\
               /etc/ssh/sshd_config"
    ssh.write(cmd)
    ssh.read_until_regexp("/#:")
    cmd = "/etc/init.d/sshd restart"
    ssh.write(cmd)
    ssh.read_until_regexp("/#:")

def ssh_run_command_error_quit(ssh,cmd):
    result=ssh.run_command(cmd) 
    if result[2]:
        LOG.error("cmd failed:%s" %(cmd))
        for i in range(2):
            LOG.error("result[%d] :%s" %(i,result[i]))
        raise Exception,"Execute command failed:%s." %(cmd)
    return result[0]

def ssh_run_command_get_result( ssh,cmd):
    try:
        result=ssh.run_command(cmd) 
    except Exception,e:
        LOG.warn("Execute command %s failed with Exception:%s" %(cmd,str(e)))
        return False
    if result[2]: return False
    return True
    
def ssh_run_command( ssh,cmd):
    try:
        result=ssh.run_command(cmd) 
    except Exception,e:
        LOG.warn("Execute command %s failed with Exception:%s" %(cmd,str(e)))
        return ''
    if result[2]:
        LOG.warn("cmd failed:%s" %(cmd))
        for i in range(2):
            LOG.warn("result[%d] :%s" %(i,result[i]))
        return ''
    #stdout
    return result[0] 

def ssh_run_command_async( ssh,cmd):
    try:
        ssh.start_command(cmd) 
        return True
    except Exception,e:
        LOG.warn("Execute command %s failed with Exception:%s" %(cmd,str(e)))
        return False

def get_async_result(ssh):
    return ssh.read_command_output(return_stdout=True, return_stderr=True, return_rc=True)


def overlap_command_running(cmdlist,cmd1,ssh):
    '''
    This function is used to run several commands at the same time on server
    @cmslist: command list which are running in the background by using start_command
    @cmd1: command are executed by using execute_command   
    @ssh: server connection
    '''
    stdout_result,stderr_result,stdrc_result=ssh.run_overlap_command(cmdlist, cmd1)
    for i in range(0,len(stdrc_result)):
        if stdrc_result[i]==0:
            if 'ERROR' not in stdout_result[i]:
                if  'ERROR' not in stderr_result[i]:
                    pass
                else:
                    LOG.error(stderr_result[i])
                    return False
            else:
                LOG.error(stderr_result[i])
                return False
        else:
            LOG.error('Command return code is %s'%stdrc_result[i])
            return False            
    return True
    
    
def server_overlap_client(server_cmd,client_cmd,server_ssh,client_ssh):
    '''
    This function is used to run server command and client command at the same time
    @server_cmd: command run on the server
    @client_cmd: command run on the client
    @server_ssh: connection to the server
    @client_ssh: connection to the client
    '''
    server_ssh.ssh_agent.start_command(server_cmd)
    client_ssh.login()
    client_ssh.ssh_agent.start_command(client_cmd)
    server_result=server_ssh.ssh_agent.read_command_output(return_stdout=True, return_stderr=True,return_rc=True)
    print server_result
    client_result=client_ssh.ssh_agent.read_command_output(return_stdout=True, return_stderr=True,return_rc=True)
    print client_result
    if server_result[2]==0 and client_result[2]==0:
        #if 'ERROR' not in server_result[0] & 'ERROR' not in server_result[1] & 'ERROR' not in client_result[0] & 'ERROR' not in client_result[1]:
        return True
    else:
        return False
    


if __name__=="__main__":
    LOG.enable_console_log()
    LOG.info("Robot ssh connection")
    ssh=ssh_connect_to("a4t81d8.datadomain.com","root","changeme",22)
    LOG.info("Robot ssh connection testing ssh_run_command")
    output=ssh_run_command(ssh,"ls")
    print output
    output=ssh_run_command(ssh,"aaaa")
    print output
    LOG.info("Robot ssh connection testing ssh_run_command_get_result")
    output=ssh_run_command_get_result(ssh,"ls")
    print output
    output=ssh_run_command_get_result(ssh,"aaaa")
    print output
    LOG.info("Robot ssh connection testing ssh_run_command_error_quit")
    output=ssh_run_command_error_quit(ssh,"ls")
    print output
    output=ssh_run_command_error_quit(ssh,"aaaa")
    print output
    ssh_disconnect(ssh)
