#!/usr/bin/env python
# encoding=utf-8

import os
import re
import time
import datetime
from lib.base.RobotLogger import LOG
from lib.server.AvCP import AvCP
from lib.server.AvDpn import AvDpn
from lib.base.InteractiveShell import InteractiveShell
from lib.base.SSHConnection import SSHConnection
from lib.mc.MCCLI import MCCLI


class ACP(object):
    '''
    A class used for run ACP testing, maintenance operation performance.
    '''
    def __init__(self):
        self.ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.log_dir = '/home/admin/performance/acp/%s' % self.ts
        self.result_repo = '/home/admin/results-archive'
        # No DD attached by default, all tests run on Avamar
        self.ddr = False

    def acp_attach_server(self, server, admin_user, admin_password, root_user, root_password):
        '''
        Attach the server's information to Perf instance.
        @server: Server host.
        @admin_user: Server admin user.
        @admin_password: Server admin password.
        @root_user: Server root user.
        @root_password: Server root password.
        '''
        self.server = server
        self.admin_user = admin_user
        self.admin_password = admin_password
        self.root_user = root_user
        self.root_password = root_password
        self.server_ssh = InteractiveShell(server, admin_user,
                                           admin_password, 22, 120, '')
        self.server_ssh.login()
        self.scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'tools', 'acp')
        self.remote_dir = '/home/admin/acp'

    def acp_attach_dd(self, ddhost, ddboostuser, ddpwd):
        '''
        Attach DD to the Avamar server, must be run after attach server.
        @ddhost: Specifies which Data Domain system to delete.
        @ddboostuser: Specifies the DD ddboost user.
        @ddpwd: Specifies the DD ddboost user password.
        '''
        self.ddr = True
        self.ddr_index = 1
        self.mccli = MCCLI()
        return self.mccli.run_mccli_add_dd(self.server_ssh, ddhost, ddboostuser, ddpwd, default=True, force=True, stream=20)

    def acp_delete_dd(self, ddhost):
        '''
        Delete DD from the Avamar server.
        @ddhost: Specifies which Data Domain system to delete.
        '''
        return self.mccli.run_mccli_del_dd(self.server_ssh, ddhost, force=True)

    def set_preconditions(self):
        '''
        Copy scripts to remote server.
        '''
        self.update_password(self.scripts_dir)
        dest = os.path.dirname(self.remote_dir)
        self.server_ssh.put_directory(self.scripts_dir,
                                      destination=dest,
                                      mode='0755',
                                      recursive=True)
        self.create_repo()

    def update_password(self, path):
        '''
        Change the default password in scripts to correct value.
        '''
        for sub_path in os.listdir(path):
            new_path = os.path.join(path, sub_path)
            if os.path.isdir(new_path):
                self.update_password(new_path)
            else:
                with open(new_path, 'rb') as f:
                    content = f.read()
                if re.search('^IDPASSWD=.*$', content, re.M):
                    new_passwd_line = 'IDPASSWD=%s' % self.root_password
                    content = re.sub('^IDPASSWD=.*$', new_passwd_line, content, flags=re.M)
                    with open(new_path, 'wb') as f:
                        f.write(content)

    def create_repo(self):
        '''
        Create repo directory in remote server.
        '''
        # repo and /home/admin/work
        self.create_directory('/home/admin/work')
        self.create_directory('/home/admin/results-archive')

    def fill_up(self, start_seed, end_seed):
        '''
        Run avtar with 1 GB backups to an Avamar server to fill up
        of an Avamar server for acp performance testing.
        @start_seed: The seed of the *first* backup to perform.
        @end_seed: The seed of the *last* backup to perform.
        '''
        if self.ddr:
            script = 'gc-crunch-backups-1gb-chunks7k-auto-dd.sh'
        else:
            script = 'gc-crunch-backups-1gb-chunks7k-auto.sh'
        script = os.path.join(self.remote_dir, 'fill-up-1.0', 'scripts', script)
        if self.ddr:
            cmd = 'eval `ssh-agent`; eval `ssh-add /home/admin/.ssh/dpnid`; %s %s %s %s 27000 %s 2>&1' \
                  % (script, start_seed, end_seed, self.server, self.ddr_index)
        else:
            cmd = 'eval `ssh-agent`; eval `ssh-add /home/admin/.ssh/dpnid`; %s %s %s %s 27000 2>&1' \
                  % (script, start_seed, end_seed, self.server)
        result = self.server_ssh.run_command(cmd)
        LOG.info('Fill up server result: %s' % result)
        return False if result[2] else True

    def run_acp_test(self, email, project, configuration, start_seed, end_seed):
        '''
        Run an ACP test.
        @email: Engineer email address.
        @project: Project Name.
        @configuration: The test configuration that was run.
        @start_seed: The *first* backup seed used to fill each node.
        @end_seed: The *final* backup seed used to fill each node.
        '''
        # 1. Take a checkpiont and note the cp tag
        avcp = AvCP(self.server_ssh)
        cp_name = avcp.create_checkpoint()
        all_cp_name = avcp.get_all_cp_name()
        if cp_name is False:
            LOG.error('Take checkpoint failed')
            return False
        LOG.info('Take a checkpoint %s' % cp_name)

        # 2. Stop Gsan
        avdpn = AvDpn(self.server_ssh)
        if avdpn.shutdown_dpn() is False:
            LOG.error('Shutdown gsan failed')
            return False
        LOG.info('Gsan stopped')

        # 3. Delete the other checkpiont and Cur data
        if self.mapall_root("rm -rf /data0?/cur") != 0:
            LOG.error('Remove cur data failed')
            return False
        LOG.info('Removed cur data')
        for tag in all_cp_name:
            if tag != cp_name:
                LOG.info('Remove checkpoint %s' % tag)
                if self.mapall_root("rm -rf /data0?/%s" % tag) != 0:
                    LOG.error('Remove other checkpoints failed')
                    return False
        LOG.info('Removed all other checkpoints')

        # 4. Roll back to checkpoint "rollback.dpn --nocheck --cptag=cp..."
        if not avdpn.rollback_dpn(cp_name, options='--nocheck'):
            LOG.error('Rollback to checkpoint %s failed' % cp_name)
            return False
        LOG.info('Rollback to checkpoint %s' % cp_name)

        # 5. Run the acp scripts "acp.pl"
        LOG.info('Start to run ACP test')
        self.wipe_workdir('/home/admin/work')
        script = os.path.join(self.remote_dir, 'acp-1.15', 'acp.pl')
        cmd = 'eval `ssh-agent`; eval `ssh-add /home/admin/.ssh/dpnid`; perl %s' % script
        self.server_ssh.login()
        self.server_ssh.write(cmd)
        self.server_ssh.read_until_regexp('Would you like to change the repository directory')
        self.server_ssh.write('y')
        self.server_ssh.read_until_regexp('Enter the repository directory to use')
        self.server_ssh.write('/home/admin/results-archive')
        self.server_ssh.read_until_regexp('Enter Engineer email address')
        self.server_ssh.write(email)
        self.server_ssh.read_until_regexp('Enter the Project Name')
        self.server_ssh.write(project)
        self.server_ssh.read_until_regexp('Enter one line describing the test configuration that was run')
        self.server_ssh.write(configuration)
        self.server_ssh.read_until_regexp('Please enter the \\*first\\* backup seed used to fill each node')
        self.server_ssh.write(str(start_seed))
        self.server_ssh.read_until_regexp('Please enter the \\*final\\* backup seed used to fill each node')
        self.server_ssh.write(str(end_seed))
        self.server_ssh.read_until_regexp('Would you like to begin the test')
        self.server_ssh.write('y')
        self.monitor_ssh = SSHConnection(self.server, 
                                         self.admin_user,
                                         self.admin_password,
                                         22,
                                         120,
                                         '')
        self.monitor_ssh.login()
        timeout = 608400
        elapsed = 0
        while elapsed < timeout:
            result = self.monitor_ssh.run_command('ps -ef | grep "acp\\.pl" | grep -v grep')
            if result[2] != 0:
                LOG.info('ACP test finished')
                break
            LOG.info('ACP test is running')
            LOG.info(self.server_ssh.read())
            time.sleep(300)
            elapsed += 300
        result = self.server_ssh.read()
        LOG.info('ACP test result: %s' % result)
        if 'ACP Test complete' in result:
            return True
        else:
            return False

    def create_directory(self, directory):
        '''
        Create directory on remote server.
        @directory: Directory path.
        '''
        cmd = 'mkdir -p %s' % directory
        result = self.server_ssh.run_command(cmd)
        if result[2] != 0:
            LOG.error('Failed to created directory: %s' % directory)
            return False
        LOG.info('Created directory: %s' % directory)
        return True

    def wipe_workdir(self, directory):
        '''
        Wipe work directory on remote server.
        @directory: Directory path.
        '''
        cmd = 'mv %s %s_%s; mkdir -p %s' % (directory, directory, self.ts, directory)
        # cmd = 'rm -rf %s/*' % directory
        result = self.server_ssh.run_command(cmd)
        if result[2] != 0:
            LOG.error('Failed to wipe work directory: %s' % directory)
            return False
        LOG.info('Wiped work directory: %s' % directory)
        return True

    def mapall_root(self, cmd):
        '''
        Execute mapall --user=root command.
        @cmd: The command to execute, if have special characters, need escape.
        '''
        cmd = r'echo %s | su - root -c "ssh-agent bash -c \"ssh-add /root/.ssh/rootid;mapall --user=root \'%s\'\""' \
            % (self.root_password, cmd)
        result = self.server_ssh.run_command(cmd)
        LOG.info('Run cmd: %s, result: %s' % (cmd, str(result)))
        return result[2]
