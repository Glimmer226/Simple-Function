#encoding:utf-8
'''Move specified postfix files to specified directory
   Author:Glimmer
   V1.0: Move specified postfix files to specified directory
   v1.1: Add log function to track error message
   v1.2: Print log to console and log file.
   v1.3: You can input specified postfix. Add usage,version.
   '''


import os
import re
import shutil
import logging
import getopt,sys


'''Defined logger'''
logger=logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

'''Defined console log'''
console=logging.StreamHandler()
formatter=logging.Formatter(r'%(asctime)s-%(filename)s[line:%(lineno)d]-%(levelname)s: %(message)s')
console.setLevel(logging.INFO)
console.setFormatter(formatter)
logger.addHandler(console)

'''Defined files log'''
files=logging.FileHandler(filename='Move.log',mode='a')
files.setFormatter(logging.DEBUG)
files.setFormatter(formatter)
logger.addHandler(files)

class Move:
    def __index__(self):
        pass

    def Findfile(self,postfix):
        '''Find the specified postfix files'''
        path = os.getcwd()
        listdir = os.listdir(path)
        str = '\n'.join(listdir)
        #print path
        logger.debug(path)
       # print listdir,'\n'
        logger.debug(listdir)
       # print str,'\n'
        logger.debug(str)

        Pattern = r'^\w*.%s$' % postfix #postfix: py,log,txt...
        pattern = re.compile(Pattern,re.M)
        self.reslut = re.findall(pattern,str)
        logger.debug('self.result:%s'%self.reslut)


    def Movefile(self):
        '''Move the files to specified directory'''
        dst = raw_input(r"Enter the destination directory path: ")
        logger.info('Inpurt destination path: %s' % dst)
        #dst = 'C:\\Users\\xzhang\\Desktop\\Script\\python script'
        if os.path.isdir(dst):
            for files in self.reslut:
                file = os.getcwd()+'\\'+files
                #print 'files have:',file
                logger.info('files have: %s' % file)
                shutil.copy(file,dst)
        else:
            #print "It's not a path!"
            logger.error("It's not a path!")

def usage():
    print "usage: %s [-p|--postfix]{py|log|txt|} [-h|--help] [-v|--version]" % sys.argv[0]

def version():
    print '''    v1.0: Move specified postfix files to specified directory
    v1.1: Add log function to track error message
    v1.2: Print log to console and log file.
    v1.3: You can input specified postfix'''

def parseArgs():
    try:
        opts,args = getopt.getopt(sys.argv[1:],'p:hv',["postfix=","help","version"])
        for o,a in opts:
            if o in ('-h','--help'):
                usage()
                sys.exit()
            if o in ('-v','--version'):
                version()
                sys.exit()
            if o in ('-p','--postfix'):
                postfix = a
    except getopt.GetoptError:
        usage()
        sys.exit()
    return postfix

def main():
    a=Move()
    postfix = parseArgs()
    a.Findfile(postfix)
    a.Movefile()

if __name__ == '__main__':
    main()
