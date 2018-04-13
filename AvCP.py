#!/usr/bin/env python
#encoding=utf-8
"""
authur: james.wen2@emc.com
"""
import time
from lib.base.SSHConnection import SSHConnection
from lib.base.RobotSSHConnection import *
from lib.base.RobotLogger import LOG
from lib.server.AvServer import AvServer
from lib.server.avmaint.AvCheckPoint import AvCheckPoint

class  AvCP( AvServer ):
    '''
    Class for wrap checkpoint related commands
    '''
    def __init__(self,ssh=None):
        
        super(self.__class__, self).__init__(ssh)
        self.ssh=ssh
        self.__classname=self.__class__.__name__
    
    def get_latest_cp_attribute( self,attribute ):
        '''
        Get the lastest check point attribute. call command "avmaint cpstatus"
        @attribute: String,The attribute to be searched
        @output:    String,The value of the attribute
        '''
        try:
            cp=AvCheckPoint(self.ssh)
            cpstatus=cp.cpstatus()
        except Exception, e:
            LOG.error("%s: Failed to get cpstatus:%s" %(self.__classname,str(e)))
            return False
        for name,value in vars(cpstatus).items():
            #print "name=%s value=%s" %(name,value)
            if ( name == attribute ):
                return value
        LOG.error("Invalid attribute name for check point :%s" %(attribute))
        return False
    def get_latest_cp_name(self):
        '''
        Get the latest check point name. call command "avmaint cpstatus"
        @output:    String;The value of the latest checkpoint name
        '''
        return self.get_latest_cp_attribute("tag")
    def get_latest_cp_tag(self):
        '''
        Get the latest check point name. call command "avmaint cpstatus"
        @output:    String;The value of the latest checkpoint name
        '''
        return self.get_latest_cp_name()
    def get_latest_cp_status(self):
        '''
        Get the latest check point status. call command "avmaint cpstatus"
        @output:    String;The value of the latest checkpoint status
        '''
        return self.get_latest_cp_attribute("status")
    def get_latest_cp_result(self):
        '''
        Get the latest check point result. call command "avmaint cpstatus"
        @output:    String,The value of the latest checkpoint result
        '''
        return self.get_latest_cp_attribute("result")

    def _get_all_status( self ):
        '''
        Private function.
        Get the all of check point information. call command "avmaint lscp"
        @output:    False or List; Wrapper of all the checkpoint information
        '''
        self.__cpobjs=[]
        try:
            cp=AvCheckPoint(self.ssh)
            cpobjs=cp.lscp()
        except Exception, e:
            LOG.error("%s: Failed to get all check points" %(self.__classname,str(e)))
            return False
        return cpobjs;
    def get_all_cp_name(self):
        '''
        Get the all of check point name. call command "avmaint lscp"
        @output:    False or Tuple; The Tuple contained all the check point name
        '''
        cplist=[]
        cpobjs=self._get_all_status()
        if cpobjs == False:
            return False
        for cpobj in cpobjs:
            cplist.append(cpobj.tag)
        return tuple(cplist)
    def get_cp_attribute( self,cp_name,attribute):
        '''
        Get the attribute value  of the specific check point. call command "avmaint lscp"
        @cp_name:    String;The checkpoint name to be search
        @attribute:      String;The attribute name of the specific check point.
        @output:    String or False; The attribute value of the specific check point
        '''
        cpobjs = self._get_all_status()
        if ( cpobjs == False ): return False
        for cpobj in cpobjs:
            LOG.info("cpobj.tag:%s" %(cpobj.tag))
            if ( cpobj.tag == cp_name ):
                for name,value in vars(cpobj).items():
                    LOG.info("name=%s value=%s" %(name,value))
                    if ( name == attribute ): return value
        LOG.warn("%s: Failed to get checkpoint:%s attribute %s" %(self.__classname,cp_name,attribute ))
        return False
    def get_cp_hfscheck_attribute(self, cp_name,hfscheck_attr):
        '''
        Get the hfscheck attribute while checkpoint creating.
        @cp_name:   String;The check point need to be get attribute.
        @hfscheck_attr:String;The attribute in hfscheck part
        @output:Boolean;True if succeed
        '''
        hfscheck_obj=self.get_cp_attribute(cp_name,'hfscheck_obj')
        if ( hfscheck_obj == False ): return False
        for name,value in vars(hfscheck_obj).items():
            #print "name=%s value=%s" %(name,value)
            if ( name == hfscheck_attr ): return value
        LOG.warn("%s: Failed to get checkpoint:%s attribute %s" %(self.__classname,cp_name,attr ))
        return False

    def create_checkpoint( self,wait_to_completed=True, timeout=36000,interval=30 ):
        '''
        Create checkpoint,call command avmaint --ava checkpoint
        @wait_to_completed:    Bool;Wait check point to be completed
        @timeout:   Integer;Seconds to be wait for completion
        @interval:  Integer;Seconds for each try
        @output:    String or False; The attribute value of the specific check point
        '''
        #LOG.info("create_checkpoint, wait_to_completed=%s" %(wait_to_completed))
           

        try:
            cp=AvCheckPoint(self.ssh)
            cp_name=cp.create_checkpoint(wait_to_completed,timeout,interval)
        except Exception, e:
            LOG.error("%s: Failed to create check points:%s" %(self.__classname ,str(e)))
            return False
        return cp_name;

    def remove_checkpoint(self,cp_name,force=False):
        '''
        Remove checkpoint,call command avmaint --ava rmcp [ --risklosingallbackups ]
        @cp_name:    String;The check point name to be removed
        @force:     Bool;Whether to Remove check point forcibly
        @output:    Bool;
        '''
        try:
            cp=AvCheckPoint(self.ssh)
            result=cp.remove_checkpoint(cp_name,force)
        except Exception, e:
            LOG.error("%s: Failed to remove check points" %(self.__classname,str(e)))
            return False
        return result;

    def lockcp(self,cp_name):
        '''
        lock checkpoint
        @cp_name:   String;The check point need to be locked.
        @output:Boolean;True if succeed
        '''
        try:
            cp=AvCheckPoint(self.ssh)
            result=cp.lockcp(cp_name)
        except Exception, e:
            LOG.error("%s: Failed to lockcp check points:%s" %(self.__classname,cp_name,str(e)))
            return False
        return result;

    def unlockcp(self,cp_name):
        '''
        unlock checkpoint
        @cp_name:   String;The check point need to be locked.
        @output:Boolean;True if succeed
        '''
        try:
            cp=AvCheckPoint(self.ssh)
            result=cp.unlockcp(cp_name)
        except Exception ,e:
            LOG.error("%s: Failed to unlock check points:%s" %(self.__classname,cp_name ,str(e)))
            return False
        return result;

if __name__=="__main__":
    import sys
    from lib.base.RobotSSHConnection import ssh_connect_to,ssh_disconnect,ssh_run_command

    hostname="a4dpe828.asl.lab.emc.com"
    #hostname="A4T81D7.datadomain.com"
    username="admin"
    password="Chang3M3Now."
    ssh = ssh_connect_to(hostname,username,password,port=22,timeout=60,prompt="")

    print "aaaaaaaaaaaaaaaaa"
    cpobj=AvCP()
    #cpobj._avserver_attach_ssh(ssh)
    cpobj._avserver_attach_ssh_static(ssh)
    LOG.enable_console_log()
    LOG.info("===============Create checkpoint==============")
    cp_name=cpobj.create_checkpoint()
    LOG.info("%s created" %(cp_name))
    
    os.exit(1)


    result=cpobj.get_latest_cp_name()
    LOG.info("get_latest_cp_name is %s" %(result))

    result=cpobj.get_latest_cp_tag()
    LOG.info("get_latest_cp_name is %s" %(result))

    result=cpobj.get_latest_cp_status()
    LOG.info("get_latest_cp_status is %s" %(result))

    result=cpobj.get_latest_cp_result()
    LOG.info("get_latest_cp_result is %s" %(result))

    result=cpobj.get_latest_cp_attribute("end-time")
    LOG.info("get_latest_cp_attribute end-time is %s" %(result))

    result=cpobj.get_latest_cp_attribute("negative-testing")
    LOG.info("get_latest_cp_attribute negative-testing is %s" %(result))

    LOG.info("===============List all checkpoint==============")
    attrs=('isvalid','deletable','complete','negative-testing','hfsctime','hfscheck')
    cps=cpobj.get_all_cp_name()
    if cps == False:
        print "cps is False"
        sys.exit(1)
    for cp in cps:
        for attr in attrs:
            value=cpobj.get_cp_attribute(cp,attr)
            LOG.info("get_cp_attribute checkpoint:%s attr=%s value=%s" %(cp ,attr,value))
        for attr in ('nodestarttime','errors','validcheck','type','negative-testing'):
            value=cpobj.get_cp_hfscheck_attribute(cp,attr)
            LOG.info("get_cp_hfscheck_attribute checkpoint:%s attr=%s value=%s" %(cp ,attr,value))

    LOG.info("===============Lock/Unlock==============")
    cpname=cpobj.get_latest_cp_name()
    result=cpobj.lockcp(cpname)
    LOG.info("lock %s result is %s" %(cpname ,result))
    result=cpobj.unlockcp(cpname)
    LOG.info("unlock %s result is %s" %(cpname ,result))
    cpname="negative-testing"
    result=cpobj.lockcp(cpname)
    LOG.info("lock %s result is %s" %(cpname ,result))

    LOG.info("===============Remove all checkpoint==============")
    cps=cpobj.get_all_cp_name()
    for cp in cps:
        result=cpobj.remove_checkpoint(cp,force=True)
        LOG.info("remove checkpoint %s result=%s" %(cp,result))
    result=cpobj.remove_checkpoint('negative-testing',force=True)
    LOG.info("remove negative-testing %s result=%s" %(cp,result))
