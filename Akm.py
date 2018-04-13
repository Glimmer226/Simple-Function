#!/usr/bin/env python
# encoding=utf-8

import os
import re
import time
from xml.etree import ElementTree as ET
from lib.base.RobotLogger import LOG
from lib.server.AvServer import AvServer


class Akm(AvServer):
    '''
    A class used for Avamar Key Manager related commands.
    '''
    def __init__(self, ssh=None):
        '''
        Constructor
        '''
        self.init_akm_conf = {
            'Address': '',
            'Password': '',
            'UserName': '',
            'ServerHostname': '',
            'LibPath': '/usr/local/avamar/lib/akm/',
            'CertPath': '/usr/local/avamar/etc/akm/',
            'DataPath': '/usr/local/avamar/etc/akm/',
            'AddDefaultSymmetricKeyClassress': 'AES256',
            }
        self.cert_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.realpath(__file__))))),
            'tools', 'kmip')
        self.ssh = ssh
        self.akm_conf = {}

    def get_conf(self):
        '''
        Return the content of akm.xml.
        '''
        self.conf_path = '/usr/local/avamar/etc/akm/akm.xml'
        result = self.ssh.run_command('cat %s' % self.conf_path)
        root = ET.fromstring(result[0].strip())
        if root.tag != 'AkmConfig':
            LOG.error('The root tag name is %s, not AkmConfig.' % root.tag)
            raise Exception('Wrong format of akm.xml.')
        if root.getchildren():
            LOG.error('The AkmConfig node has child nodes.')
            raise Exception('Wrong format of akm.xml.')
        self.akm_conf = root.attrib
        return self.akm_conf

    def is_initial_conf(self):
        '''
        Check the akm.xml is in initial state.
        '''
        self.get_conf()
        for key, value in self.init_akm_conf.iteritems():
            if value != self.akm_conf.get(key, None):
                return False
        return True

    def initialize_conf(self):
        '''
        Set all the values in the akm.xml to initial values.
        '''
        init_conf_file = os.path.join(self.cert_dir, 'akm.xml')
        self.ssh.put_file(init_conf_file,
                          destination='/usr/local/avamar/etc/akm/',
                          mode='0744')

    def install_certificate(self, root_password):
        '''
        Copy certificates to remote Avamar server.
        @root_password: Avamar server root password, installAKM.sh should
            be run as root user.
        '''
        self.remote_dir = '/usr/local/avamar/etc/akm/'
        self.tmp_dir = '/tmp'
        self.ssh.directory_should_exist(self.remote_dir)
        for cert in os.listdir(self.cert_dir):
            LOG.info('+++' + str(cert))
            if cert.endswith('xml'):
                LOG.info('Skip')
                continue
            local_cert = os.path.join(self.cert_dir, cert)
            tmp_cert = os.path.join(self.tmp_dir, cert)
            remote_cert = os.path.join(self.remote_dir, cert)
            self.ssh.put_file(local_cert, destination=self.tmp_dir)
            cmd = 'echo %s | su - root -c "mv %s %s;chown root:root %s;chmod 444 %s"' \
                  % (root_password, tmp_cert, remote_cert, remote_cert, remote_cert)
            self.ssh.run_command(cmd)

    def enable_akm(self, root_password, address, username, password):
        '''
        Use installAKM.sh script installs, configures, and starts Avamar
        Key Manager. Check script execution result.
        @root_password: Avamar server root user password.
        @address: IP Address or FQDN and port of the kmip server.
        @username: User Name in client public PEM.
        @password: Password for the Avamar system’s private key certificate.
        '''
        # Check whether akm is already enabled
        status = self.status_akm()
        if re.search('akm \(pid \d+\) is running', status):
            return True

        # Copy certificates to server
        self.install_certificate(root_password)
        # Check whether akm configuration file is initialized
        if not self.is_initial_conf():
            self.initialize_conf()

        cmd = 'echo %s | su - root -c "ssh-agent bash -c \\\"ssh-add /root/.ssh/rootid;echo \'%s\' | installAKM.sh --ip=%s --username=%s\\\""' \
            % (root_password, password, address, username)
        LOG.info('Execute command: %s' % cmd)
        result = self.ssh.run_command(cmd)
        LOG.info('Install AKM result: %s' % result)

        # Check script result
        if 'Successfully started AKM' not in result[0]:
            return False
        # Check akm service status
        status = self.status_akm()
        if not re.search('akm \(pid \d+\) is running', status):
            return False
        # Check configuration file
        akm_conf = self.get_conf()
        if akm_conf['Address'] != address or akm_conf['UserName'] != username:
            return False
        return True

    def run_install_akm(self, root_password, address, username, password):
        '''
        Use installAKM.sh script installs, configures, and starts Avamar
        Key Manager. Return result without checking.
        @root_password: Avamar server root user password.
        @address: IP Address or FQDN and port of the kmip server.
        @username: User Name in client public PEM.
        @password: Password for the Avamar system’s private key certificate.
        '''
        cmd = 'echo %s | su - root -c "ssh-agent bash -c \\\"ssh-add /root/.ssh/rootid;echo \'%s\' | installAKM.sh --ip=%s --username=%s\\\""' \
            % (root_password, password, address, username)
        LOG.info('Execute command: %s' % cmd)
        result = self.ssh.run_command(cmd)
        LOG.info('Install AKM result: %s' % result)
        return result

    def change_password(self, root_password, cert_password):
        '''
        Replaces the private key certificate password that Avamar Key Manager
        stores with a new one.
        @root_password: Avamar server root user password.
        @server: The fully qualified domain name, or IP address in
            dotted-quad format of external key management server.
        @cert_password: The new private key certificate password.
        '''
        cmd = 'echo %s | su - root -c "ssh-agent bash -c \\\"ssh-add /root/.ssh/rootid;echo \'%s\' | installAKM.sh --ip=%s --updatepassword=%s\\\""' \
            % (root_password, cert_password)
        LOG.info('Execute command: %s' % cmd)
        self.ssh.write(cmd)
        self.ssh.read_until_regexp('Would you like to continue?\[y/n\]')
        self.ssh.write('y')
        self.ssh.read_until_regexp('Please enter the AKM Password\:')
        self.ssh.write(cert_password)
        akm_output = self.ssh.read_until_prompt()
        LOG.info('Update AKM password output: %s' % akm_output)
        return akm_output

    def status_akm(self):
        '''
        Check the akm service status.
        /etc/init.d/akm
        0  akm (pid $pid) is running...
        1  akm dead but pid file exists
        2  akm dead but subsys locked
        3  akm is stopped
        '''
        result = self.ssh.run_command('sudo service akm status')
        return result[0]

    def start_akm(self):
        '''
        Start the akm service.
        '''
        result = self.ssh.run_command('sudo service akm start')
        return False if result[2] else True

    def stop_akm(self):
        '''
        Stop the akm service.
        '''
        result = self.ssh.run_command('sudo service akm stop')
        return False if result[2] else True

    def restart_akm(self):
        '''
        Restart the akm service.
        '''
        result = self.ssh.run_command('sudo service akm restart')
        return False if result[2] else True

    def rotate_key(self):
        '''
        Generate a new key on KMIP server and retrieved/rotated into GSAN.
        '''
        cmd = 'avmaint atrestencryption --akmkey --ava'
        std_out, std_err, ret_code = self.ssh.run_command(cmd)
        LOG.info('Output: %s, Error: %s, Return code: %s' % (std_out, std_err, ret_code))
        if ret_code == 0:
            if 'ERROR' in std_out.upper() or 'ERROR' in std_err.upper():
                return False
            return True
        else:
            return False

    def get_salts_number(self):
        '''
        Get number of salts retrieved from KMIP server.
        '''
        cmd = 'avmaint nodelist | grep salts'
        std_out, std_err, ret_code = self.ssh.run_command(cmd)
        LOG.info('Output: %s, Error: %s, Return code: %s' % (std_out, std_err, ret_code))
        if ret_code == 0:
            m = re.search('nr-salts="(\d+)"/>', std_out)
            if m:
                return int(m.group(1))
            else:
                return False
        else:
            return False

    def check_gsan_log(self, msg):
        '''
        Check whether the given message exist in gsan logs.
        @msg: The message to find in gsan logs.
        '''
        LOG.info('Check %s in gsan log' % msg)
        cmd = 'eval `ssh-agent`;eval `ssh-add ~/.ssh/dpnid`;mapall "tail -1000 /data01/cur/gsan.log|egrep \\\"%s\\\""' % msg
        result = self.ssh.run_command(cmd)
        if result[2] != 0:
            return False
        else:
            return True

    def restart_dpn_with_akm_stop(self):
        '''
        Start gsan using dpnctl.
        '''
        cmd = 'eval `ssh-agent`;eval `ssh-add ~/.ssh/dpnid`;restart.dpn'
        self.ssh.write(cmd)
        elapsed = 0
        interval = 30
        timeout = 900
        ret_value = True
        while elapsed < timeout:
            time.sleep(interval)
            elapsed += interval
            if self.check_gsan_log('ERROR: <0001>'):
                LOG.info('Found akm not available in gsan log')
                break
        else:
            ret_value = False
        cmd = "ps -ef | grep restart.dpn | grep -v grep | awk '{print $2}' | xargs kill -9"
        result = self.ssh.run_command(cmd)
        if result[2]:
            LOG.info('Kill restart.dpn failed: %s' % str(result))
            ret_value = False
        return ret_value
