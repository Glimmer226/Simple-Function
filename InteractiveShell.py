#!/usr/bin/env python
#encoding=utf-8
"""
arthur: kevin.zou@emc.com
"""
from lib.base.SSHConnection import SSHConnection
class InteractiveShell(SSHConnection):
    """
    This class use robot ssh library to provide a base class for interactive ssh connection
    """
    def __init__(self,hostname,username,password,port,timeout=60,prompt="#"):
        self.host = hostname
        self.user = username
        self.passwd= password
        self.port= port
        self.timeout= timeout
        self.prompt= prompt
        SSHConnection.__init__(self, self.host, self.user, self.passwd, self.port, self.timeout, self.prompt)
        
    def write(self, text):
        """
        Writes the given `text` on the remote machine and appends a newline
        """
        return self.ssh_agent.write(text)

    def read(self, loglevel=None, delay=None):
        """
        Consumes and returns everything available on the server output.
        If `delay` is given, this keyword waits that amount of time and reads
        output again. This wait-read cycle is repeated as long as further reads
        return more output or the [#Default timeout|timeout] expires.
        `delay` must be given in Robot Framework's time format (e.g. `5`,
        `4.5s`, `3 minutes`, `2 min 3 sec`) that is explained in detail in
        the User Guide.

        This keyword is most useful for reading everything from
        the server output, thus clearing it.

        The read output is logged. `loglevel` can be used to override
        the [#Default loglevel|default log level].
        """
        return self.ssh_agent.read(loglevel=loglevel, delay=delay)

    def read_until_prompt(self):
        """
        Read output until the end of a command, the prompt is set defaultly as "#"  
        """
        return self.ssh_agent.read_until_regexp(self.prompt)
        
    def read_until_regexp(self, regexp):
        """
        Read output until match given regular expression
        """
        return self.ssh_agent.read_until_regexp(regexp)
    
if __name__=="__main__":
    shell=InteractiveShell("a4t81d8.datadomain.com","root","changeme",22)
    shell.login()
    shell.write("pwd")
    print shell.read_until_prompt()