#encoding:utf-8
'''Move specified postfix files to specified directory
   Author:Glimmer
   V1.0: Move specified postfix files to specified directory
   v1.1: Add log function to track error message
   v1.2: Print log to console and log file.
   '''


import os
import re
import shutil
import logging


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

    def Findfile(self):
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

        pattern = re.compile(r'^\w*.py$',re.M)
        self.reslut = re.findall(pattern,str)
        logger.info('self.result:%s'%self.reslut)


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


a = Move()
if __name__ == '__main__':
    a.Findfile()
    a.Movefile()