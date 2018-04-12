#encoding=utf-8
import os
import re
import sys
import time
import json
import urllib2
import paramiko
import smtplib
import platform
import logging
import logging.handlers
from email.mime.text import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.header import Header
from optparse import OptionParser

#Pylts config file template
CONFIG_TEMPLATE="""
# pylts template config file

from pylts import log as qalog, qautils
import sys
import os

workingdir = "WORKINGDIR_REPLACE_HERE"
restoredir = "RESTOREDIR_REPLACE_HERE"
remotefolder = "REMOTEFOLDER_REPLACE_HERE"

generate = 1

# logging stuff
run_id = qautils.get_run_id(workingdir)
logfile = os.path.join(workingdir, "%s.out" % run_id)
print "Log file is %s" % logfile

# project tags #
# uncomment and add comma seperated list of additional project tags when
# posting in QADB
project = "TAG_REPLACE_HERE"

qalog.setconsumer('logfile', open(str(logfile), 'w', buffering=1))
qalog.setconsumer('console', qalog.STDOUT)
qalog.setconsumer('null', None)
qalog.setconsumer('db', qalog.QADB)

email = "EMAIL_REPLACE_HERE"

log = qalog.MultipleProducer('logfile')
log.debug = qalog.MultipleProducer('logfile').debug
log.info = qalog.MultipleProducer('logfile').info
log.warn = qalog.MultipleProducer('logfile').warn
log.error = qalog.MultipleProducer('logfile').error
log.critical = qalog.MultipleProducer('logfile').critical
log.db = qalog.MultipleProducer('db')

dpn       = "HFSADDR_REPLACE_HERE"
hfsaddr   = "HFSADDR_REPLACE_HERE"
mcs_node  = "HFSADDR_REPLACE_HERE"
# hardware = "HARDWARE_REPLACE_HERE";
# dpndim   = "DPNDIMENSION_REPLACE_HERE";
module0   = "HFSADDR_REPLACE_HERE";
module1   = "";
mcs       = dpn;
password  = "8RttoTriz";
sourcedir = "/data01/home/admin/sources";
bindir = "/usr/local/avamar/bin";
srcdir = "/usr/local/avamar/src";
vardir = "/usr/local/avamar/var";
stripesize = 0;  # (120*1024*1024);
cpid = "";

# # default test case options (enabled when ver_opt = 0 or a version is not found)
args = {}
args["cp"] = ""  # ./lts dpn.cp flags    
args["gc"] = ""  # ./lts dpn.gc flags
args["hfscheck"] = ""  # ./lts dpn.hfscheck flags
args["rollinghfs"] = "0"  # checkdata=0 as default
args["daily"] = ""  # ./lts mci.snapups (daily) flags
args["repl"] = ""  # repl_cron flags
args["fill"] = ""  # ./lts mci.snapups (fill) flags
args["restore"] = ""  # ./lts mci.snapups (restore) flags
args["gctime"] = "3600"  # number of seconds to run gc_cron
args["deleteGB"] = "150"  # number of GB to delete in gc_dpn
args["balancemin"] = "15"  # avmaint config balancemin value
args["wait.crunch"] = "60"  # default time to run wait.crunch for (minutes)

# # Avamar version options
ver_opt = 1  # on = 1, off = 0
args["cp-3.6.1"] = ""
args["cp-3.7.1"] = ""
args["cp-3.7.2"] = ""
args["cp-4.0.0"] = ""
args["cp-4.0.1"] = ""
args["cp-4.0.2"] = ""
args["cp-4.1.0"] = ""
args["gc-4.0.0"] = ""
args["gc-4.0.1"] = ""
args["gc-4.1.0"] = ""
args["hfscheck-3.6.1"] = ""
args["hfscheck-3.7.1"] = ""
args["hfscheck-3.7.2"] = ""
args["hfscheck-4.0.0"] = ""
args["hfscheck-4.0.1"] = ""
args["hfscheck-4.0.2"] = ""
args["hfscheck-4.1.0"] = ""
args["daily-3.6.1"] = ""
args["daily-3.7.1"] = ""
args["daily-3.7.2"] = ""
args["daily-4.0.0"] = ""
args["daily-4.0.1"] = ""
args["daily-4.0.2"] = ""
args["daily-4.1.0"] = ""
args["repl-3.6.1"] = ""
args["repl-3.7.1"] = ""
args["repl-3.7.2"] = ""
args["repl-4.0.0"] = ""
args["repl-4.0.1"] = ""
args["repl-4.0.2"] = ""
args["repl-4.1.0"] = ""
args["fill-3.6.1"] = ""
args["fill-3.7.1"] = ""
args["fill-3.7.2"] = ""
args["fill-4.0.0"] = ""
args["fill-4.0.1"] = ""
args["fill-4.0.2"] = ""
args["fill-4.1.0"] = ""
args["restore-3.6.1"] = ""
args["restore-3.7.1"] = ""
args["restore-3.7.2"] = ""
args["restore-4.0.0"] = ""
args["restore-4.0.1"] = ""
args["restore-4.0.2"] = ""
args["restore-4.1.0"] = ""
args["gctime-3.6.1"] = "3600"
args["gctime-3.7.1"] = "3600"
args["gctime-3.7.2"] = "3600"
args["gctime-4.0.0"] = "3600"
args["gctime-4.0.1"] = "7200"
args["gctime-4.0.2"] = "7200"
args["gctime-4.1.0"] = "7200"
args["deleteGB-3.6.1"] = "150"
args["deleteGB-3.7.1"] = "150"
args["deleteGB-3.7.2"] = "150"
args["deleteGB-4.0.0"] = "150"
args["deleteGB-4.0.1"] = "150"
args["deleteGB-4.0.2"] = "150"
args["deleteGB-4.1.0"] = "150"
args["balancemin-3.6.1"] = "2"
args["balancemin-3.7.1"] = "2"
args["balancemin-3.7.2"] = "2"
args["balancemin-4.0.0"] = "2"
args["balancemin-4.0.1"] = "2"
args["balancemin-4.0.2"] = "2"
args["balancemin-4.1.0"] = "2"
args["wait.crunch-3.6.1"] = "60"
args["wait.crunch-3.7.1"] = "60"
args["wait.crunch-3.7.2"] = "60"
args["wait.crunch-4.0.0"] = "60"
args["wait.crunch-4.0.1"] = "60"
args["wait.crunch-4.0.2"] = "60"
args["wait.crunch-4.1.0"] = "60"

# # client stuff
# avcfg = {"hfsaddr": "HFSADDR_REPLACE_HERE.avamar.com",
#         "id": "root",
#         "pswd": "8RttoTriz",
#         "path": "/clients/HFSADDR_REPLACE_HERE.avamar.com"}

# mccli_cfg = {
#        #"version" : "3.5.0-420",
#        "domain": "/clients",
#        "mcsaddr": "dpe58",
#        "mcsuserid": "root",
#        "mcspasswd": "8RttoTriz",
#        }

# mccli_xml = True

# mccli_client_cfg = {
#        "activated" : "false",
#        "contact" : "false",
#        "recursive" : "false",
#        "retired" : "false",
#        "verbose" : "true",
#        "plugin" : "1001",
#        "encryption" : "AES 128-bit",
#        "group-name" : "testgroup_mccli",
#        "dataset" : "Default Dataset",
#        "target" : "/tmp/work",
#        }

# mccli_group_cfg = {
#        "verbose" : "true",
#        "domain" : "/clients/",
#        "clients" : "false",
#        "enabled" : "false",
#        "recursive" : "false",
#        "retention" : "Default Retention",
#        "schedule" : "Default Schedule",
#        "dataset" : "pizza",
#        "new-domain" : "/clients/",
#        "old-group-name" : "Default Group",
#        "old-group-domain" : "/clients/",
#        "client-name" :"a1230.avamar.com",
#        "client-domain" : "/clients/",
#        }

# mccli_dataset_cfg = {
#        "verbose" : "true",
#        "recursive" : "false",
#        "plugin" : "1001",
#        "exclude" : "/tmp/blah",
#        "option" : "debug",
#        "value" : "true",
#        "include" : "/tmp",
#       "target" : "/tmp",
#        "new-name" : "REPLACEME",
#        "new-domain" : "/clients",
#        }
# QAPlugin-specific variables to be used in avagent-based testing

# unix_clients = ['qarhas3.avamar.com', 'vm-linux-15.avamar.com']
# win_clients = ['a1230.avamar.com']
# avscc_exe = "/usr/local/avamar/bin/avscc"
# avscc_var = "/usr/local/avamar/var/"
# qascript_xml_templ = "run_qascript_templ.xml"
# refresh_plugins_xml = "refresh_plugins.xml"
# dir_tree_to_send = "../../pylts"
# qascript_dest = "C:\\Program Files\\Avamar\\etc\\scripts"
# qascript_cmdline = "pylts\\lts.py"  # relative to QASCRIPT_DEST
# lts_args = "win_perm.gen_perm"
# lts_args = "gen_data.gen_data --create --toplevel --startdir=gendata"  
"""
class CILogger:
    """
    This class defines how to write log, two handlers are attached to logger, RotatingFileHandler writes log to a file, default log level is DEBUG
    StreamHandler writes log to console, default log level is INFO, you can call method 'enable_debug' to enable DEBUG log on console
    """
    def __init__(self,log_name,log_file_path):
        self.log_file_path=log_file_path
        self.logger = None
        self.config(log_name)
    def config(self,log_name):
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.DEBUG)
        self.fh = logging.handlers.RotatingFileHandler(self.log_file_path,mode='a', maxBytes=1024*1024*10, backupCount=10, encoding="utf-8")
        #Set file log level here
        self.fh.setLevel(logging.DEBUG)
        self.ch = logging.StreamHandler()
        #Set console log level here
        self.ch.setLevel(logging.DEBUG)    
        formatter = logging.Formatter("%(asctime)s *%(levelname)s* : %(message)s",'%Y-%m-%d %H:%M:%S')  
        self.ch.setFormatter(formatter)
        self.fh.setFormatter(formatter)
        self.logger.addHandler(self.ch)  
        self.logger.addHandler(self.fh)
    
    def get_logger(self):
        return self.logger

log=CILogger("server smoke","run_lts.log")
LOG=log.get_logger()
class RemoteShell:
    """
    Run command/download/upload via SSH
    """
    def __init__(self,host,username,password,port=22):
        self.host=host
        self.username=username
        self.password=password
        self.port=port
        self.ssh=paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.host, username=self.username, password=self.password, port=port,look_for_keys=False, allow_agent=False)
        
    def run_command_ssh(self,cmd,nohup=False,redirect_file="/dev/null"):
        """
        Run command via ssh
        @param cmd: Command to run
        @param nohup: Run command in background
        @param redirect_file: Redirect command stdout/stderr to a file when usning nohup
        """
        result={}
        try:
            if nohup:
                cmd="nohup %s >> %s 2>&1 &"%(cmd,redirect_file)
            LOG.debug("Run command \"%s\" on remote machine \"%s\""%(cmd,self.host))
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            channel = stdout.channel
            status = channel.recv_exit_status()
            error= stderr.read()
            out= stdout.read()
            result["stderr"]=error
            result["stdout"]=out
            result["status"]=status
        except Exception,e:
            LOG.error(str(e))
        LOG.debug(str(result))
        return result
    
    def upload_file_ssh(self,from_file,to_file):
        """
        Upload file via SSH
        @param from_file: Local file path
        @param to_file: Remote file path
        """
        try:
            t=paramiko.Transport((self.host,self.port)) 
            t.connect(username=self.username,password=self.password) 
            sftp=paramiko.SFTPClient.from_transport(t)
            LOG.debug("Upload local file \"%s\" to remote machine \"%s\", path \"%s\""%
            (from_file,self.host,to_file))
            sftp.put(from_file,to_file)
            return True
        except Exception,e:
            LOG.error(str(e))
            return False
     
    def download_file_ssh(self,from_file,to_file):
        """
        Doanload file via SSH
        @param from_file: Remote file path
        @param to_file: Local file path
        """
        try:
            t=paramiko.Transport((self.host,self.port)) 
            t.connect(username=self.username,password=self.password) 
            sftp=paramiko.SFTPClient.from_transport(t)
            LOG.debug("Download file \"%s\" from remote machine \"%s\",to local path \"%s\""%
            (from_file,self.host,to_file))
            sftp.get(from_file,to_file)
            return True
        except Exception,e:
            LOG.error(str(e))
            return False
    def close(self):
        self.ssh.close()

class runLTS:
    """
    This class defines some functions for running LTS, like install qts, enable root, collect test log
    """
    def __init__(self,target_host,admin_user_name,admin_user_password,root_user_password,ssh_port=22):
        """
        Check if not root enabled, enable it
        @param target_host: Target host to run pylts
        @param admin_user_name: admin user for target host, default is 'admin'
        @param admin_user_password: admin user's password
        @param root_user_password: root user's password
        @param ssh_port: ssh port
        """
        self.host=target_host
        self.ssh_port=ssh_port
        #If root not enabled, enable root access since install pylts/lts need root permission
        if not self.__is_root_enabled(self.host, root_user_password,self.ssh_port):
            LOG.info("Active root login for target server \"%s\""%self.host)
            res=self.__avtive_root(self.host,admin_user_name,admin_user_password,root_user_password,self.ssh_port)
            if not res:
                LOG.error("Failed to active root login for target server \"%s\""%self.host)
                sys.exit(1)
        self.username="root"
        self.password=root_user_password
        self.remote_qts_path="/tmp/qts.rpm"
        self.remote_pylts_output_file=None
        self.local_pylts_output_file=None
        self.remote_pylts_result_json=None
        self.local_pylts_result_json=None
        
    def __is_root_enabled(self,host,root_password,port):
        """
        Check is root enabled
        @param host: Host name
        @param root_password: root password
        @param port: ssh port
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username="root", password=root_password, port=port,look_for_keys=False, allow_agent=False)
            return True
        except:
            return False
    
    def __avtive_root(self,host,no_root_user,no_root_user_password,root_password,port,active=1):
        """
        Active/deavtive root login by change file /etc/ssh/sshd_config, update entry 'PermitRootLogin yes/no'
        @param host: Host name
        @param no_root_user: non-root user, before enable root, this user will be temporarily used
        @param no_root_user_password: non-root user's password
        @param root_password: root password
        @param port: ssh port
        @param active: If active==1, enable root, else disable root
        """
        if active==1:
            cmd="echo '%s' | su - root -c \"echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config&&service sshd restart\""%root_password
        else:
            cmd="echo '%s' | su - root -c \"echo 'PermitRootLogin no' >> /etc/ssh/sshd_config&&service sshd restart\""%root_password
        try:
            remote_shell=RemoteShell(host,no_root_user,no_root_user_password,port)
            res=remote_shell.run_command_ssh(cmd)
            if res and res.has_key("status") and res["status"]==0:
                return True
        except Exception,e:
            LOG.error(str(e))
        return False
    
    def __create_pylts_config_file(self,tag=None):
        """
        Create pylts config file
        """
        pylts_root="/home/admin/pylts"
        username = "admin"
        remote_shell=RemoteShell(self.host,self.username,self.password,port=self.ssh_port)
        res=remote_shell.run_command_ssh("hostname")
        if res and res.has_key("status") and res["status"]==0:
            hostname=res["stdout"].strip()
            short_hostname = hostname.split(".")[0]
            config_path="%s/config/%s_%s" % (pylts_root,username, hostname)
#             res=remote_shell.run_command_ssh("ls %s"%config_path)
#             if res and res.has_key("status") and res["status"]==0:
#                 LOG.info("Config file '%s' already exit, no need to create"%config_path)
#                 return True
#             else:
            workingDir = "/data01/work"
            restoreDir = "/data01/restore"
            remoteFolder = "/qadepot"
            file_content=""
            for line in CONFIG_TEMPLATE.split("\n"):
                if re.search("HFSADDR_REPLACE_HERE", line):
                    file_content+= line.replace("HFSADDR_REPLACE_HERE", short_hostname)+"\n"
                elif re.search("WORKINGDIR_REPLACE_HERE", line):
                    out = "/data01/work" if re.search("\s+", workingDir) or workingDir == '' else workingDir
                    file_content+= line.replace("WORKINGDIR_REPLACE_HERE", out)+"\n"
                elif re.search("RESTOREDIR_REPLACE_HERE", line):
                    out = "/data01/restore" if re.search("\s+", restoreDir) or restoreDir == '' else restoreDir
                    file_content+= line.replace("RESTOREDIR_REPLACE_HERE", out)+"\n"
                elif re.search("REMOTEFOLDER_REPLACE_HERE", line):
                    out = "/qadepot/" if re.search("\s+", remoteFolder) or remoteFolder == '' else remoteFolder
                    file_content+= line.replace("REMOTEFOLDER_REPLACE_HERE", out)+"\n"
                elif re.search("EMAIL_REPLACE_HERE", line):
                    file_content+= line.replace("EMAIL_REPLACE_HERE", "")+"\n"
                elif re.search("TAG_REPLACE_HERE", line):
                    if tag:
                        file_content+= line.replace("TAG_REPLACE_HERE", tag)+"\n"
                    else:
                        file_content+= line.replace("TAG_REPLACE_HERE", "")+"\n"
                else:
                    file_content+= line+"\n"
            temp_file=str(int(time.time()*1000))+".tmp"
            f=open(temp_file,"w")
            f.write(file_content)
            f.close()
            if remote_shell.upload_file_ssh(temp_file, config_path):
                LOG.info("Successfully created config file '%s'"%config_path)
                os.remove(temp_file)
                return True
            else:
                os.remove(temp_file)
                return False
        else:
            return False
    
    def install_qts(self,qts_rpm_path,tag=None):
        """
        Install qts rpm
        @param qts_rpm_path: qts rpm in local path
        """
        try:
            remote_shell=RemoteShell(self.host,self.username,self.password,port=self.ssh_port)
            #Step 1, config search domain, this is need to let test case connect to qahome/dudepot
            cmd= "sed -i 's/search.*/search datadomain.com asl.lab.emc.com/g' /etc/resolv.conf"
            res=remote_shell.run_command_ssh(cmd)
            if res and res.has_key("status") and res["status"]==0:
                pass
            else:
                LOG.error("Failed to config search domain")
                remote_shell.close()
                return False
            #Step 2, copy qts.rpm to remote machine and install
            LOG.info("Copying qts.rpm to remote machine %s"%self.host)
            res= remote_shell.upload_file_ssh(qts_rpm_path,self.remote_qts_path)
            #Remove qts rpm no matter uploaded successfully or not
            try:
                os.remove(qts_rpm_path)
            except:
                pass
            if not res:
                LOG.error("Failed to copy qts.rpm to remote server")
                remote_shell.close()
                return False
            #Step 3, install qts.rpm
            LOG.info("Installing qts rpm")
            cmd="rpm -ivh --replacepkgs --force %s&&rm -rf %s"%(self.remote_qts_path,self.remote_qts_path)
            res=remote_shell.run_command_ssh(cmd)
            if res and res.has_key("status") and res["status"]==0:
                pass
            else:
                LOG.error("Failed to install qts.rpm on remote server")
                remote_shell.close()
                return False
            #Step 4, update python link
            LOG.info("Updating python link")
            cmd="cd /usr/bin && unlink python;ln -s /opt/ActivePython-2.7.5.6/bin/python /usr/bin/python"
            res=remote_shell.run_command_ssh(cmd)
            if res and res.has_key("status") and res["status"]==0:
                pass
            else:
                LOG.error("Failed to update python link on remote server")
                remote_shell.close()
                return False
            #Step 5. create config file if not exist
            self.__create_pylts_config_file(tag)
            #Step 6, run env setup script, which will install CLP license, 
            #configure password less login with admin/root from utility node to storage node
            cmd="su - admin -l -c '/usr/bin/sh /home/admin/pylts/env-setup.sh --password=%s'"%self.password
            res=remote_shell.run_command_ssh(cmd)
            if res and res.has_key("status") and res["status"]==0:
                pass
            else:
                LOG.error("Failed to run env-setup.sh")
                remote_shell.close()
                return False
            #Step 7, gen lts config file
            lts_home="/home/admin/lts"
            if tag:
                cmd="""su - admin -c '[ ! -s $HOME/.lts ] && %s/bin/lts.pl --email=${EMAILADDR:-$USER@localhost} || cat $HOME/.lts';
            su - admin -c 'grep mcs_password  $HOME/.lts || echo "mcs_password = %s" >> $HOME/.lts; echo "tag = %s" >> $HOME/.lts';"""%\
                (lts_home,self.password,tag)
            else:
                cmd="""su - admin -c '[ ! -s $HOME/.lts ] && %s/bin/lts.pl --email=${EMAILADDR:-$USER@localhost} || cat $HOME/.lts';
            su - admin -c 'grep mcs_password  $HOME/.lts || echo "mcs_password = %s" >> $HOME/.lts'; """%(lts_home,self.password)
            res=remote_shell.run_command_ssh(cmd)
            if res and res.has_key("status") and res["status"]==0:
                pass
            else:
                LOG.error("Failed to generate lts config file")
                remote_shell.close()
                return False
            #Step 8, gen lts password file
            #Wait for qts environment ready
            time.sleep(120)
            cmd="""su - admin -l -c 'cd /home/admin/lts/tools;perl gen_password_file.pl --user=root --password=%s'"""%self.password
            res=remote_shell.run_command_ssh(cmd)
#             if res and res.has_key("status") and res["status"]==0:
#                 pass
#             else:
#                 LOG.error("Failed to generate lts password file")
#                 remote_shell.close()
#                 return False
            remote_shell.close()
        except Exception,e:
            LOG.error(str(e))
            return False
        return True
    


    def run_pylts(self,scenario_path_list,component=None,test_type=None,test_case_type=None,project=None,upload_to_dashboard=False,resume_on_error=True):
        """
        Run pylts on remote machine and wait it exit
        @param scenario_path_list: scenario file path, it's list type
        @param component: Component to run pylts, it will be included in output json
        @param test_type: Test types for running pylts, valid values are "daily", "weekly", "smoke","ete"
        @param test_case_type: Test case types for running pylts, valid values are "legacy", "new"
        @param project: Avamar release for running pylts
        @param upload_to_dashboard: Upload test result to qa dashboard
        @param resume_on_error: Run all test case even if have failures
        """
        cmd="service avfirewall stop;su admin -l -c \"cd /home/admin/pylts;ssh-agent bash -c 'ssh-add /home/admin/.ssh/dpnid;python run_scenario.py "
        output_json="/tmp/"+str(int(time.time()*1000))+"_output.json"
        cmd+="--output-file=%s "%output_json
        self.remote_pylts_result_json=output_json
        if component:
            cmd+="--component=%s "%component
        if test_type:
            cmd+="--test-type=%s "%test_type
        if test_case_type:
            cmd+="--test-case-type=%s "%test_case_type
        if project:
            cmd+="--project=%s "%project
        if upload_to_dashboard:
            cmd+="--upload-to-dashboard "
        if resume_on_error:
            cmd+="--resume-on-error "
        cmd+=" ".join(scenario_path_list)
        cmd+="'\""
        pylts_out="/tmp/"+str(int(time.time()*1000))+"_pylts.out"
        self.remote_pylts_output_file=pylts_out
        LOG.info("start to run pylts, you can login to '%s' and use command 'tail -f %s' to monitor progress"%(self.host,self.remote_pylts_output_file))
        remote_shell=RemoteShell(self.host,self.username,self.password,port=self.ssh_port)
        remote_shell.run_command_ssh(cmd+" >%s  2>&1"%self.remote_pylts_output_file)
        remote_shell.close()
        
    def collect_test_result(self):
        """
        Collect run_scemarios.py stdout/stderr and result
        """
        remote_shell=RemoteShell(self.host,self.username,self.password,port=self.ssh_port)
        if platform.system()=="Linux":
            local_pylts_output_file=os.path.join("/tmp",str(int(time.time()*1000))+".out")
        elif platform.system()=="Windows":
            local_pylts_output_file=os.path.join(r"c:\tmp",str(int(time.time()*1000))+".out")
        self.local_pylts_output_file=local_pylts_output_file
        remote_shell.download_file_ssh(self.remote_pylts_output_file,local_pylts_output_file)
        pylts_output=open(local_pylts_output_file,"r").read()
        LOG.info("====================Pylts output====================")
        LOG.debug(pylts_output)
        LOG.info("================End of pylts output=================")
        if platform.system()=="Linux":
            local_result_file=os.path.join("/tmp",str(int(time.time()*1000))+".json")
        elif platform.system()=="Windows":
            local_result_file=os.path.join(r"c:\tmp",str(int(time.time()*1000))+".json")
        self.local_pylts_result_json=local_result_file
        remote_shell.download_file_ssh(self.remote_pylts_result_json,local_result_file)
        result=open(local_result_file,"r").read()
        LOG.info("====================Test result=====================")
        LOG.debug(result)
        LOG.info("================End of test result==================")
        remote_shell.close()
        return True

    def cleanup(self):
        """
        Cleanup test environment
        1. Delete remote output file and uninstall qts rpm
        2. Delete local temp file
        """
        LOG.info("==============Cleanup test environment==============")
        remote_shell=RemoteShell(self.host,self.username,self.password,port=self.ssh_port)
        #Delete remote output file and uninstall qts rpm
        cmd="rm -rf %s;rm -rf %s;rpm -e qts"%(self.remote_pylts_output_file,self.remote_pylts_result_json)
        remote_shell.run_command_ssh(cmd)
        remote_shell.close()
        #Delete local temp file
        try:
            os.remove(self.local_pylts_output_file)
            os.remove(self.local_pylts_result_json)
        except:
            pass

    def check_test_result(self,result_json):
        """
        Check if there are test failures
        @param result_json: result json which generated by run_scenario.py
        """
        data=json.loads(result_json)
        test_result=data["test_result"]
        passed_num=0
        failed_num=0
        for sce,res in test_result.items():
            for tc in res:
                if tc["test_result"]=="PASSED":
                    passed_num+=1
                elif tc["test_result"]=="FAILED":
                    failed_num+=1
        LOG.info("===================Test summarize===================")
        LOG.info("Passed test case number: %d"%passed_num)
        LOG.info("Failed test case number: %d"%failed_num)
        if failed_num>0:
            return False
        else:
            return True

def send_mail(mail_to,hostname,return_code):
    """
    Send email notification to the specified receiver
    @param mail_to: email receiver
    @param hostname: Test machine hostname
    @param return_code: pylts return code
    """
    mail_from="Avamar-QA <Avamar.Qa@emc.com>"
    result="passed"
    if return_code!=0:
        result="failed"
    title="Your test %s on server \"%s\""%(result,hostname)
    msg = MIMEMultipart()
    msg['Subject'] = Header(title, 'utf-8')
    msg['From'] = mail_from
    msg['To']=",".join(mail_to)
    body = MIMEText("","html")
    msg.attach(body)
    if mail_to:
        try:
            smtp = smtplib.SMTP()
            smtp.connect("mailhubwc.lss.emc.com")
            smtp.sendmail(mail_from, mail_to, msg.as_string())
            smtp.quit()
        except Exception,e:
            LOG.error(str(e))

def download(doanload_link,local_dir):
    """
    Download file from url
    @param doanload_link: Download link
    @param param: Local download directory
    """
    try:
        if not os.path.isdir(local_dir):
            os.makedirs(local_dir)
        local_file_name=doanload_link.split("/")[-1]
        local_file_path=os.path.join(local_dir, local_file_name)
        LOG.info("Downloading '%s' to local path '%s'" % (doanload_link,local_file_path))
        res= urllib2.urlopen(doanload_link)
        f = open(local_file_path, 'wb')
        meta = res.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        LOG.debug("bytes: '%s'"%file_size)
        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = res.read(block_sz)
            if not buffer:
                break
            file_size_dl += len(buffer)
            f.write(buffer)
            status=r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8)*(len(status)+1)
#             print status+"\r",
        f.close()
        return local_file_path
    except Exception,e:
        LOG.error(str(e))
        return ""

def main():
    OpParser = OptionParser() 
    OpParser.add_option("-t", "--hostname", action="store", 
                  dest="hostname", 
                  help="Specify the remote machine hostname")

    OpParser.add_option("-u", "--username", action="store",
                  dest="username",
                  help="Specify the remote machine username")
    OpParser.add_option("-p", "--password", action="store",
                  dest="password",
                  help="Specify the remote machine password")
    OpParser.add_option("-r", "--root-password", action="store",
                  dest="root_password",
                  help="Specify the root password")
    OpParser.add_option("-U", "--upload-to-dashboard", action="store_true",
                  dest="upload_to_dashboard",default=False,
                  help="Upload test result to dashboard")
    OpParser.add_option("-i", "--install-qts", action="store_true",
                  dest="install_qts",default=False,
                  help="Install qts remotely")
    OpParser.add_option("-q", "--qts-rpm", action="store",
                  dest="qts_rpm",default="",
                  help="Speficy qts rpm package")
    OpParser.add_option("-T", "--test-type", action="store",type="choice",
                  choices=["daily", "weekly", "smoke","ete"],
                  dest="test_type",
                  help="Test type for upload API, currently suport 'daily','weekly','smoke','ete'")
    OpParser.add_option("-c", "--test-case-type", action="store",type="choice",
                  choices=["legacy", "new"],
                  dest="test_case_type",
                  help="Test case type for upload API, currently support 'legacy','new'")
    OpParser.add_option("-C", "--component", action="store",type="choice",
                  choices=["server","platform","security","workflow","mc","client","proxy","dpe","vcp"],
                  dest="component",
                  help="Test type for upload API, currently suport 'daily','weekly','smoke','ete'")
    OpParser.add_option("-P", "--project", action="store",
                  dest="project",default="",
                  help="Project name for upload API")
    OpParser.add_option("-d", "--detail-link", action="store",
                  dest="detail_link",default="",
                  help="Specify the testcase detail link")
    OpParser.add_option("-s", "--scenario-files", action="store",
                  dest="scenario_files",
                  help="pylts test scenarios, use ; to separate each scenario file")
    OpParser.add_option("-E", "--cleanup", action="store_true",
                  dest="cleanup",default=False,
                  help="Cleanup test environment on remote machine")
    OpParser.add_option("-e", "--email-receiver", action="store",
                  dest="email_receiver",default="",
                  help="Specify the email receiver for the test result notification, use ; to separate each receiver")
    OpParser.add_option("-a", "--tag", action="store",
                  dest="tag",default="",
                  help="Specify test case tag, which will be used to upload test result to qahome")
    options = OpParser.parse_args()[0]
    hostname= options.hostname
    username= options.username
    password= options.password
    root_password=options.root_password
    upload_to_dashboard= options.upload_to_dashboard
    install_qts=options.install_qts
    test_type= options.test_type
    test_case_type=options.test_case_type
    component=options.component
    project= options.project
    detail_link= options.detail_link
    cleanup=options.cleanup
    tag=options.tag
    scenario_files=[]
    if options.scenario_files:
        scenario_files=options.scenario_files.split(";")
    email_receiver=[]
    if options.email_receiver:
        email_receiver=options.email_receiver.split(";")
    #qts rpm can be local file or http link
    qts_local_rpm=""
    qts_rpm=options.qts_rpm
    if qts_rpm and qts_rpm.startswith("http"):
        if platform.system()=="Linux":
            res=download(qts_rpm,os.path.join("/tmp",str(int(time.time()*1000))))
            if res:
                qts_local_rpm=res
            else:
                sys.exit(1)
        elif platform.system()=="Windows":
            res=download(qts_rpm,os.path.join(r"c:\tmp",str(int(time.time()*1000))))
            if res:
                qts_local_rpm=res
            else:
                sys.exit(1)
    else:
        qts_local_rpm=qts_rpm
    if not hostname or not username or not password or not root_password:
        print "run 'python run_pylts_remotely.py -h' to get help"
        sys.exit(1)
    runner=runLTS(hostname,username,password,root_password)
    #Install pylts and lts on remote machine
    if install_qts: 
        if qts_local_rpm:
            if runner.install_qts(qts_local_rpm,tag):
                LOG.info("Finished...")
            else:
                sys.exit(1)
        else:
            print "If want to install qts,\nparameter '-q --qts-rpm' is required "
            sys.exit(1)
    #Run test case
    if scenario_files:
        return_code=0
        runner.run_pylts(scenario_files, component=component, test_type=test_type, test_case_type=test_case_type,
                          project=project, upload_to_dashboard=upload_to_dashboard)
        #Collect test log and result
        runner.collect_test_result()
        result_json=""
        if os.path.isfile(runner.local_pylts_result_json):
            result_json=open(runner.local_pylts_result_json,"r").read()
        #Check is there any test case failed, if yes, return code is 1, else return 0
        if result_json:
            if not runner.check_test_result(result_json):
                return_code=1
        #If email receiver is specified, send notification mail to them for test result
        if email_receiver:
            send_mail(email_receiver,hostname,return_code)
        #Cleanup test environment
        if cleanup:
            runner.cleanup()
        sys.exit(return_code)
    else:
        #Nothing to do, exit
        sys.exit(0)
        
if __name__=="__main__":
    main()
    

