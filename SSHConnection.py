#!/usr/bin/env python
#encoding=utf-8
"""
arthur: kevin.zou@emc.com
"""
from SSHLibrary import SSHLibrary
from lib.base.Errors import SSHLoginFailedError,SSHLogoutFailedError,CommandNotFoundError,CommandPermissionDeniedError
class SSHConnection():
    """
    This class use robot ssh library to provide a base class for ssh connection
    """
    def __init__(self,hostname,username,password,port,timeout=60,prompt="#"):
        self.host = hostname
        self.user = username
        self.passwd=password
        self.port=port
        self.timeout=timeout
        self.prompt=prompt
        self.ssh_agent = SSHLibrary(timeout=self.timeout, prompt=self.prompt)
        
    def login(self):
        """
        Login to remote ssh server
        """
        try:
            self.ssh_agent.open_connection(self.host)
            self.ssh_agent.login(self.user, self.passwd)
        except Exception,e:
            raise SSHLoginFailedError(str(e))
        
    def logout(self):
        """
        Logout remote ssh server
        """
        try:
            self.ssh_agent.close_connection()
        except Exception,e:
            raise SSHLogoutFailedError(str(e))
    
    def get_user(self):
        return self.user
    def get_hostname(self):
        return self.host
    
    def change_to_root_user(self, root_password, prompt="~/#"):
        """Changes to root user
        @root_password: root user password
        """
        self.change_to_user("root", root_password, prompt)

    def change_to_user(self, username, password, prompt="$"):
        """Changes to given user
        @username: the username will be switch to
        @password: the password for switch user
        """
        self.ssh_agent.write("su - " + username)
        if (username == "root"):
            self.ssh_agent.set_client_configuration(prompt=":")
            self.ssh_agent.read_until_prompt()
            self.ssh_agent.write(password)
            self.ssh_agent.set_client_configuration(prompt=prompt)
            self.ssh_agent.read_until_prompt(loglevel="info")
            
    def admin_password_complexity_check(self,command,change_password,default_password='AVE.changeme3M3Now.',prompt='~/>'):
        """
        Return change password output inforamtion, this method used to test admin password complexity rule
        @command: change admin password command, passwd admin
        @change_password: the password will be change to for admin user
        @default_password: the default password for admin user
        @prompt:default prompt
        """
        try:
            self.ssh_agent.write(command)
            self.ssh_agent.set_client_configuration(prompt=":")
            self.ssh_agent.read_until_prompt()
            self.ssh_agent.write(default_password)
            self.ssh_agent.set_client_configuration(prompt=":")
            self.ssh_agent.read_until_prompt()
            for i in range(0,3):
                self.ssh_agent.write(change_password)
                self.ssh_agent.set_client_configuration(prompt=":")
                self.ssh_agent.read_until_prompt()
            self.ssh_agent.set_client_configuration(prompt=prompt)
            output = self.ssh_agent.read_until_prompt(loglevel="info")
        except Exception,e:
            raise CommandNotFoundError(str(e))
        return output
    
    def change_admin_password(self,command,new_password,default_password,prompt='~/>'):
        
        """
        Return change password output inforamtion, this method used to change admin password
        @command: change admin password command, passwd admin
        @new_password: the password will be change to for admin user
        @default_password: the default password for admin user
        @prompt: default prompt
        """
        try:
            self.ssh_agent.write(command)
            self.ssh_agent.set_client_configuration(prompt=":")
            self.ssh_agent.read_until_prompt()
            self.ssh_agent.write(default_password)
            self.ssh_agent.set_client_configuration(prompt=":")
            self.ssh_agent.read_until_prompt()
            self.ssh_agent.write(new_password)
            self.ssh_agent.set_client_configuration(prompt=":")
            self.ssh_agent.read_until_prompt()
            self.ssh_agent.write(new_password)
            self.ssh_agent.set_client_configuration(prompt=prompt)
            output = self.ssh_agent.read_until_prompt(loglevel="info")
        except Exception,e:
            raise CommandNotFoundError(str(e))
        return output
    
    
    def execute_command(self, command, loglevel="info"):
        """
        execute ssh command with prompt and return output
        @command: command
        """
        self.ssh_agent.write(command, loglevel="trace")
        output = self.ssh_agent.read_until_prompt(loglevel="trace")
        output = self._drop_prompt_line(output)
        output = self._remove_new_mail_notification(output)
        return output
    
    def _drop_prompt_line(self, string):
        """
        drop the last line in system output
        @string: execute command output
        """
        try:
            idx = string.rfind('\n')
            string = string[:idx]
        except Exception,e:
            raise CommandNotFoundError(str(e))
        return string.rstrip('\r\n') 

    def _remove_new_mail_notification(self, string):
        """
        drop the send email notification line
        @string: execute command output
        """
        idx = string.rfind('You have new mail in')
        if idx != -1:
            string = string[:idx]
            return string.rstrip('\r\n')
        idx = string.rfind('You have mail in')
        if idx != -1:
            string = string[:idx]
            return string.rstrip('\r\n')
        else:
            return string
        
    def run_command(self, cmd):
        """
        Run command via ssh shell
        Ruturn a list, first item of the list is std_out, second item of the list is std_err, third item of the list 
        is return code
        """
        cmd_output=self.ssh_agent.execute_command(cmd,return_stdout=True, return_stderr=True,return_rc=True)
        #If command not found, raise CommandNotFoundError
        if cmd_output[1].find("command not found")!=-1:
            raise CommandNotFoundError("%s: command not found"%cmd)
        #If command permission denied, raise CommandPermissionDeniedError
        elif cmd_output[1].find("Permission denied")!=-1:
            raise CommandPermissionDeniedError("%s: command permission denied"%cmd)
        return cmd_output
    
    def start_command(self, cmd):
        '''
        Run command in async mode
        '''
        self.ssh_agent.start_command(cmd)
        
    def read_command_output(self, return_stdout=True, return_stderr=True, return_rc=True):
        '''
        Read output for asyn command
        '''
        return self.ssh_agent.read_command_output(return_stdout,return_stderr,return_rc)

    def run_overlap_command(self,cmdlist, cmd1):
        '''
        This function is to run several commands on server at the same time and return the runnning result
        '''
        for cmd in cmdlist:
            self.ssh_agent.start_command(cmd)
        cmd1_result=self.run_command(cmd1)
        result=[]
        for i in range(0,len(cmdlist)):
            result.append(self.ssh_agent.read_command_output(return_stdout=True, return_stderr=True, return_rc=True))
        result.append(cmd1_result)
        result.reverse()
        print result
        stdout_result=[]
        stderr_result=[]
        stdrc_result=[]
        for i in range(0,len(result)):
            stdout_result.append(result[i][0])
            stderr_result.append(result[i][1])
            stdrc_result.append(result[i][2])
        return stdout_result,stderr_result,stdrc_result
    

    def put_file(self, source, destination='.', mode='0744', newline=''):
        """
        Uploads the file(s) from the local machine to the remote host.
        @source: The path to the file on the local machine.
        Glob patterns, like '*' and '?', can be used in the source, in
        which case all the matching files are uploaded.
        @destination: The target path on the remote host.
        If multiple files are uploaded, e.g. patterns are used in the
        `source`, then this must be a path to an existing directory.
        The destination defaults to the user's home at the remote host.
        @mode: Can be used to set the target file permission.
        Numeric values are accepted. The default value is `0744` (-rwxr--r--).
        @newline: Can be used to force the line break characters that are
        written to the remote files. Valid values are `LF` and `CRLF`.

        The remote `destination` is created as following:
        1. If `destination` is an existing file, `source` file is uploaded
           over it.
        2. If `destination` is an existing directory, `source` file is
           uploaded into it. Possible file with same name is overwritten.
        3. If `destination` does not exist and it ends with [#Default path
           separator|the path separator], it is considered a directory.
           The directory is then created and `source` file uploaded into it.
           Possibly missing intermediate directories are also created.
        4. If `destination` does not exist and it does not end with [#Default
           path separator|the path separator], it is considered a file.
           If the path to the file does not exist, it is created.
        5. If `destination` is not given, the user's home directory
           on the remote machine is used as the destination.
        """
        return self.ssh_agent.put_file(source=source,
                                       destination=destination,
                                       mode=mode,
                                       newline=newline)

    def put_directory(self, source, destination='.', mode='0744', newline='',
                      recursive=False):
        """
        Uploads a directory, including its content, from the local machine to the remote machine.
        @source: The path on the local machine. Both absolute paths and
        paths relative to the current working directory are supported.
        @destination: The target path on the remote machine. Both absolute
        paths and paths relative to the current working directory are supported.
        @mode: Can be used to set the target file permission.
        Numeric values are accepted. The default value is `0744` (-rwxr--r--).
        @newline: Can be used to force the line break characters that are
        written to the remote files. Valid values are `LF` and `CRLF`.
        @recursive: Specifies, whether to recursively upload all
        subdirectories inside `source`. Subdirectories are uploaded if the
        argument value evaluates to true.

        The remote `destination` is created as following:
        1. If `destination` is an existing path on the remote machine,
           `source` directory is uploaded into it.
        2. If `destination` does not exist on the remote machine, it is
           created and the content of `source` directory is uploaded into it.
        3. If `destination` is not given, `source` directory is typically
           uploaded to user's home directory on the remote machine.
        """
        return self.ssh_agent.put_directory(source=source,
                                            destination=destination,
                                            mode=mode,
                                            newline=newline,
                                            recursive=recursive)
    def get_file(self, source, destination='.'):
        """
        @output: throw exception while failed
        Downloads file(s) from the remote machine to the local machine.

        source is a path on the remote machine. Both absolute paths and paths relative to the current
        working directory are supported. If the source contains wildcards explained in pattern matching,
        all files matching it are downloaded. In this case destination must always be a directory.

        destination is the target path on the local machine.
        Both absolute paths and paths relative to the current working directory are supported.
        The local destination is created using the rules explained below:

        1. If the destination is an existing file, the source file is downloaded over it.

        2. If the destination is an existing directory, the source file is downloaded into it.
            Possible file with the same name is overwritten.

        3. If the destination does not exist and it ends with the path separator of the local operating syst
em,           it is considered a directory. The directory is then created and the source file is
           downloaded into it. Possible missing intermediate directories are also created.

        4. If the destination does not exist and does not end with the local path separator,
           it is considered a file. The source file is downloaded and saved using that file name,
           and possible missing intermediate directories are also created.

        5. If destination is not given, the current working directory on the local machine is used as
           the destination. This is typically the directory where the test execution was started and
           thus accessible using built-in ${EXECDIR} variable.
        Argument path_separator was deprecated in SSHLibrary 2.0.
        """
        return self.ssh_agent.get_file(source=source, destination=destination)

    def list_directories_in_directory(self, path, pattern = None, absolute = False):
        """
        Returns the directory names, or optionally the absolute paths, on the
        given `path` on the remote host.

        @path: The path on the remote host to list.
        @pattern: If given, only the directory names that match the given pattern are returned. 
            Please do note, that the `pattern` is never matched against the full path, 
            even if `absolute` is set `True`.
        @absolute: If `True`, the absolute paths of the directories are returned instead of 
            the directory names.
        @returns: A sorted list of directories.
        """
        dirs = self.ssh_agent.list_directories_in_directory(path, pattern, absolute)
        return sorted(dirs)

    def directory_should_exist(self, path):
        """
        Check if the `path` points to a directory on the remote host.

        @path: The path on the remote host to check.
        @returns: `True`, if the `path` is points to an existing directory. False otherwise.
        """
        return self.ssh_agent.directory_should_exist(path)

if __name__=="__main__":
    ssh=SSHConnection("a4t81d8.datadomain.com","root","changeme",22)
    ssh.login()
    print ssh.run_command("pwd")
    ssh.logout()
