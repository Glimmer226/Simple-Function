#!/usr/bin/env python
#encoding=utf-8
"""
authur: kevin.zou@emc.com
"""
import os
import re
import sys
import json
import urllib2
import paramiko
import time
import datetime
import platform
import logging
import logging.handlers
import zipfile
from optparse import OptionParser
from robot.run import run
from xml.dom import minidom
VALID_TEST_TYPES=["daily","ete","weekly","smoke"]
VALID_TEST_CASE_TYPES=["legacy","new"]
VALID_COMPONENTS=["server","platform","security","workflow","mc","client","proxy","dpe","vcp"]
VALID_CLOUD_TYPE=["aws","azure"]
VALID_ROBOT_LOG_LEVEL=["TRACE","DEBUG","INFO","WARN","ERROR","NONE"]
LOG_FILE_NAME="robot_run.log"
UPLOAD_ROBOT_HTML_API = "http://ciweb228-123.asl.lab.emc.com/web/app.php/core/ci/upload/%s/"
UPLOAD_RESULT_JSON_API = "http://ciweb228-123.asl.lab.emc.com/web/app.php/core/ci/upload/"
UPLOAD_TO_CLOUD_API="http://34.196.240.52/web/app.php/ci/cloud/upload/"
class Logger:
    """
    This class defines how to write log, two handlers are attached to logger, RotatingFileHandler writes log to a file, default log level is DEBUG
    StreamHandler writes log to console, default log level is INFO, you can call method 'enable_debug' to enable DEBUG log on console
    """
    def __init__(self,log_name,log_file_name):
        self.log_file_path=log_file_name
        self.logger = None
        self.config(log_name)
    def config(self,log_name):
        """
        Set log handler and format, in this case, log will be write to console and rotated file
        @param log_name: logger name
        """
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.DEBUG)
        self.fh = logging.handlers.RotatingFileHandler(self.log_file_path,mode='a', maxBytes=1024*1024*10, backupCount=10, encoding="utf-8")
        self.fh.setLevel(logging.DEBUG)
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.INFO)    
        formatter = logging.Formatter("%(asctime)s *%(levelname)s* : %(message)s",'%Y-%m-%d %H:%M:%S')  
        self.ch.setFormatter(formatter)
        self.fh.setFormatter(formatter)
        self.logger.addHandler(self.ch)  
        self.logger.addHandler(self.fh)
    
    def get_logger(self):
        return self.logger
    
    def enable_debug(self):
        self.fh.setLevel(logging.DEBUG)
        self.ch.setLevel(logging.DEBUG)
#logger instance created here    
logger=Logger("install_logger",LOG_FILE_NAME)
LOG= logger.get_logger()

class remoteShell:
    """
    This class provides ssh related methods
    """
    def __init__(self,host,username,password=None,key=None,port=22):
        self.host=host
        self.username=username
        self.password=password
        self.port=port
        self.key=key
        self.ssh = paramiko.SSHClient()
#         paramiko.util.log_to_file("paramiko.log", logging.DEBUG)
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        LOG.debug("Initialize ssh connection to '%s'"%self.host)
        if not self.key and self.password:
            self.ssh.connect(host, username=username, password=password, look_for_keys=False, allow_agent=False)
        else:
            if os.path.isfile(self.key):
                key=paramiko.RSAKey.from_private_key_file(self.key)
                self.ssh.connect(self.host,username =self.username,pkey=key)
    
    def run_command(self,cmd):
        """
        Run ssh command
        @param cmd: Command to run
        """
        result={}
        try:
            LOG.debug("Running command: '%s'"%cmd)
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            channel = stdout.channel
            status = channel.recv_exit_status()
            error= stderr.read()
            out= stdout.read()
            result["stderr"]=error
            if result["stderr"]:
                LOG.error("stderr: %s"%result["stderr"])
            result["stdout"]=out
            LOG.debug("stdout: %s"%result["stdout"])
            result["status"]=status
            LOG.debug("return status: %s"%result["status"])
        except Exception,e:
            LOG.error(str(e))
        return result
    
    def close(self):
        """
        Close ssh connection
        """
        self.ssh.close()
    

class TestRunner:
    def __init__(self):
        self.upload_to_qahome=False
        self.qahome_user=None
        self.qahome_tag=None
        self.upload_to_dashboard=False
        self.upload_to_cloud_dashboard=False
        self.robot_root_directory=None
        self.active_password_authentication=False
        self.disable_password_authentication_after_finish=False
        self.cloud_type=""
        self.component=""
        self.test_type=""
        self.project=""
        self.test_case_type=""
        self.robot_testcase_names=[]
        self.include_tags=[]
        self.robot_scenarios=[]
        self.robot_run_options={}
        #Reserved robot parameters, those parameters will be passed to robot environment via robot.run
        self.avamar_server_hostname=""
        self.avamar_server_username=""
        self.avamar_server_password=""
        self.avamar_admin_key=""
        self.avamar_support_key=""
        self.robot_log_level="INFO"
        self.datadomains=[]
        self.clients=[]
        self.replication_servers=[]
        self.migration_servers=[]
    
    def check_config(self,config_file):
        """
        Check the legality of configuration file
        @param config_file: config file path
        """
        with open(config_file,"r") as config_f:
            content_json= json.load(config_f)
        #parameter 'robot_root_directory' is required
        assert content_json.has_key("robot_root_directory"), "Parameter 'robot_root_directory' is required"
        #parameter 'upload_to_qahome' is optional, if no defined, the default value is no
        if content_json.has_key("upload_to_qahome"):
            upload_to_qahome=content_json["upload_to_qahome"]
            assert upload_to_qahome.has_key("upload"), "Sub_parameter 'upload' is required for 'upload_to_qahome'"
            assert upload_to_qahome["upload"] in ["yes","no"], "the value of 'upload' should be 'yes/no'"
            assert upload_to_qahome.has_key("qahome_user"), "Sub_parameter 'qahome_user' is required for 'upload_to_qahome'"
            assert upload_to_qahome.has_key("tag"), "Sub_parameter 'tag' is required for 'upload_to_qahome'"
        #parameter 'upload_to_dashboard' is optional, if no defined, the default value is no    
        if content_json.has_key("upload_to_dashboard"):
            upload_to_dashboard=content_json["upload_to_dashboard"]
            assert upload_to_dashboard in ["yes","no"], "The value of 'upload_to_dashboard' must be 'yes/no'"
        #parameter 'upload_to_cloud_dashboard' is optional, if no defined, the default value is no    
        if content_json.has_key("upload_to_cloud_dashboard"):
            upload_to_cloud_dashboard=content_json["upload_to_cloud_dashboard"]
            assert upload_to_cloud_dashboard.has_key("upload"), "Sub_parameter 'upload' is required for 'upload_to_cloud_dashboard'"
            assert upload_to_cloud_dashboard["upload"] in ["yes","no"], "the value of 'upload' should be 'yes/no'"
            assert upload_to_cloud_dashboard.has_key("cloud_type"), "Sub_parameter 'cloud_type' is required for 'upload_to_cloud_dashboard'"
        #parameter 'component' is optional
        if content_json.has_key("component"):
            assert content_json["component"] in VALID_COMPONENTS, "component must be in '%s'"%",".join(VALID_COMPONENTS)
        #parameter 'tags' is optional
        if content_json.has_key("tags"):
            assert isinstance(content_json["tags"],list), "The value of 'tags' should be list type"
        #parameter 'test_type' is optional
        if content_json.has_key("test_type"):
            assert content_json["test_type"] in VALID_TEST_TYPES, "test_type must be in '%s'"%",".join(VALID_TEST_TYPES)
        #parameter 'test_case_type' is optional
        if content_json.has_key("test_case_type"):
            assert content_json["test_case_type"] in VALID_TEST_CASE_TYPES, "test_case_type must be in '%s'"%",".join(VALID_TEST_CASE_TYPES)
        #parameter 'test_cases' is optional
        if content_json.has_key("test_cases"):
            assert isinstance(content_json["test_cases"],list), "The value of 'test_cases' should be list type"
        #parameter 'active_password_authentication' is needed if you are running test on cloud AVE
        if content_json.has_key("active_password_authentication"):
            assert content_json["active_password_authentication"] in ["yes","no"], "the value of 'active_password_authentication' should be 'yes/no'"
        #parameter 'disable_password_authentication_after_finish' is optional if you are running test on cloud AVE
        if content_json.has_key("disable_password_authentication_after_finish"):
            assert content_json["disable_password_authentication_after_finish"] in ["yes","no"], "the value of 'disable_password_authentication_after_finish' should be 'yes/no'"
        #parameter "robot_log_level" is optional, the default level is "INFO", 
        #it will set the robot log level, messages below the level will not be logged 
        if content_json.has_key("robot_log_level"):
            assert content_json["robot_log_level"] in VALID_ROBOT_LOG_LEVEL, "robot_log_level must be in '%s'"%",".join(VALID_ROBOT_LOG_LEVEL)
        #parameter 'scenarios' is required
        assert content_json.has_key("scenarios"), "Parameter 'scenarios' is required"
        assert isinstance(content_json["scenarios"],list), "The value of 'scenarios' should be list type"
        #parameter 'target_machines' is required
        assert content_json.has_key("target_machines"), "Parameter 'target_machines' is required"
        target_machines=content_json["target_machines"]
        #Other sub_parameters are optional
        for machine_category,machine_details in target_machines.items():
            assert machine_category in ["avamar_server","datadomains","clients","replication_servers","migration_servers"], \
            "parameter '%s' is not valid"%machine_category
            if machine_category=="avamar_server":
                assert machine_details.has_key("hostname"), "Sub_parameter 'hostname' is required for '%s'"%machine_category
                assert machine_details.has_key("username"), "Sub_parameter 'username' is required for '%s'"%machine_category
                assert machine_details.has_key("password"), "Sub_parameter 'password' is required for '%s'"%machine_category
                if machine_details.has_key("admin_key"):
                    admin_key_path=machine_details["admin_key"]
                    assert os.path.isfile(admin_key_path), "The admin_key \"%s\" that you specified is not existed"%admin_key_path
            else:
                assert isinstance(machine_details, list), "The value of '%s' should be list type"%machine_category
                for machine in machine_details:
                    assert machine.has_key("hostname"), "Sub_parameter 'hostname' is required for '%s'"%machine
                    assert machine.has_key("username"), "Sub_parameter 'username' is required for '%s'"%machine
                    assert machine.has_key("password"), "Sub_parameter 'password' is required for '%s'"%machine
                    if machine.has_key("admin_key"):
                        admin_key_path=machine["admin_key"]
                        assert os.path.isfile(admin_key_path), "The admin_key \"%s\" that you specified is not existed"%admin_key_path
    def load_config(self,config_file):
        """
        Load config file to attributes
        @param config_file: config file path
        """
        with open(config_file,"r") as config_f:
            content_json= json.load(config_f)
        if content_json.has_key("upload_to_qahome"):
            upload_to_qahome=content_json["upload_to_qahome"]
            upload=upload_to_qahome["upload"]
            if upload.lower()=='yes':
                self.upload_to_qahome=True
                self.qahome_user=upload_to_qahome["qahome_user"]
                self.qahome_tag=upload_to_qahome["tag"]
            else:
                self.upload_to_qahome=False
        if content_json.has_key("upload_to_dashboard"):
            upload_to_dashboard=content_json["upload_to_dashboard"]
            if upload_to_dashboard.lower()=="yes":
                self.upload_to_dashboard=True
        if content_json.has_key("upload_to_cloud_dashboard"):
            upload_to_cloud_dashboard=content_json["upload_to_cloud_dashboard"]
            upload=upload_to_cloud_dashboard["upload"]
            if upload.lower()=='yes':
                self.upload_to_cloud_dashboard=True
                self.cloud_type=upload_to_cloud_dashboard["cloud_type"]
        if content_json.has_key("test_type"):
            self.test_type=content_json["test_type"]
        if content_json.has_key("project"):
            self.project=content_json["project"]
        if content_json.has_key("test_case_type"):
            self.test_case_type=content_json["test_case_type"]
        if content_json.has_key("component"):
            self.component=content_json["component"]
        self.robot_root_directory=content_json["robot_root_directory"]
        if content_json.has_key("tags"):
            self.include_tags=content_json["tags"]
        if content_json.has_key("test_cases"):
            self.robot_testcase_names=content_json["test_cases"]
        if content_json.has_key("active_password_authentication"):
            active_password_authentication=content_json["active_password_authentication"]
            if active_password_authentication.lower()=='yes':
                self.active_password_authentication=True
        if content_json.has_key("disable_password_authentication_after_finish"):
            disable_password_authentication_after_finish=content_json["disable_password_authentication_after_finish"]
            if disable_password_authentication_after_finish.lower()=='yes':
                self.disable_password_authentication_after_finish=True
        if content_json.has_key("robot_log_level"):
            self.robot_log_level=content_json["robot_log_level"]
        scenarios=content_json["scenarios"]
        self.robot_scenarios=scenarios
        target_machines=content_json["target_machines"]
        if target_machines.has_key("avamar_server"):
            self.avamar_server_hostname=target_machines["avamar_server"]["hostname"]
            self.avamar_server_username=target_machines["avamar_server"]["username"]
            self.avamar_server_password=target_machines["avamar_server"]["password"]
            if target_machines["avamar_server"].has_key("admin_key"):
                self.avamar_admin_key=target_machines["avamar_server"]["admin_key"]
            if target_machines["avamar_server"].has_key("support_key"):
                self.avamar_support_key=target_machines["avamar_server"]["support_key"]
        if target_machines.has_key("datadomains"):
            self.datadomains=target_machines["datadomains"]
        if target_machines.has_key("clients"):
            self.clients=target_machines["clients"]
        if target_machines.has_key("replication_servers"):
            self.replication_servers=target_machines["replication_servers"]
        if target_machines.has_key("migration_servers"):
            self.migration_servers=target_machines["migration_servers"]
    
    def gen_robot_variable(self):
        """
        Generate variable list which used by robot.run, those variable will overwrite the ones defined in the robot case
        """
        variable_list=[]
        variable_list.append("AVAMAR_SERVER_HOSTNAME:%s"%self.avamar_server_hostname)
        variable_list.append("AVAMAR_SERVER_USERNAME:%s"%self.avamar_server_username)
        variable_list.append("AVAMAR_SERVER_PASSWORD:%s"%self.avamar_server_password)
        if self.avamar_admin_key:
            variable_list.append("AVAMAR_SERVER_ADMIN_KEY:%s"%self.avamar_admin_key)
        if self.avamar_support_key:
            variable_list.append("AVAMAR_SERVER_SUPPORT_KEY:%s"%self.avamar_support_key)
        #Below variable are list, walk this list and then load to python variables
        for index in range(len(self.datadomains)):
            datadomain_host_variable_name="DATADOMAIN_SERVER%d_HOSTNAME"%(index+1)
            variable_list.append("%s:%s"%(datadomain_host_variable_name,self.datadomains[index]["hostname"]))
            datadomain_user_variable_name="DATADOMAIN_SERVER%d_USERNAME"%(index+1)
            variable_list.append("%s:%s"%(datadomain_user_variable_name,self.datadomains[index]["username"]))
            datadomain_passwd_variable_name="DATADOMAIN_SERVER%d_PASSWORD"%(index+1)
            variable_list.append("%s:%s"%(datadomain_passwd_variable_name,self.datadomains[index]["password"]))
        for index in range(len(self.clients)):
            client_host_variable_name="CLIENT%d_HOSTNAME"%(index+1)
            variable_list.append("%s:%s"%(client_host_variable_name,self.clients[index]["hostname"]))
            client_user_variable_name="CLIENT%d_USERNAME"%(index+1)
            variable_list.append("%s:%s"%(client_user_variable_name,self.clients[index]["username"]))
            client_passwd_variable_name="CLIENT%d_PASSWORD"%(index+1)
            variable_list.append("%s:%s"%(client_passwd_variable_name,self.clients[index]["password"]))
            #Client version is optional
            if self.clients[index].has_key("version"):
                client_version_variable_name="CLIENT%d_VERSION"%(index+1)
                variable_list.append("%s:%s"%(client_version_variable_name,self.clients[index]["version"]))
        for index in range(len(self.replication_servers)):
            replication_host_variable_name="REPLICATION_SERVER%d_HOSTNAME"%(index+1)
            variable_list.append("%s:%s"%(replication_host_variable_name,self.replication_servers[index]["hostname"]))
            replication_user_variable_name="REPLICATION_SERVER%d_USERNAME"%(index+1)
            variable_list.append("%s:%s"%(replication_user_variable_name,self.replication_servers[index]["username"]))
            replication_passwd_variable_name="REPLICATION_SERVER%d_PASSWORD"%(index+1)
            variable_list.append("%s:%s"%(replication_passwd_variable_name,self.replication_servers[index]["password"]))
            if self.replication_servers[index].has_key("admin_key"):
                replication_key_variable_name="REPLICATION_SERVER%d_ADMIN_KEY"%(index+1)
                variable_list.append("%s:%s"%(replication_key_variable_name,self.replication_servers[index]["admin_key"]))
        for index in range(len(self.migration_servers)):
            migration_host_variable_name="MIGRATION_SERVER%d_HOSTNAME"%(index+1)
            variable_list.append("%s:%s"%(migration_host_variable_name,self.migration_servers[index]["hostname"]))
            migration_user_variable_name="MIGRATION_SERVER%d_USERNAME"%(index+1)
            variable_list.append("%s:%s"%(migration_user_variable_name,self.migration_servers[index]["username"]))
            migration_passwd_variable_name="MIGRATION_SERVER%d_PASSWORD"%(index+1)
            variable_list.append("%s:%s"%(migration_passwd_variable_name,self.migration_servers[index]["password"]))
            if self.migration_servers[index].has_key("admin_key"):
                migration_key_variable_name="MIGRATION_SERVER%d_ADMIN_KEY"%(index+1)
                variable_list.append("%s:%s"%(migration_key_variable_name,self.migration_servers[index]["admin_key"]))
        return variable_list
    
    def __configure_pass_auth(self,host,user,private_key,root_password,active=True):
        """
        Active/disable password authentication, allow root login
        @param host: Target machine host name
        @param user: Target machine user name
        @param private_key: Target machine private key
        @param root_password: Target machine root password
        @param active: True for active, False for disable
        """
        if active:
            cmd="echo '%s' | su - root -c \"sed -i s'/^Match.*User.*Address/Match User noone Address/'g /etc/ssh/sshd_config;\
            sed -i s'/^PasswordAuthentication.*$/PasswordAuthentication yes/'g /etc/ssh/sshd_config;\
            sed -i s'/^ChallengeResponseAuthentication.*$/ChallengeResponseAuthentication yes/'g /etc/ssh/sshd_config;\
            echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config\
            &&service sshd restart\""%root_password
        else:
            cmd="echo '%s' | su - root -c \"sed -i s'/^Match.*User.*Address/Match User root Address/'g /etc/ssh/sshd_config;\
            sed -i s'/^PasswordAuthentication.*$/PasswordAuthentication no/'g /etc/ssh/sshd_config;\
            sed -i s'/^ChallengeResponseAuthentication.*$/ChallengeResponseAuthentication no/'g /etc/ssh/sshd_config;\
            sed -i 's/^PermitRootLogin.*yes//g' /etc/ssh/sshd_config&&service sshd restart\""%root_password
        try:
            remote_shell=remoteShell(host,user,key=private_key)
            res=remote_shell.run_command(cmd)
            if res and res.has_key("status") and res["status"]==0:
                return True
        except Exception,e:
            LOG.error(str(e))
        return False
    
    def configure_pass_auth_for_all(self,active=True):
        """
        Active/disable password authentication for all configure avamar machines, allow root login
        @param active: True for active, False for disable
        """
        if self.avamar_server_hostname and self.avamar_server_username and self.avamar_server_password and self.avamar_admin_key:
            if active:
                LOG.info("Active password authentication for server \"%s\""%self.avamar_server_hostname)
            else:
                LOG.info("Disable password authentication for server \"%s\""%self.avamar_server_hostname)
            self.__configure_pass_auth(self.avamar_server_hostname, self.avamar_server_username, 
                                       self.avamar_admin_key, self.avamar_server_password, active=active)
        if self.replication_servers:
            for repl_server in self.replication_servers:
                if repl_server.has_key("admin_key"):
                    admin_key=repl_server["admin_key"]
                    host=repl_server["hostname"]
                    user=repl_server["username"]
                    password=repl_server["password"]
                    if active:
                        LOG.info("Active password authentication for server \"%s\""%host)
                    else:
                        LOG.info("Disable password authentication for server \"%s\""%host)
                    self.__configure_pass_auth(host, user, admin_key, password, active=active)
        if self.migration_servers:
            for mig_server in self.migration_servers:
                if mig_server.has_key("admin_key"):
                    admin_key=mig_server["admin_key"]
                    host=mig_server["hostname"]
                    user=mig_server["username"]
                    password=mig_server["password"]
                    if active:
                        LOG.info("Active password authentication for server \"%s\""%host)
                    else:
                        LOG.info("Disable password authentication for server \"%s\""%host)
                    self.__configure_pass_auth(host, user, admin_key, password, active=active)
    
    def robot_result_parser(self,output_xml_path):
        """
        Dump robot output.xml to a json object
        @param output_xml_path: output xml path
        """
        out_obj={}
        if not os.path.isfile(output_xml_path):
            return out_obj
        try:
            doc = minidom.parse(output_xml_path)
        except Exception,e:
            LOG.error(str(e))
            return out_obj
        test_result={}
        for suite_tag in doc.getElementsByTagName("suite"):
            #If run a directory which contains many ".robot" file, the directory itself was the root "suite" tag, skip this tag if 
            #the "suite" tag has child tag "suite"
            if suite_tag.hasAttribute("source") and not suite_tag.getElementsByTagName("suite"):
                scenario_result=[]
                suite_file_path=suite_tag.getAttribute("source")
                suite_name=os.path.basename(suite_file_path)
                for test_tag in suite_tag.getElementsByTagName("test"):
                    if test_tag.hasAttribute("name"):
                        test_case_result={}
                        tc_id=""
                        duration="0"
                        result=""
                        testcase_name=test_tag.getAttribute("name")
                        test_case_result["tc_name"]= testcase_name
                        for test_child_tag in test_tag.childNodes:
                            if test_child_tag.nodeName=="doc":
                                tc_id_text= test_child_tag.childNodes[0].nodeValue
                                tc_id=re.search("tc_id:\s*(\d{1,})", tc_id_text).group(1)
                            elif test_child_tag.nodeName=="status":
                                if test_child_tag and test_child_tag.hasAttribute("starttime") and test_child_tag.hasAttribute("endtime") \
                                and test_child_tag.hasAttribute("status"):
                                    start_time=test_child_tag.getAttribute("starttime").split(".")[0]
                                    end_time=test_child_tag.getAttribute("endtime").split(".")[0]
                                    start_time_p=datetime.datetime.strptime(start_time, "%Y%m%d %H:%M:%S")
                                    end_time_p=datetime.datetime.strptime(end_time, "%Y%m%d %H:%M:%S")
                                    days_diff=(end_time_p-start_time_p).days
                                    seconds_diff=(end_time_p-start_time_p).seconds
                                    duration=days_diff*24*3600+seconds_diff
                                    result=test_child_tag.getAttribute("status")
                                    if result.lower()=="pass":
                                        result="PASSED"
                                    elif result.lower()=="fail":
                                        result="FAILED"
                        test_case_result["tc_id"]= tc_id
                        test_case_result["duration"]= str(duration)
                        test_case_result["test_result"]= result
                        test_case_result["tc_type"]= self.test_case_type
                        scenario_result.append(test_case_result)
                test_result[suite_name]=scenario_result
        out_obj["test_result"]=test_result
        #Add other parameter to result
        target_hostname,target_username,target_password,target_admin_key=self.__determin_test_target_machine()
        out_obj["host_name"]=target_hostname
        out_obj["component"]=self.component
        LOG.debug("Recognize target platform...")
        target_platform=self.get_test_target_platform(target_hostname,target_username,target_password,target_admin_key)
        LOG.debug("Target platform is: '%s'"%target_platform)
        out_obj["platform"]=target_platform
        LOG.debug("Recognize target Avamar version...")
        target_avamar_version=self.get_test_target_avamar_version(target_hostname,target_username,target_password,target_admin_key)
        LOG.debug("Target Avamar version is: '%s'"%target_avamar_version)
        out_obj["build_version"]=target_avamar_version
        out_obj["gsan_version"]=target_avamar_version
        out_obj["avtar_version"]=""
        out_obj["test_type"]=self.test_type
        out_obj["project"]=self.project
        out_obj["test_framework"]="robot"
        return out_obj
    
    def upload_result_to_dashboard(self,result_json):
        """
        Upload all robot test result to dashboard
        @param result_json: test result which generated by function 'robot_result_parser'
        """
        try:
            encoder= json.JSONEncoder()
            upload_data=encoder.encode(result_json)
            LOG.debug("Sending request to url '%s'"%UPLOAD_RESULT_JSON_API)
            LOG.debug("Upload data: %s"%upload_data)
            request = urllib2.Request(UPLOAD_RESULT_JSON_API)
            request.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(request,upload_data)
            code= response.code
            LOG.debug("Response code: %d"%code)
            result= response.read()
            LOG.debug("Response result: %s"%result)
            if code==200:
                result_json=json.loads(result)
                if result_json.has_key("Status") and result_json["Status"]=="Ok":
                    return True
        except Exception,e:
            LOG.error(str(e))
        return False
    
    def upload_result_to_cloud_dashboard(self,result_json):
        """
        Upload all robot test result to cloud dashboard
        @param result_json: test result which generated by function 'robot_result_parser'
        """
        passed_num=0
        failed_num=0
        upload_data={}
        upload_data["project"]= result_json["project"]
        upload_data["test_type"]= result_json["test_type"]
        upload_data["build_number"]=result_json["build_version"]
        upload_data["component"]=result_json["component"]
        upload_data["testbed"]=result_json["host_name"]
        upload_data["cloud_type"]=self.cloud_type
        result=result_json["test_result"]
        for scenario_result in result.values():
            for tc_result_list in scenario_result:
                tc_result=tc_result_list["test_result"]
                if tc_result.lower()=="passed":
                    passed_num+=1
                elif tc_result.lower()=="failed":
                    failed_num+=1
        summary={}
        summary["total_tc"]=passed_num+failed_num
        summary["pass"]=passed_num
        summary["fail"]=failed_num
        summary["detail_link"]=""
        upload_data["summary"]=summary
        encoder= json.JSONEncoder()
        upload_data=encoder.encode(upload_data)
        LOG.debug("Upload data format: %s"%str(upload_data))
        try:
            request = urllib2.Request(UPLOAD_TO_CLOUD_API)
            request.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(request,upload_data)
            code= response.code
            LOG.debug("Response code: %d"%code)
            result= response.read()
            LOG.debug("Response string: %s"%result)
            if code==200:
                result_json=json.loads(result)
                if result_json.has_key("Status") and result_json["Status"]=="Ok":
                    return True
            else:
                print result
        except Exception,e:
            print e
        return False
    def upload_robot_report_to_dashboard(self,upload_name,robot_report_html_path):
        """
        Upload robot report html to dashboard
        @param upload_name: Report name which will be stored in dashboard server
        @param robot_report_html_path: result html which generated by robot.run
        """
        try:
            with open(robot_report_html_path,"r") as f:
                data=f.read()
            api=UPLOAD_ROBOT_HTML_API%upload_name
            LOG.debug("Sending request to url '%s'"%api)
            request = urllib2.Request(api)
            response = urllib2.urlopen(request,data)
            code= response.code
            LOG.debug("Response code: %d"%code)
            result= response.read()
            LOG.debug("Response result: %s"%result)
            if code==200:
                result_json=json.loads(result)
                if result_json.has_key("Status") and result_json["Status"]=="Ok":
                    return True
        except Exception,e:
            LOG.error(str(e))
        return False
    
    def __upload_single_result_qahome(self,tc_id,test_result,client,server,user,build_ver,tag):
        """
        Upload test result to qahome for a specific tc id
        @param tc_id: Test case ID which defined in qahome
        @param test_result: test result, should be pass/fail
        @param client: test client
        @param server: test server
        @param user: qahome user
        @param build_ver: Avamar server build version
        @param tag: tag which defined in qahome
        """
        url = "http://qahome.avamar.com/server_test/add_result.php?tcID=%s&passfail=%s&client=%s&server=%s&user=%s&buildver=%s&test_duration=10&tag=%s&bugid=&" %\
            (tc_id,test_result,client,server,user,build_ver,tag)
        try:
            LOG.debug("Sending requst to '%s'"%url)
            response = urllib2.urlopen(url)
            code=response.code
#             message=response.read()
            LOG.debug("Response code: %d"%code)
#             LOG.debug("Response message: %s"%message)
            if code==200:
                return True
        except Exception, e:
            LOG.error(str(e))
        return False
    
    def upload_all_result_to_qahome(self,result_json):
        """
        Upload all robot test result to qahome
        @param result_json: test result which generated by function 'robot_result_parser'
        """
        build_ver=result_json["build_version"]
        host_name=result_json["host_name"]
        result=result_json["test_result"]
        for scenario, scenario_result in result.items():
            for tc_result in scenario_result:
                tc_id=tc_result["tc_id"]
                test_result=tc_result["test_result"]
                if test_result.lower()=="passed":
                    test_result="pass"
                elif test_result.lower()=="failed":
                    test_result="fail"
                if tc_id:
                    LOG.debug("Posting result for test case '%s', test result '%s'"%(tc_id,test_result))
                    res= self.__upload_single_result_qahome(tc_id,test_result,host_name,host_name,self.qahome_user,build_ver,self.qahome_tag)
                    if res:
                        LOG.debug("Successful")
                    else:
                        LOG.debug("failed")
        return None
    
    def get_test_target_platform(self,target_server_hostname,target_server_username,target_server_password,target_admin_key):
        """
        Get target machine platform name
        @param target_server_hostname: Target server hostname
        @param target_server_username: Target server username
        @param target_server_password: Target server password
        """
        command_check_list={"gen4":"cat /proc/cpuinfo  | grep -q 5504",
                            "gen4s":"sudo dmidecode | grep -q S2600G",
                            "gen4t":"/sbin/div_cli -r 2>/dev/null| grep -q GEN4T"}
        try:
            ssh_shell=remoteShell(target_server_hostname,target_server_username,target_server_password,target_admin_key)
            for avamar_type,cmd in command_check_list.items():
                res=ssh_shell.run_command(cmd)
                if res["status"]==0:
                    return avamar_type
            return "ave"
#             #If not physical machines, check whether it's AVE
#             ave_type_file="/usr/local/avamar/etc/node.cfg"
#             res=ssh_shell.run_command("ls %s"%ave_type_file)
#             #Check whether node.cfg exited
#             if res["status"]==0:
#                 res=ssh_shell.run_command("cat %s"%ave_type_file)
#                 if res["status"]==0:
#                     #Try to find AVE type
#                     node_type_content=res["stdout"]
#                     for line in node_type_content.split("\n"):
#                         if re.match("ave type=\s*(.*)", line):
#                             ave_type= re.search("ave type=\s*(.*)", line).group(1)
#                             return ave_type+" ave"
        except Exception,e:
            LOG.error(str(e))
        return ""
    
    def get_test_target_avamar_version(self,target_server_hostname,target_server_username,target_server_password,target_admin_key):
        """
        Get test Avamar server version
        @param target_server_hostname: Target server hostname
        @param target_server_username: Target server username
        @param target_server_password: Target server password
        """
        version=None
        try:
            ssh_shell=remoteShell(target_server_hostname,target_server_username,target_server_password,target_admin_key)
            res=ssh_shell.run_command("avtar --version")
            stdout=res["stdout"]
            version = re.search("version:\s*(\d{1,}.\d{1,}.\d{1,}-\d{1,})",stdout).group(1)
            version= version.replace("-",".")
            client_third_version=version.split(".")[2]
            server_third_version=str(int(client_third_version)-100)
            return version.replace(client_third_version,server_third_version)
        except Exception,e:
            LOG.error(str(e))
        return ""
    
    def __determin_test_target_machine(self):
        """
        Currently most of the test scenarios just need one Avamar server, for replication and migration, they need at least two 
        Avamar servers, just need to choose one Avamar server as the primary test target, whose version and platform will be uploaded
        to dashboard
        """
        if self.avamar_server_hostname:
            if self.avamar_server_password:
                return self.avamar_server_hostname,self.avamar_server_username,self.avamar_server_password,None
            elif self.avamar_admin_key:
                return self.avamar_server_hostname,self.avamar_server_username,None,self.avamar_admin_key
        if self.replication_servers:
            if self.replication_servers[0].has_key("password"):
                return self.replication_servers[0]["hostname"],self.replication_servers[0]["username"],self.replication_servers[0]["password"],None
            elif self.replication_servers[0].has_key("admin_key"):
                return self.replication_servers[0]["hostname"],self.replication_servers[0]["username"],None,self.replication_servers[0]["admin_key"]
        if self.migration_servers:
            if self.migration_servers[0].has_key("password"):
                return self.migration_servers[0]["hostname"],self.migration_servers[0]["username"],self.migration_servers[0]["password"],None
            elif self.migration_servers[0].has_key("admin_key"):
                return self.migration_servers[0]["hostname"],self.migration_servers[0]["username"],None,self.migration_servers[0]["admin_key"]
    def zip_files(self,target_file_list,zip_file_name):
        """
        Compress giving file list to a zip file
        @param target_file_list: Files that need to be zipped
        @param zip_file_name: ZIP file name
        """
        try:
            zfile = zipfile.ZipFile(zip_file_name,"a", compression=zipfile.ZIP_DEFLATED)
            for f in target_file_list:
                zfile.write(f,os.path.basename(f))
            return True
        except Exception,e:
            LOG.error(str(e))
        return ""
    
    def check_if_all_passed(self,result_json):
        """
        Check if all test case passed
        @param result_json: Result json which generated by function 'robot_result_parser'
        """
        return_value=True
        test_result=result_json["test_result"]
        for scenarios,tc_result in test_result.items():
            for tc in tc_result:
                if tc["test_result"]=="FAILED":
                    return_value=False
                    break
        return return_value
    
    def run_robot(self):
        """
        Run robot with parameters
        """
        #Add robot root directory to PYTHONPATH
        sys.path.append(self.robot_root_directory)
        if platform.system()=="Linux":
            output_dir=os.path.join("/tmp",str(int(time.time()*1000)))
        elif platform.system()=="Windows":
            output_dir=os.path.join(r"c:\tmp",str(int(time.time()*1000)))
        self.robot_run_options["outputdir"]=output_dir
        self.robot_run_options["variable"]=self.gen_robot_variable()
        if self.robot_testcase_names:
            self.robot_run_options["test"]=self.robot_testcase_names
        if self.include_tags:
            self.robot_run_options["include"]=self.include_tags
        self.robot_run_options["loglevel"]=self.robot_log_level
        res=run(*self.robot_scenarios,**self.robot_run_options)
        return res
    

def main():
    OpParser = OptionParser()
    OpParser.add_option("-c", "--config-file", action="store", type="str",
                    dest="config_file_path",
                    help="Specify configuration file path")
    OpParser.add_option("-d", "--debug", action="store_true", 
                    dest="debug_mode", 
                    default=False,
                    help="Enable debug log")
    options = OpParser.parse_args()[0]
    config_file= options.config_file_path
    debug_mode = options.debug_mode
#     config_file="input.json"
    if not config_file:
        sys.exit(1)
    if debug_mode:
        logger.enable_debug()
    test_runner=TestRunner()
    try:
        LOG.info("Checking config file: '%s'"%config_file)
        test_runner.check_config(config_file)
        LOG.info("Well formatted...")
    except ValueError,e:
        LOG.error("Your config file '%s' is not a well formatted json"%config_file)
        LOG.error(str(e))
        sys.exit(1)
    except AssertionError,e:
        LOG.error(str(e))
        sys.exit(1)
    LOG.info("Loading config file: '%s'"%config_file)
    test_runner.load_config(config_file)
    try:
        #Active password authentication for all configured Avamar machines
        if test_runner.active_password_authentication:
            test_runner.configure_pass_auth_for_all(active=True)
        LOG.info("Start to run robot test case")
        test_runner.run_robot()
        LOG.info("Robot run ended")
    except Exception,e:
        LOG.error(str(e))
        sys.exit(1)
    output_path=test_runner.robot_run_options["outputdir"]
    LOG.info("Output files was put to '%s'"%output_path)
    ouput_xml_path=os.path.join(output_path,"output.xml")
    LOG.info("Parse robot result from '%s'"%ouput_xml_path)
    test_result=test_runner.robot_result_parser(ouput_xml_path)
    LOG.debug("Result json:\n %s"%test_result)
    if test_runner.upload_to_qahome:
        LOG.info("Uploading test result to qahome")
        test_runner.upload_all_result_to_qahome(test_result)
    if test_runner.upload_to_dashboard:
        LOG.info("Uploading test result to dashboard")
        #Upload robot output files
        time_now=time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
        robot_log_upload_name="robot_%s.log"%time_now
        robot_log_path=os.path.join(output_path,"log.html")
        robot_outout_upload_name="robot_%s.output"%time_now    
        robot_report_upload_name="robot_%s.report"%time_now
        robot_report_path=os.path.join(output_path,"report.html")
        test_result["log_file"]=robot_report_upload_name
        LOG.info("Uploading '%s' to dashboard server"%robot_log_path)
        test_runner.upload_robot_report_to_dashboard(robot_log_upload_name,robot_log_path)
        LOG.info("Uploading '%s' to dashboard server"%ouput_xml_path)
        test_runner.upload_robot_report_to_dashboard(robot_outout_upload_name,ouput_xml_path)
        LOG.info("Uploading '%s' to dashboard server"%robot_report_path)
        test_runner.upload_robot_report_to_dashboard(robot_report_upload_name,robot_report_path)
        LOG.info("Uploading result json to dashboard server")
        test_runner.upload_result_to_dashboard(test_result)
    if test_runner.upload_to_cloud_dashboard:
        LOG.info("Uploading test result to cloud dashboard server")
        test_runner.upload_result_to_cloud_dashboard(test_result)
    #Disable password authentication for all configured Avamar machines
    if test_runner.disable_password_authentication_after_finish:
        test_runner.configure_pass_auth_for_all(active=False)
    if not test_runner.check_if_all_passed(test_result):
        sys.exit(1)
    sys.exit(0)
    
if __name__=="__main__":
    main()
#     test_runner=TestRunner()
#     test_runner.robot_result_parser("output.xml")
#     test_runner.load_config("input.json")
#     test_runner.gen_robot_variable()
