#encoding:utf-8
'''Move specified postfix files to specified directory'''

import os
import re
import shutil

class Move:
    def __index__(self):
        pass

    def Findfile(self):
        '''Find the specified postfix files'''
        path = os.getcwd()
        listdir = os.listdir(path)
        str = '\n'.join(listdir)
        #print path
       # print listdir,'\n'
       # print str,'\n'

        pattern = re.compile(r'^\w*.py$',re.M)
        self.reslut = re.findall(pattern,str)
        print 'self.result:',self.reslut


    def Movefile(self):
        '''Move the files to specified directory'''
        dst = raw_input(r"Enter the destination directory path: ")
        #dst = 'C:\\Users\\xzhang\\Desktop\\Script\\python script'
        if os.path.isdir(dst):
            for files in self.reslut:
                file = os.getcwd()+'\\'+files
                print 'files have:',file
                shutil.copy(file,dst)
        else:
            print "It's not a path!"


a = Move()
if __name__ == '__main__':
    a.Findfile()
    a.Movefile()