#encoding:utf-8
'''Move specified postfix files to specified directory
   Author:Glimmer
   V1.0: Move specified postfix files to specified directory
   v1.1: Add log function to track error message
   v1.2: Print log to console and log file.
   v1.3: You can input specified postfix. Add usage,version.
   V1.4: Improve log function.
   '''


import os
import re
import shutil
import logging
import getopt,sys

class log():
    def __init__(self,logger_name,log_name,csl=logging.INFO):
        #time_str = time.strftime('%Y_%m_%d_%H_%M_%S',time.localtime(time.time()))
        self.logname = log_name + '.log'
        self.log_file_dir = 'Move_log'
        self.csl = csl
        '''Defined logger'''
        self.logger=logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        self.formatter = logging.Formatter(r'%(asctime)s-%(filename)s[line:%(lineno)d]-%(levelname)s: %(message)s')

    def console(self):
        '''Defined console log'''
        console = logging.StreamHandler()
        console.setLevel(self.csl)
        console.setFormatter(self.formatter)
        self.logger.addHandler(console)

    def file(self):
        '''Defined files log'''
        files = logging.FileHandler(filename=self.logname, mode='a')
        files.setFormatter(logging.DEBUG)
        files.setFormatter(self.formatter)
        self.logger.addHandler(files)

    def file_log(self):
        if not os.path.isdir(self.log_file_dir):
            self.logger.debug("Log file directory %s no exsit,will create it." % self.log_file_dir)
            #print "Log file directory %s no exsit,will create it." % log_file_dir
            os.mkdir(self.log_file_dir)
            os.chdir(self.log_file_dir)
            self.file()
        else:
            self.logger.debug("%s exsit" % self.log_file_dir)
            #print "%s exsit" % log_file_dir
            os.chdir(self.log_file_dir)
            self.file()

log = log('Move','Move',logging.INFO)
log.console()
log.file_log()

def parseArgs():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'p:hvd', ["postfix=", "help", "version", "debug"])
        for o, a in opts:
            if o in ('-h', '--help'):
                usage()
                sys.exit()
            if o in ('-v', '--version'):
                version()
                sys.exit()
            if o in ('-p', '--postfix'):
                postfix = a
                return postfix
    except getopt.GetoptError:
        usage()
        sys.exit()

class Move:
    def __init__(self):
        pass

    def Findfile(self,postfix):
        '''Find the specified postfix files'''
        os.chdir("C:\Users\zhangg14\Desktop\Python")
        path = os.getcwd()
        listdir = os.listdir(path)
        str = '\n'.join(listdir)
        log.logger.debug('Working direcroty is %s'% path)
        log.logger.debug('Target files have %s'% listdir)
        log.logger.debug('Separate files in list: %s'% str)

        Pattern = r'^\w*.%s$' % postfix #postfix: py,log,txt...
        pattern = re.compile(Pattern,re.M)
        self.reslut = re.findall(pattern,str)
        if self.reslut == None:
            print "Have not find postfix files in this directory!"
            #sys.exit()
        log.logger.debug('self.result:%s'%self.reslut)
        #sys.exit()

    def Movefile(self):
        '''Move the files to specified directory'''
        dst = raw_input(r"Enter the destination directory path: ")
        log.logger.info('Input destination path: %s' % dst)
        #dst = 'C:\\Users\\xzhang\\Desktop\\Script\\python script'
        if os.path.isdir(dst):
            for files in self.reslut:
                file = os.getcwd()+'\\'+files
                #print 'files have:',file
                log.logger.info('files have: %s' % file)
                shutil.copy(file,dst)
        else:
            #print "It's not a path!"
            log.logger.error("It's not a path!")

def usage():
    print "usage: %s [-p|--postfix]{py|log|txt|} [-h|--help] [-v|--version]" % sys.argv[0]

def version():
    print '''    v1.0: Move specified postfix files to specified directory.
    v1.1: Add log function to track error message.
    v1.2: Print log to console and log file.
    v1.3: You can input specified postfix.
    V1.4: Improve log function.'''

def main():
    p = parseArgs()
    a=Move()
    a.Findfile(p)
    a.Movefile()

if __name__ == '__main__':
    main()
