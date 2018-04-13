#!/usr/bin/env python
#encoding=utf-8
"""
arthur: kevin.zou@emc.com
"""
class Error(Exception):
    """
    Base class for framework errors.

    Do not raise this method but use more specific errors instead.
    """

    def __init__(self, message='', details=''):
        Exception.__init__(self, message)
        self.details = details

    @property
    def message(self):
        return unicode(self)
    

class SSHError(Error):
    """
    Base class for ssh error
    
    Do not raise this method but use more specific errors instead.
    """

class SSHLoginFailedError(SSHError):
    """
    Used when the ssh login has problem
    """
    
class SSHLogoutFailedError(SSHError):
    """
    Used when the ssh logout has problem
    """
    
class CommandError(Error):
    """
    Base class for run command error
    
    Do not raise this method but use more specific errors instead.
    """
class CommandNotFoundError(CommandError):
    """
    Used whem commmand not found
    """
class CommandPermissionDeniedError(CommandError):
    """
    Used whem commmand permission denied
    """