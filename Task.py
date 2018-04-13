#!/usr/bin/env python
#encoding=utf-8
"""
authur: james.wen2@emc.com
"""
import time
import importlib
import sys
from types import *
from lib.server.AvCP import AvCP
from lib.server.AvHfs import AvHfs
from lib.server.AvGC import AvGC
from lib.client.DataGen import DataGen
from lib.client.Avtar import Avtar
from lib.client.LinuxClientRegister import LinuxClientRegister
from lib.base.RobotLogger import LOG
from lib.base.RobotSSHConnection import *

class  Task():
    '''
    Class for task, called by taskgroup
    '''
    def __init__(self):
        self.__classname=self.__class__.__name__
        self.__current_class=None
        self.__current_classname=None
        self.__current_instance=None
        '''
        [
        ['add_class',class_name,(),{},cls_instance,result],
        ['add_method',method_name,(),{},cls_instance,result],
        ..]
        '''
        self.__ops=[]
    def add_ops(self,op,object_name,*args,**kwargs ):
        '''
        Add operation for task, called by taskgroup class
        '''
        if op != "add_class" and op != "add_method" and op != "ssh_reconn":
            raise Exception , "Invalid op:%s ,should be add_class or add_method" %(op)
        if type(object_name) == StringType:
            LOG.info("Add operation %s:%s" %(op,object_name))
        else:
            LOG.info("Add operation %s" %(op))
        oplist=(op,object_name,args,kwargs,None,None)
        self.__ops.append(oplist)
        return True

    def print_ops(self):
        '''
        Print all operationis for task
        '''
        for i in xrange(len(self.__ops)):
            LOG.info("self.__ops[%d]:%s" %(i,self.__ops[i]))
    def init_call_class ( self,class_name,*args,**kwargs):
        '''
        Initialize the class specified by the class_name and arguments
        @class_name:    String,The class name
        @output:        object,The instance with the specified class
        '''
        #module = importlib.import_module()
        self.__current_classname = class_name
        self.__current_class = getattr(sys.modules[__name__], class_name)
        self.__current_instance = self.__current_class(*args,**kwargs)
        return self.__current_instance

    def call_instance_method ( self,instance,method,*args,**kwargs ):
        '''
        Call the method specified by install and method name with the specified arguments
        @instance:    The instance object
        @method:      String ,The method name in the instance object
        @output:      The output returned by the method
        '''
        clsname=self.__current_classname
        result=False
        try:
            func=getattr(instance, method,False)
            if func:
                result=func(*args,**kwargs)
            else:
                LOG.error("No method:%s for class:%s" %(method, clsname))

            LOG.info("Start method successfuly:%s, result=%s" %(method,result))
        except Exception,e:
            LOG.error("%s:Execute %s.%s %s %s failed with exception" \
                %(self.__classname,clsname,method,args,kwargs));
            LOG.error(str(e))
            return False
        return result
    def execute_ops(self):
        '''
        Execute the operation list in the task,called by execute_task
        @output:  The output returned by the last method
        '''
        result=False
        try:
            for index in xrange(len(self.__ops)):
                oplist=self.__ops[index]
                (op,object_name,args,kwargs,l_instance,l_result)= oplist
                result=False

                if op == "ssh_reconn":
                    LOG.info("Executing task: ssh reconnecting")
                    ssh=object_name
                    ssh.login()
                    cls_instance=ssh
                    result=True
                elif op == "add_class":
                    LOG.info("Executing task: init_call_class :%s" %(object_name))
                    cls_instance=self.init_call_class( object_name,*args,**kwargs )
                    if cls_instance: result=True
                else:
                    LOG.info("Executing task: call mothod :%s" %(object_name))
                    cls_instance=self.__current_instance 
                    result=self.call_instance_method(cls_instance,object_name,*args,**kwargs)
                    result_type=type(result)
                    if result_type is IntType and result == 0:
                        result = True
                if not result:
                    LOG.error("%s:Execute task %s %s failed " %(self.__classname,op,object_name))
                    return False
                u_oplist=(op,object_name,args,kwargs,cls_instance,result)
                self.__ops[index]=u_oplist
        except Exception,e:
            LOG.error("%s:Execute execute_ops failed with exception" %(self.__classname))
            LOG.error(str(e))
        return result

    def execute_task ( self ):
        '''
        Execute the operation list in the task, change the return valueto digit. Called by taskgroup
        @output:  Integer ;zero means sucessful
        '''
        result=self.execute_ops()
        exit_code=1
        result_type=type(result)
        if result_type is IntType:
            exit_code=result
        elif result_type is BooleanType:
            if result == True: exit_code=0
        elif result_type:
            if result: exit_code=0
        sys.exit(exit_code)
if __name__=="__main__":
    import os
    hostname="a4dpe828.asl.lab.emc.com"
    username="admin"
    password="Chang3M3Now."

    LOG.enable_console_log()
    task=Task()
    ssh=ssh_connect_to(hostname,username,password)
    LOG.info("Task executing")
    #task.add_ops('add_class','AvCP')
    #task.add_ops('add_method','create_checkpoint',ssh)
    #task.print_ops()
    #os.sys.exit(0)
    result=task.add_ops('add_class',"AvCP",ssh)
    #result=task.init_call_class("AvCP",ssh)
    LOG.info("result is %s" %(result))
    result=task.add_ops('add_method',"test_multi")
    LOG.info("result is %s" %(result))
    LOG.info("=====================Testing no arguments=================")
    result=task.add_ops('add_method',"create_checkpoint")
    LOG.info("result is %s" %(result))
    LOG.info("=====================Testing variable arguments=================")
    result=task.add_ops('add_method',"create_checkpoint",wait_to_completed=True, timeout=4,interval=1)
    LOG.info("result is %s" %(result))
    task.print_ops()
    task.execute_ops() 
    task.print_ops()
    os.sys.exit(0)
