#encoding:utf-8
'''Move specified postfix files to specified directory'''

import os
import re
import shutil
import logging


'''Defined log configuration and output'''
logger=logging.getLogger(__name__)
Filename='Move.log'
Filemode='a'
Format='%(asctime)s %(filename)s %(process)d [line:%(lineno)d] %(levelname)s %(message)s'
Datefmt='%a-%d-%b-%Y %H:%M:%S'
#logging.basicConfig(filename=Filename,filemode=Filemode,format=Format,level=logging.DEBUG,datefmt=Datefmt)

console=logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(Format)
logger.addHandler(console)

logfile=logging.FileHandler(Filename,mode=Filemode)
logfile.setLevel(logging.DEBUG)
logfile.setFormatter(Format)
logger.addHandler(logfile)


class Move:
    def __index__(self):
        pass

    def Findfile(self):
        '''Find the specified postfix files'''
        path = os.getcwd()
        listdir = os.listdir(path)
        str = '\n'.join(listdir)
        #print path
        logging.debug(path)
       # print listdir,'\n'
        logging.debug(listdir)
       # print str,'\n'
        logging.debug(str)

        pattern = re.compile(r'^\w*.py$',re.M)
        self.reslut = re.findall(pattern,str)
        logging.info('self.result:%s'%self.reslut)


    def Movefile(self):
        '''Move the files to specified directory'''
        dst = raw_input(r"Enter the destination directory path: ")
        #dst = 'C:\\Users\\xzhang\\Desktop\\Script\\python script'
        if os.path.isdir(dst):
            for files in self.reslut:
                file = os.getcwd()+'\\'+files
                #print 'files have:',file
                logging.info('files have: %s' % file)
                shutil.copy(file,dst)
        else:
            #print "It's not a path!"
            logging.error("It's not a path!")


a = Move()
if __name__ == '__main__':
    logger.addHandler(console)
    logger.addHandler(logfile)
    a.Findfile()
    a.Movefile()