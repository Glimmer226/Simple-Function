#!/usr/bin/env python
# encoding=utf-8

import os
import re
from robot.errors import ExecutionFailed
from lib.base.RobotLogger import LOG
from lib.server.AvServer import AvServer


class ChdDump(AvServer):
    '''
    A class used for dump chd stripe.
    '''
    def __init__(self, ssh=None):
        '''
        Constructor
        '''
        self.ssh = ssh
        self.chd_dump_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.realpath(__file__))))),
            'tools', 'debug_utils', 'chddump')
        self.remote_dir = '/tmp/'
        self.remote_script = os.path.join(self.remote_dir, 'chddump')
        # Node list, such as 0.0, 0.1
        self.node_list = []
        # List of chd stripe files
        self.file_list = []
        # List of new generated chd stripe files
        self.new_file_list = []
        self.is_multi = False

    def get_node_list(self):
        '''
        Get node list of the server.
        avmaint ping --xmlperline=5 |  egrep "<nodelist" | grep ONLINE
            <nodelist id="0.2" state="ONLINE" count="54">
            <nodelist id="0.1" state="ONLINE" count="49">
            <nodelist id="0.0" state="ONLINE" count="58">
        '''
        cmd = 'avmaint ping --xmlperline=5 | egrep "<nodelist" | grep ONLINE'
        result = self.ssh.run_command(cmd)
        if result[2]:
            LOG.error('Fail to get node list.')
            raise ExecutionFailed('Fail to get node list.')
        for line in result[0].split('\n'):
            m = re.search(r'id="(\d\.\d{1,2})"', line)
            if m:
                self.node_list.append(m.group(1))
        if len(self.node_list) > 1:
            self.is_multi = True

    def scp_debug_script(self):
        '''
        Copy debug script to Avamar server.
        '''
        self.get_node_list()
        # Copy debug script to utility node first
        self.ssh.directory_should_exist(self.remote_dir)
        self.ssh.put_file(self.chd_dump_script,
                          destination=self.remote_dir,
                          mode='0755')

        # If multi-node, copy debug script to each data node
        eval_cmd = 'eval `ssh-agent`;eval `ssh-add ~/.ssh/dpnid`;'
        if self.is_multi:
            for node in self.node_list:
                scn_cmd = 'scn %s %s:%s' % (self.remote_script, node, self.remote_dir)
                cmd = eval_cmd + scn_cmd
                result = self.ssh.run_command(cmd)
                if result[2]:
                    LOG.error('Falied to copy debug script to node %s' % node)
                    return False
        LOG.info('Copy debug script to all nodes.')
        return True

    def chd_dump(self, node, chd_file):
        '''
        Run chddump script to dump stripe content.
        @node: Specifies the node, such as 0.0.
        @chd_file: The file path of chd stripe.
        '''
        eval_cmd = 'eval `ssh-agent`;eval `ssh-add ~/.ssh/dpnid`;'
        ssn_cmd = "ssn %s '%s %s'" % (node, self.remote_script, chd_file)
        cmd = eval_cmd + ssn_cmd
        result = self.ssh.run_command(cmd)
        if result[2]:
            LOG.error('Run chddump failed.')
            return False
        return result[0]

    def parse_chd_dump(self, node, chd_file):
        '''
        Parse chd stripe dump output.
        admin@a4t34:/tmp/>: ./chddump 0000000000000037.chd
        Chunk Descriptor File 0000000000000037.chd:
                    0   magic      = 0xdeadfeed
                    4   headersize = 128
                    8   seqno      = 0
                   12   count      = 32768
                   16   nbytes     = 262144
                   20   saltid     = 0
                   24   newsaltid  = 0
                   28   restoffset = 0
                   32   pad(96)    = 0

          Start of chunk descriptors

              file-off    id    offset nextoffset   size chunktype
                   128     1      4096       4572    476 0x87 (hascomphints recipe4)
                   136     2      4572       5408    836 0x87 (hascomphints recipe4)

        @node: Specifies the node, such as 0.0.
        @chd_file: The file path of chd stripe.
        '''
        dump_dict = {'header': {}, 'chunks': {}}
        res = self.chd_dump(node, chd_file)
        if not res:
            return False

        # Attributes in header
        attributes = ['magic', 'headersize', 'seqno', 'count', 'nbytes',
                      'saltid', 'newsaltid', 'restoffset', 'pad(96)']
        # Parse header
        for a in attributes:
            t = a.replace('(', '\(').replace(')', '\)')
            dump_dict['header'][a] = re.search('%s.*= (.*)' % t, res).group(1)

        # Parse chunk descriptors block
        fields = ['file-off', 'id', 'offset', 'nextoffset', 'size', 'chunktype']
        chk = re.findall('(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.*)', res)
        for c in chk:
            c_dict = dict(zip(fields, c))
            dump_dict['chunks'][c_dict['id']] = c_dict
        return dump_dict

    def get_chd_salt_id(self, node, chd_file):
        '''
        Get salt id of the chd stripe.
        @node: Specifies the node, such as 0.0.
        @chd_file: The file path of chd stripe.
        '''
        result = self.parse_chd_dump(node, chd_file)
        return int(result.get('header').get('saltid'))

    def get_chd_files(self):
        '''
        Get *.chd files on all nodes, meanwhile identify new
        generated stripe files since the last time.
        '''
        # Clear list of new stripe files
        self.new_file_list = []
        eval_cmd = 'eval `ssh-agent`;eval `ssh-add ~/.ssh/dpnid`;'
        for node in self.node_list:
            ssn_cmd = 'ssn %s \'find /data0?/cur -name "*.chd"\'' % node
            cmd = eval_cmd + ssn_cmd
            result = self.ssh.run_command(cmd)
            if result[2]:
                LOG.error('Fail to get chd file list on node %s.' % node)
                raise ExecutionFailed('Fail to get chd file on %s.' % node)
            for line in result[0].split('\n'):
                # Ignore other files
                if not line.endswith('.chd'):
                    continue
                # Ignore existing stripe files
                if (node, line) in self.file_list:
                    continue
                # Add new stripe files into two lists
                self.file_list.append((node, line))
                self.new_file_list.append((node, line))

    def get_new_chd_files(self):
        '''
        Return new generated chd stripe files
        '''
        return self.new_file_list
