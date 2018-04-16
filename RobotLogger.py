#!/usr/bin/env python
#encoding=utf-8
"""
arthur: kevin.zou@emc.com
"""
import os
import datetime
import platform
import logging
import logging.handlers
from robot.libraries.BuiltIn import BuiltIn

class RobotLogger:
    """
    Use robot built-in log to recored message
    
    "log_to_html" is enabled by default as details test log should be in the html for test trace.
    
    "log_to_console" is disabled for"trace/debug/info" by default, but if you are not running test library in robot environment, 
    log to html doesn't work, you need to enable console to debug, you can use method "enable_console_log" to enable all for 
    debug purpose, or you can pass parameter "log_to_console=True" for special case that you really want to log to console 
    
    "ebable_repr" is used to log strings or bytes containing invisible characters, like "Hyv\xe4 \\x00", it's disabled by 
    default, also you can pass parameter "ebable_repr=True" for special case if you want to enable.
    """
    def __dlogger__init(self):
        '''
        Added robot debug log for debug purpose.
        '''
        self.__dlog_name="robot_debug"
        self.__dlog_file=None
        self.__dlogger=None
        if platform.system()=="Linux":
            self.__dlog_file="/tmp/robot_debug.log"
        elif platform.system()=="Windows":
            #Try to find temp folder from system environment variable
            if os.environ.has_key("TMP"):
                log_dir=os.environ["TMP"]
                self.__dlog_file=os.path.join(log_dir,"robot_debug.log")
        if self.__dlog_file:
            self.__fhandle=logging.handlers.RotatingFileHandler(self.__dlog_file,mode='a', maxBytes=1024*1024*10, backupCount=10, encoding="utf-8")
            formatter = logging.Formatter(
                fmt='%(asctime)s pid=%(process)d %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.__fhandle.setFormatter(formatter)
            self.__fhandle.setLevel(logging.DEBUG)
            self.__dlogger = logging.getLogger( self.__dlog_name )
            self.__dlogger.setLevel(logging.DEBUG)
            self.__dlogger.addHandler(self.__fhandle)

    def __init__(self):
        self.enable_console_all= False
        self.main_pid = None
        self.robot_built_in = BuiltIn()
        self.__dlogger__init()
         

    def enable_background(self, main_pid, msg_dict):
        """
        Enable log in background
        """
        self.main_pid = main_pid
        self.messages = msg_dict

    def disable_background(self):
        self.main_pid = None
        self.messages.clear()

    def enable_console_log(self):
        """
        Enable all level message log to console for debug purpose
        """
        self.enable_console_all= True

    def disable_console_log(self):
        """
        Disable message log to console unless "log_to_console" is set to True
        """
        self.enable_console_all= False

    def write(self, msg, level, log_to_html=True, log_to_console=False, enable_repr=False):
        pid = os.getpid()
        if (not self.main_pid) or (pid == self.main_pid):
            self.robot_built_in.log(msg, level, html = log_to_html, console = log_to_console, repr = enable_repr)
        else:
            message = Background_Message(msg, level, log_to_html, log_to_console, enable_repr)
            message_list = self.messages.get(pid, [])
            message_list.append(message)
            self.messages[pid] = message_list
        #self.__dlogger.debug("%s:%s" %(level,msg))
    def trace(self, message, log_to_html=True, log_to_console=False, enable_repr=False):
        """
        Disable trace message logging to console
        """
        if self.enable_console_all:
            log_to_console=True
        self.write(message, "TRACE", log_to_html, log_to_console, enable_repr)
        if self.__dlogger:
            self.__dlogger.debug("%s" %(message))

    def debug(self,message,log_to_html=True, log_to_console=False, enable_repr=False):
        """
        Disable debug message logging to console
        """
        if self.enable_console_all:
            log_to_console=True
        self.write(message, "DEBUG", log_to_html, log_to_console, enable_repr)
        if self.__dlogger:
            self.__dlogger.debug("%s" %(message))

    def info(self,message,log_to_html=True, log_to_console=False, enable_repr=False):
        """
        Disable info message logging to console
        """
        if self.enable_console_all:
            log_to_console=True
        self.write(message, "INFO", log_to_html, log_to_console, enable_repr)
        if self.__dlogger:
            self.__dlogger.info("%s" %(message))

    def warn(self,message,log_to_html=True, log_to_console=True, enable_repr=False):
        """
        Warn message is important, should be displayed in the console
        """
        if self.enable_console_all:
            log_to_console=True
        self.write(message, "WARN", log_to_html, log_to_console, enable_repr)
        if self.__dlogger:
            self.__dlogger.warn("%s" %(message))

    def error(self,message,log_to_html=True, log_to_console=True, enable_repr=False):
        """
        Error message is important, should be displayed in the console
        """
        if self.enable_console_all:
            log_to_console=True
        self.write(message, "ERROR", log_to_html, log_to_console, enable_repr)
        if self.__dlogger:
            self.__dlogger.error("%s" %(message))

    def log_background_messages(self, pid = None):
        """
        Forwards messages logged on background to Robot Framework log.
        By default forwards all messages logged by all processes, but can be
        limited to a certain process by passing process's pid as an argument.
        This method must be called from the main process.
        Logged messages are removed from the message storage.
        """
        current_pid = os.getpid()
        if current_pid != self.main_pid:
            raise RuntimeError(
                "Logging background messages is only allowed from main"
                " process. Current process id: %s" % pid)

        if pid:
            self._log_messages_by_process(pid)
        else:
            self._log_all_messages()

    def _log_messages_by_process(self, pid):
        for message in self.messages.pop(pid, []):
            self.robot_built_in.log(message.message, message.level, message.html, message.console, message.repr)

    def _log_all_messages(self):
        """
        Log all background messages and clear logged messages.
        """
        for pid, message_list in self.messages.items():
            self.robot_built_in.log("Messages by sub process - %s" % pid, "INFO", html = True, console = self.enable_console_all, repr = False)
            for message in message_list:
                self.robot_built_in.log(message.message, message.level, message.html, message.console, message.repr)
        self.messages.clear()

    def reset_background_messages(self, pid = None):
        if pid:
            self.messages.pop(pid)
        else:
            self.messages.clear()

class Background_Message():
    def __init__(self, message, level = 'INFO', log_to_html = True, log_to_console = False, enable_repr = False):
        current_time = datetime.datetime.now()
        self.message = "%s: %s" % (current_time.strftime("%H:%M:%S.%f"), message)
        self.level = level.upper()
        self.html = log_to_html
        self.console = log_to_console
        self.repr = enable_repr

#Use "from base.RobotLogger import LOG" to call this module
LOG=RobotLogger()
if __name__=="__main__":
    LOG.enable_console_log()
    LOG.info("info message")
    LOG.disable_console_log()
    LOG.error("error message")
