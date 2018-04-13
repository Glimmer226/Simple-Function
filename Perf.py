#!/usr/bin/env python
# encoding=utf-8

import os
import re
import json
import datetime
import Utils
from lib.base.RobotLogger import LOG
from lib.base.SSHConnection import SSHConnection
from lib.client.Avtar import Avtar
from lib.client.DataGen import DataGen
from lib.mc.MCCLI import MCCLI


class Perf(object):
    '''
    A class used for testing backup, restore, replicate performance.
    This class use the avtar on utility node to do backup, restore job.
    '''
    def __init__(self):
        self.ts = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.log_dir = '/home/admin/performance/backup/%s' % self.ts
        self.test_summary = '/tmp/performance_test_summary_%s.json' % self.ts
        self.summary = {}
        self.backup_speed = 0
        self.restore_speed = 0
        self.replicate_speed = 0
        # No DD attached by default, all tests run on Avamar
        self.ddr = False

    def perf_dataset(self, size, size_unit, count):
        '''
        Set the data size and pattern, all the following performance testing
        will operate on the same data set.
        @size: Size of backup without unit.
        @size_unit: File size unit, the value can be one of 'KB', 'MB', 'GB', 'TB'.
        @count: The count of files to backup.
        '''
        self.size = float(size)
        self.size_unit = size_unit
        self.count = int(count)
        self.total_size = self.size * self.count
        self.units = ['KB', 'MB', 'GB', 'TB']
        if size_unit not in self.units:
            raise Exception('Wrong file size unit, the legal values collection is %s.' % self.units)
        self.size_str = '%s %s' % (self.size, self.size_unit)
        self.total_size_str = '%s %s' % (self.total_size, self.size_unit)

    def perf_attach_server(self, server, admin_user, admin_password, root_user, root_password):
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
        self.server_ssh = SSHConnection(server, admin_user,
                                        admin_password, 22, timeout=36000, prompt='')
        self.server_ssh.login()
        Utils.create_directory(self.server_ssh, self.log_dir)
        self.set_server_preconditions()

    def perf_attach_client(self, client, client_user, client_password):
        '''
        Attach the client's information to Perf instance.
        @client: Client host.
        @client_user: Client user account.
        @client_password: Client account password.
        '''
        self.client = client
        self.avtar = Avtar(client, client_user, client_password)
        self.dg = DataGen(client, client_user, client_password)
        self.dg.init_datagen()
        self.client_ssh = SSHConnection(client, client_user,
                                        client_password, 22, prompt='')
        self.client_ssh.login()
        Utils.create_directory(self.client_ssh, self.log_dir)

    def perf_check_account(self, account):
        '''
        Check for client account used for avtar, create account if not exist.
        @account: Specifies a hierarchical LOCATION on the Avamar server.
                  If use avtar on Avamar server, need create an account.
                  Otherwise, account will be created once the client
                  registered, should be domain plus client name.
        '''
        ret = 1
        self.account = account
        cmd = 'avmgr getu --account=%s' % account
        result = self.server_ssh.run_command(cmd)
        LOG.info('Get account result: %s' % result)

        # Creating client account if not exist
        if result[2] != 0:
            domains = filter(None, account.split('/'))
            for domain in domains[:-1]:
                cmd = 'avmgr newd --account=%s' % domain
                result = self.server_ssh.run_command(cmd)
                # User or account already exists
                if result[2] == 6:
                    continue
                elif result[2] != 0:
                    LOG.error('Create account failed, %s' % result)
                    return False
            cmd = 'avmgr newm --account=%s' % account
            result = self.server_ssh.run_command(cmd)
            LOG.info('Create account result: %s' % result)
            ret = result[2]
        # Remove the existing data for the client account
        else:
            ret = self.avtar.delete_all_backups(self.server, self.root_user, self.root_password, self.account)
        return False if ret else True
    
    def perf_attach_dd(self, ddhost, ddboostuser, ddpwd):
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

    def perf_delete_dd(self, ddhost):
        '''
        Delete DD from the Avamar server.
        @ddhost: Specifies which Data Domain system to delete.
        '''
        return self.mccli.run_mccli_del_dd(self.server_ssh, ddhost, force=True)

    def perf_backup(self):
        '''
        Fill the Avamar server with some data and calculate backup rate.
        '''
        elapsed_minutes = []
        for index in range(self.count):
            data_set = '/home/admin/data_set/backup'
            log_file = 'avtar_backup_%s%s_%s.log' % (self.size, self.size_unit, index)
            log_file = os.path.join(self.log_dir, log_file)
            options = '--logfile=%s --nocache=true' % log_file
            if self.ddr:
                options += ' --ddr --ddr-index=%s' % self.ddr_index
            self.dg.generate_file(data_set, self.size, self.size_unit, 1)
            res = self.avtar.create_backup(self.server,
                                           self.root_user,
                                           self.root_password,
                                           self.account,
                                           data_set,
                                           options=options)
            self.dg.remove_data(data_set)
            if res != 0:
                LOG.error('Backup file failed.')
                return False
            elapsed = self.analyze_log(self.client_ssh, log_file)
            if elapsed is None:
                LOG.error('Can not get elapsed time from log file.')
                return False
            speed = self.calculate_speed(self.size, elapsed)
            LOG.info('[%s] Backed-up %s %s in %s minutes: %s GB/hour.'
                     % (index + 1, self.size, self.size_unit, elapsed, speed))
            elapsed_minutes.append(elapsed)
        overall_elapsed = sum(elapsed_minutes)
        overall_speed = self.calculate_speed(self.total_size, overall_elapsed)
        self.backup_elapsed = overall_elapsed
        self.backup_speed = overall_speed
        self.summary['Backup'] = {'Type': 'Backup',
                                  'File Size': self.size_str,
                                  'File Count': self.count,
                                  'Total Size': self.total_size_str,
                                  'Test Time (mins)': overall_elapsed,
                                  'Rate (GB/Hr)': overall_speed}
        LOG.info('Backed-up %s %s in %s minutes: %s GB/hour.' %
                 (self.total_size, self.size_unit, overall_elapsed, overall_speed))
        return True

    def perf_restore(self):
        '''
        Extract from Avamar server with some data and calculate restore rate.
        '''
        elapsed_minutes = []
        restore_dir = '/home/admin/data_set/restore'
        sn_list = self.avtar.get_backup_sequence_number(self.server,
                                                        self.root_user,
                                                        self.root_password,
                                                        self.account)

        for index, sn in enumerate(sn_list[0: self.count]):
            self.dg.remove_data(restore_dir, force=True)
            Utils.create_directory(self.client_ssh, restore_dir)
            log_file = 'avtar_restore_%s.log' % sn
            log_file = os.path.join(self.log_dir, log_file)
            res = self.avtar.extract_backup(self.server,
                                            self.root_user,
                                            self.root_password,
                                            self.account,
                                            sequence_number=sn,
                                            target=restore_dir,
                                            options='--logfile=%s' % log_file)

            if res != 0:
                LOG.error('Restore file failed, sequence number %s.' % sn)
                return False
            elapsed = self.analyze_log(self.client_ssh, log_file)
            if elapsed is None:
                LOG.error('Can not get elapsed time from log file.')
                return False
            speed = self.calculate_speed(self.size, elapsed)
            LOG.info('[%s] Restored %s %s in %s minutes: %s GB/hour.'
                     % (index + 1, self.size, self.size_unit, elapsed, speed))
            elapsed_minutes.append(elapsed)
        overall_elapsed = sum(elapsed_minutes)
        overall_speed = self.calculate_speed(self.total_size, overall_elapsed)
        self.restore_elapsed = overall_elapsed
        self.restore_speed = overall_speed
        self.summary['Restore'] = {'Type': 'Restore',
                                   'File Size': self.size_str,
                                   'File Count': self.count,
                                   'Total Size': self.total_size_str,
                                   'Test Time (mins)': overall_elapsed,
                                   'Rate (GB/Hr)': overall_speed}
        LOG.info('Restored %s %s in %s minutes: %s GB/hour.' %
                 (self.total_size, self.size_unit, overall_elapsed, overall_speed))
        self.dg.remove_data(restore_dir, force=True)
        return True

    def perf_replicate(self, dst_server, dst_user, dst_password):
        '''
        Run basic replicate to destination Avamar server and calculate speed.
        avrepl --operation=replicate --hfsaddr=src_addr --id=root --ap=Chang3M3Now.
        --dstaddr=dst_addr --dstid=repluser --dstap=Chang3M3Now. --dpnname=src_addr
        --[replscript]dstencrypt=tls --logfile=/tmp/replicate.log account 2>&1
        @dst_server: Destination server.
        @dst_user: Destination server repl user.
        @dst_password: Destination server repl user password.
        '''
        log_file = os.path.join(self.log_dir, 'replicate.log')
        cmd = 'avrepl --operation=replicate --hfsaddr=%s --id=%s ' \
            '--ap=%s --dstaddr=%s --dstid=%s --dstap=%s --dpnname=%s ' \
            '--[replscript]dstencrypt=tls %s > %s 2>&1' \
            % (self.server, self.root_user, self.root_password, dst_server,
               dst_user, dst_password, self.server, self.account, log_file)
        result = self.server_ssh.run_command(cmd)
        if result[2] != 0:
            LOG.error('Replicate to %s failed, please check log file %s.' % (dst_server, log_file))
            LOG.error('Return result: %s' % str(result))
            return False
        elapsed = self.analyze_log(self.server_ssh, log_file)
        if elapsed is None:
            LOG.error('Can not get elapsed time from log file.')
            return False
        speed = self.calculate_speed(self.total_size, elapsed)
        self.replicate_elapsed = elapsed
        self.replicate_speed = speed
        self.summary['Replicate'] = {'Type': 'Replicate',
                                     'File Size': self.size_str,
                                     'File Count': self.count,
                                     'Total Size': self.total_size_str,
                                     'Test Time (mins)': elapsed,
                                     'Rate (GB/Hr)': speed}
        LOG.info('Replicated %s %s in %s minutes: %s GB/hour.'
                 % (self.total_size, self.size_unit, elapsed, speed))
        return True

    def show_summary_result(self):
        '''
        Show summary result of backup, restore, replicate speed.
        Save summary result in json format on server.
        '''
        LOG.info('Log directory: %s' % self.log_dir)
        LOG.info('Data set size: %s %s' % (self.total_size, self.size_unit))
        LOG.info('Backup speed: %s GB/hour' % self.backup_speed)
        LOG.info('Restore speed: %s GB/hour' % self.restore_speed)
        LOG.info('Replicate speed: %s GB/hour' % self.replicate_speed)
        with open (self.test_summary, 'wb') as fp:
            json.dump(self.summary, fp)

    def set_server_preconditions(self):
        '''
        Set any server preconditions before running the tests
        '''
        LOG.info('Stop maintenance windows')
        result = self.server_ssh.run_command('avmaint sched stop --ava')
        LOG.info('Result: %s' % result)

    def analyze_log(self, ssh_connection, log_file):
        '''
        Analyze log to get statistics.
        @ssh_connection: Ssh connection to remote server.
        @log_file: Log file to be analyzed.
        '''
        result = ssh_connection.run_command('tail -50 %s' % log_file)
        if result[2] == 0:
            for line in result[0].split('\n'):
                # avtar Info <6083>: Backed-up 1.281 GB in 2.59 minutes: 30 GB/hour (413,108 files/hour)
                if '<6083>' in line or '<6090>' in line:
                    m = re.search(r'(Backed-up|Restored) .+ in (\S+) minutes', line)
                    if m:
                        elapsed = float(m.group(2))
                        return elapsed

    def calculate_speed(self, size, elapsed):
        """
        Calculate avtar backup or restore speed (GB/hour).
        @size: Size of backup without unit.
        @elapsed: Elapsed time (minutes) for avtar job.
        """
        return round(float(size) * (1024 ** (self.units.index(self.size_unit) - 2)) / (elapsed / 60.0), 2)
