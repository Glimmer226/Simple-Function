'''
Created on May 26, 2016

@author: chenj62
'''

import sys
import json
import multiprocessing
import subprocess
import os
import signal
import re
import commands
import paramiko
import time
import urllib2
import getopt
import requests
from fabric.api import *
from fabric.tasks import execute
from subprocess import Popen, PIPE
from install_lib import *
from logger import DriverNodeLogger
log_halder=DriverNodeLogger("drivernode","driver_node.log")
LOG=log_halder.getLogger()

termColor = {'red': '\033[1;31m',
             'cyan': '\033[36m',
             'lightcyan': '\033[1;36m',
             'blue': '\033[1;34m',
             'green': '\033[1;32m',
             'cyan_underline' : '\033[4;36m',
             'off' : '\033[0m'}
env.user = 'root'
env.password = 'Chang3M3Now.'
env.disable_known_hosts = True
path_repo_package="/data01/avamar/repo/packages/"
support_keys = {'18.0.0':' Supp0rtLab8',
                '7.5.0': 'Supp0rtLag6',
                '7.5.1': 'Supp0rtLag6',
                '7.4.1': 'Supp0rtKen10',
		'7.4.0': 'Supp0rtKen10',
                '7.3.0': 'Supp0rtJul6',
                '7.2.1': 'Supp0rtHarV1',
                '7.2.0': 'Supp0rtHarV1'}

class testRunner():
    
    def __init__(self,conf_file):
        try:
            with open(conf_file) as test_conf:
                self.conf = json.load(test_conf)
            
            #print self.conf
            #print self.conf["tests"]
            
        except Exception as err:
            #exception_trace_str = get_exception_stack()
            LOG.error("Error: %s", err)
    

    
    
    def get_install_info(self, index):
        host= self.conf["tests"][index]['hostname']          
        
        test_info = self.conf["tests"][index]     
        if re.search("\w*-\w*",host):
            install_info = {        
                "install_iso":"yes",
		"install_osrollup":"yes",
                "vip":self.conf["vip"],
                "vu":self.conf["vu"],
                "vp":self.conf["vp"],
                "ds":self.conf["ds"],
                "net":self.conf["net"],
                "esxi":self.conf["esxi"],
				"kmippackage":self.conf["kmippackage"],
				"kmipversion":self.conf["kmipversion"],
				"kmiptitle":self.conf["kmiptitle"],
				"kmipyaml":self.conf["kmipyaml"],
                "sip":self.conf["tests"][index]["sip"],
                "smask":self.conf["tests"][index]["smask"],
                "gateway":self.conf["tests"][index]["gateway"],
                "dns":self.conf["tests"][index]["dns"],
                "ntp":self.conf["tests"][index]["ntp"],
                "smask":self.conf["tests"][index]["smask"],
                "domain":self.conf["tests"][index]["domain"],
                "yaml":self.conf["tests"][index]["yaml"],
                "key":self.conf["tests"][index]["key"],
                "hostname":self.conf["tests"][index]["hostname"],
                "build":self.conf["tests"][index]["build"]
            
            }
        else:
            install_info = {
                        
                "install_iso":"yes",
                "build":self.conf["tests"][index]["build"],
                "lab":self.conf["tests"][index]["lab"],
                "configuration":self.conf["tests"][index]["configuration"],
                "osversion":self.conf["tests"][index]["osversion"],
                "kspasswd":self.conf["tests"][index]["kspasswd"],
                "ispasswd":self.conf["tests"][index]["ispasswd"],
                "domain":self.conf["tests"][index]["domain"],
                "yaml":self.conf["tests"][index]["yaml"],
                "key":self.conf["tests"][index]["key"],
                "hostname":self.conf["tests"][index]["hostname"],
                "shorthostname":self.conf["tests"][index]["shorthostname"]
        }
            
            
            
        if "install" in test_info:
            cust_install_info = test_info["install"]
            for k in install_info:
                if k in cust_install_info:
                    install_info[k]=cust_install_info[k]
        self.conf["tests"][index]["install"]=install_info
        
        
        return install_info
	
    def deploy_ave(self,idx):
        
        ave_install_info = self.get_install_info(idx)
        build = ave_install_info["build"]

       #latest_build=self.get_latest_ave_build(build)
        latest_build=parseArgs().get('version')
        if not latest_build:
            return None
        LOG.debug ( "latest build=%s" %(latest_build) )
            
        sname=ave_install_info['hostname'].split('.')[0]
        command="autodeploy -vip " + ave_install_info['vip'] + " -vu " + "\""+ave_install_info['vu'] +"\""+ " -vp " + ave_install_info['vp'] + " -esxi " +"\""+ave_install_info['esxi']+"\"" \
                +" -ds " + "\""+ave_install_info['ds']+"\"" + " -net " + "\"" +ave_install_info['net'] +"\"" + " -a forceinstall "  + " -sip " + ave_install_info['sip'] \
                +" -smask " + ave_install_info['smask'] + " -sname " + sname + " -g "+ ave_install_info['gateway']+ " -dns " + ave_install_info['dns'] + " -ntp " + ave_install_info['ntp'] \
                +" -domain " + ave_install_info['domain'] + " -b " + latest_build + " -yaml " + ave_install_info['yaml'] + " -key " + ave_install_info['key'] + " -root True "
            
            
        print command

        return self.execute_deploy(command)

    def kick_start(self,idx):
        """
        ssh-agent bash -c 'ssh-add /home/admin/.ssh/dpnid; python kickstart.py -l durham -m asl -c 2.6 -v v30 -p changeme a4dpe824'
        """
        ads_install_info = self.get_install_info(idx)
        command="ssh-agent bash -c 'ssh-add /home/admin/.ssh/dpnid;python kickstart.py -l " + ads_install_info['lab'] + " -m " + ads_install_info['domain'] + " -c " + ads_install_info['configuration'] + " -v " + ads_install_info['osversion'] + " -p " + ads_install_info['kspasswd'] + " " + ads_install_info['shorthostname'] + "\'"
        print command
        return self.execute_deploy ( command  )

    def deploy_avp(self,idx):
        
	
        #latest_build=self.conf["avp_version"]
	
        #if not latest_build:
        #    return None
        #LOG.debug ( "latest build=%s" %(latest_build) )
        avp_install_info = self.get_install_info(idx)
        build = avp_install_info['build']
        latest_build = self.get_latest_avp_build(build)
        if not latest_build:
	        return None
        command="ssh-agent bash -c 'ssh-add /home/admin/.ssh/dpnid;python auto-install.py -s " + avp_install_info['shorthostname'] + " -l " + avp_install_info['lab']  + " -v " + latest_build + " -p " + avp_install_info['ispasswd'] + " -y " + avp_install_info['yaml'] + "\'"
	print command
        return self.execute_deploy ( command  )
    def get_latest_avp_build(self,build):
        
        #command="ls /qadepot/builds/v%s*/PACKAGES/AvamarBundle_SLES11_64*|grep -v md5sum|awk -F '/' '{print $6}'|awk -F '-' '{print $2\"-\"$3}'|sed s'/.zip//g'|sort  -nr|head -n 1" %(build)
        command="ls /qadepot/builds/v%s*/PACKAGES/AvamarBundle_SLES11_64*|grep -v md5sum|awk -F '/' '{print $NF}'|awk -F '-' '{print $2\"-\"$3}'|sed s'/.zip//g'|sort -k 2 -t '-'  -nr|head -n 1" %(build)
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        stdout,stderr = p.communicate()
        if p.returncode != 0 or stderr :
            LOG.error( "Excute %s  failed with stderr %s" %( command, stderr) )
            LOG.error( "Please check build or /qadepot is correct")
            return None
        else:
            return stdout.strip('\n')
    def get_latest_ave_build(self,build):
        """
        Get the latest build version of AVE
        """
        command="ls -d /qadepot/builds/v%s*/AVE|awk -F/ '{print $4}'|sed 's/[a-z]//g'|sed 's#/##g'|sort -V|tail -n 1" %(build)
        #/qadepot/builds/v7.4.0.32/AVE/HARMONY_VMWARE_COPY_IN_PROGRESS
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        stdout,stderr = p.communicate()
        if p.returncode != 0 or stderr :
            LOG.error( "Excute %s  failed with stderr %s" %( command, stderr) )
            LOG.error( "Please check build or /qadepot is correct")
            return None
        return stdout.strip('\n')
    def execute_deploy(self,command):
        """
        Execute avautod command to deploy AVE and monitor the status
        Todo: Add logging here
        """
        LOG.debug( "do_deploy: %s" %(command) )
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT )    
        while True:
            try:
                s = p.stdout.readline()
            except SystemExit:
                os.kill(p.pid, signal.SIGTERM)
            except KeyboardInterrupt:
                LOG.warning( "Capture Ctrl+C ,terminaled by user")
                os.kill(p.pid, signal.SIGINT)
            #except:
            except Exception,e:
                os.kill(p.pid, signal.SIGKILL)
            if ( s == "" ):break
            try:
                #sys.stdout.write(s)
                #sys.stdout.flush()
                LOG.info(s)
            except:
                os.kill(p.pid, signal.SIGKILL)
        ret = p.wait()
        return ret   
    @parallel   
    def put_file(self,local_file,remote_file):
	    put(local_file,remote_file)
    @parallel
    def run_command(self,cmd):
	    return run(cmd,pty=False)
	#if run(cmd).succeeded:
	#    return True
	#else:
	#    return False
    @parallel
    def get_file(self,remote_file,local_file):
	    get(remote_file,local_file)	    
    
	
    def install(self,index):
        
        test_info = self.conf["tests"][index]
        install_info = self.get_install_info(index)
        if not install_info["install_iso"] == "yes":
            LOG.info("Skipped to install Avamr for host %s.", install_info["hostname"])
            return 1
        
        
        if re.search("\w*-\w*",install_info["hostname"]):
            #Install AVE
            ret = self.deploy_ave(index)
	    return ret
        else:
            kt_ret = self.kick_start(index)
            print "kick_start return status"
            print kt_ret
            if kt_ret  == 0:
                
                it_ret = self.deploy_avp(index)
                #it_ret = 0
		print "deploy phsycial result"
		return it_ret
 	    else:
                return 1
					

    def run_test(self, index):
        test_info = self.conf["tests"][index]
        #Comments there for testing
        install_status = self.install(index)
        if install_status == 0:
             if re.search("\w*-\w*",test_info["hostname"]):
                 execute_cmd_1 ="cd /opt/robot;robot -t akm_installation testcase/akm/akm.robot"
	         execute_cmd_2 ="cd /home/ci/;python run_pylts_remotely.py --hostname=%s --username=admin --password=Chang3M3Now. --root-password=Chang3M3Now. --qts-rpm=http://dudepot.asl.lab.emc.com/repo/QA/qts-0-28.noarch.rpm  --install-qts --scenario-files=\"/home/admin/pylts/scenarios/single/avmaint_base;/home/admin/pylts/scenarios/single/avmaint_config;/home/admin/pylts/scenarios/single/avmaint_sched;/home/admin/pylts/scenarios/single/avmgr_scenario;/home/admin/pylts/scenarios/single/dpnutils_ave;/home/admin/pylts/scenarios/single/avmgr_overlap\"  --tag=proj:KMIP --component=server --test-type=daily --test-case-type=legacy --project=labrador --upload-to-dashboard" %(test_info["hostname"])
                 out_1=os.system(execute_cmd_1)
                 out_2=os.system(execute_cmd_2)
                 print out_1
                 print out_2
               #/home/admin/pylts/scenarios/single/avmaint_base 
               #--component=security --test-type=daily --test-case-type=legacy --project=rooster --upload-to-dashboard
	       #/home/admin/pylts/scenarios/single/avmgr_overlap	
		
        
        
    def run(self):
        tests = self.conf["tests"]
        processes =[]
        for idx in range(0,len(tests)):
           
            process = multiprocessing.Process(target=self.run_test,
                                                 args=(idx,))
            process.start()
            processes.append(process)
                
        for process in processes:
                process.join()

    
def parseArgs():
    
        
    ptionDict = dict(project=None,config=None,version=None)
    try:
        options,args = getopt.getopt(sys.argv[1:],"hc:p:v:",["help","project=","config=","version="])
        print len(args)
        for o, a in options:
            if o in ("-h","--help"):
                print "help"
                sys.exit()
            elif o in ("-p","--project"):
                ptionDict['project']=a
            elif o in ("-c","--config"):
                ptionDict['config']=a
            elif o in ("-v","--version"):
                ptionDict['version']=a
            else:
                assert False, "Unhandled option"
            
            #assert len(args) >= 2, "Must provide scenario name and project name as argument"
        assert ptionDict['config'], "Must provide a configure file with -c"
        assert ptionDict['project'], "Must provide a project name with -p"
        assert ptionDict['version'], "Must provide a version name with -v"
    except AssertionError, err:
        usageError(str(err))
    except getopt.GetoptError, err:
        usageError(str(err))
    return ptionDict
    
def usage():
    print """Name
    testRunner.py
Synopsis
    python testRunner.py [-hcp] --config=xxx --project=xxxx... --version=$rooster_version
Description
    
    
    -p PROJECT, --project=PROJECT
        Provide the release branch for running regression test cases currently support julian, kensington
    -c CONFIG, --config=CONFIG
        Provide the testRunner configuration information
    -v VERSION, --version=VERSION
        Provide the testRunner version
    -h , --help
        Display this help and exit
Example
    python testRunner.py --config=julianConfig.json --project=juliansp1 --verison=$rooster_version
"""
def usageError(msg="", code=1):
    printError(msg) 
    usage()
    sys.exit(code)

def printTestPassResult(msg):
    ISOTIMEFORMAT='%Y-%m-%d %X'
    sys.stdout.write("\n" + termColor['green'] + time.strftime( ISOTIMEFORMAT, time.gmtime( time.time() ) ) + " " + msg + termColor['off'] + "\n")
    sys.stdout.flush()

def printTestFailResult(msg):
    sys.stdout.write("\n" + termColor['red'] + msg + termColor['off'] + "\n")
    sys.stdout.flush()

def printError(msg):
    sys.stdout.write("\n" + termColor['red'] + msg + termColor['off'] + "\n")
    sys.stdout.flush()
    
def main():
    #config_file="testConfig.json"
    config_file = parseArgs().get('config')
    runner = testRunner(config_file)
    runner.run()
   
if __name__ == "__main__":
    sys.exit(main())
   
   
