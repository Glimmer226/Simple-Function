from subprocess import Popen, PIPE
from threading import Timer
import getopt
import sys
import time
import re
import os
import SSHLibrary
import paramiko
from robot.libraries.BuiltIn import BuiltIn


BI_AGENT = BuiltIn()

# ssh constants
ssh_key = "~/.ssh/dpnid"
ssh_opts = " -o BatchMode=yes -o StrictHostKeyChecking=no \
            -o UserKnownHostsFile=/dev/null "
ssh_cmd = "/usr/bin/ssh -x %s -i %s" % (ssh_opts, ssh_key)
sshOpt = "-oBatchMode=yes -oConnectTimeout=10 " + \
        "-oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null "

# normal string constants
qadepotMountPoint = "/qadepot"
pathAvamarSrc = "/data01/avamar/src/"
pathRepoPkg = "/data01/avamar/repo/packages/"
unzipBundleFolder = "AvamarBundle_SLES11_64/"
default_pass = "changeme"

# dictionary constant
termColor = {'red': '\033[1;31m',
             'cyan': '\033[36m',
             'lightcyan': '\033[1;36m',
             'blue': '\033[1;34m',
             'green': '\033[1;32m',
             'cyan_underline': '\033[4;36m',
             'off': '\033[0m'}
qadepot = {"irvine": "qadepot.avamar.com",
           "durham": "dudepot.asl.lab.emc.com"}
shellDict = {'shell': True, 'stdout': PIPE, 'stderr': PIPE}
support_keys = {'7.4.0': 'Supp0rtKen10',
                '7.3.0': 'Supp0rtJul6',
                '7.2.1': 'Supp0rtHarV1',
                '7.2.0': 'Supp0rtHarV1'}
avp_title = {'AvamarInstallSles': 'avamar-install-sles'}


# Disply '.' when wait for shell command running
def fastdot(interval=0.01, color=None):
    start = time.time()
    out = termColor[color] if color else ""
    out += ". "
    out += termColor['off'] if color else ""
    while True:
        now = time.time()
        while now - start > 1:
            start += 1
            sys.stdout.write(out)
            sys.stdout.flush()
        time.sleep(interval)
        yield


# a wrapper to run a shell command.
# by default, it will launch a shell cmd running locally.
# if the server is set, the shell cmd will be run remotely.
# a timeout value can be set optionally.
def runShell(cmd, server='local', user=None, timeout=60):
    if server != 'local':
        cmd = "sh -c \\\"%s\\\"" % cmd
        cmd = "ssh %s %s@%s %s" % (sshOpt, user, server, cmd)
    print cmd

    ssh = Popen(cmd, **shellDict)
    dot = fastdot(0.01, 'cyan')
    for _ in xrange(int(timeout / 0.01)):
        dot.next()

        if ssh.poll() is not None:
            break
    if ssh.poll() is None:
        print "shell timeout",
        ssh.kill()
    return filter(None, ssh.communicate()[0].split("\n"))


# mount qadepot on local host.
def mountQadepot(lab, server='local'):
    # check if qadepot is already mounted
    for line in runShell("mount | grep '%s' | grep '%s'" %
                         (qadepot[lab], qadepotMountPoint)):
        if line.startswith("%s:/qadepot on %s type nfs" %
                           (qadepot[lab], qadepotMountPoint)):
            print "The qadepot is already mounted."
            return True

    # mount qadepot
    output = runShell("mount -o nolock %s:/qadepot %s" %
                      (qadepot[lab], qadepotMountPoint))
    mounted = False
    for line in runShell("mount | grep '%s' | grep '%s'" %
                         (qadepot[lab], qadepotMountPoint)):
        if re.search("%s:/qadepot on %s type nfs" %
                     (qadepot[lab], qadepotMountPoint), line):
            mounted = True
    if mounted is False:
        print "Failed to mount qadepot on %s" % server
        BI_AGENT.fail("Failed to mount qadepot on %s" % server)
        return False
    return True



def scp_from_local_repository(file_name,server,user,target_path=pathAvamarSrc):
    print "The package to be copied: %s" % file_name
    cmd = "/bin/find /home/img/ -name \'%s\'" % (file_name)
    output = runShell(cmd,timeout=900)
    print output
    file_path = ""
    for line in output:
        if re.search(file_name, line):
            file_path = line.strip()
    print "\nThe file path: %s" % file_path
    if file_path == "":
        print "Failed to find the package"
        BI_AGENT.fail("Failed to find the package!")
        return False

    # scp the file to target server
    cmd = "scp %s %s %s@%s:%s" % \
          (ssh_opts, file_path, user, server, target_path)
    runShell(cmd, timeout=900)
    print "Copy the file %s successfully!" % file_name

    return True


# scp a avp package into remote server.
# by default, it will put into /data01/avamar/src
# the specified path can be set also.
def scpFromQadepot(file_name, server, user, target_path=pathAvamarSrc):
    print "The package to be copied: %s" % file_name

    # check if the package exists
    cmd = "/bin/find %s/builds/ -name \'%s\'" % \
          (qadepotMountPoint, file_name)
    output = runShell(cmd,timeout=900)
    file_path = ""
    for line in output:
        if re.search(file_name, line):
            file_path = line.strip()
    print "\nThe file path: %s" % file_path
    if file_path == "":
        print "Failed to find the package"
        BI_AGENT.fail("Failed to find the package!")
        return False

    # scp the file to target server
    cmd = "scp %s %s %s@%s:%s" % \
          (ssh_opts, file_path, user, server, target_path)
    runShell(cmd, timeout=900)

    # validate the copied package
    cmd = "md5sum " + target_path + "/" + file_name
    remote_output = runShell(cmd, server, user, timeout=300)
    tmp_arr = remote_output[0].split()
    remote_md5 = tmp_arr[0].strip()
    if remote_md5 == "":
        print "Failed to get the md5sum in remote!"
        BI_AGENT.fail("Failed to get the md5sum in remote!")
        return False
    print "Remote md5sum for %s: %s" % (file_name, remote_md5)

    # get the local md5sum
    cmd = "cat " + file_path + ".md5sum | awk \'{ print $1}\'"
    local_output = runShell(cmd)

    local_md5 = local_output[0].strip()
    if local_md5 == "":
        print "Failed to get the md5sum in local!"
        BI_AGENT.fail("Failed to get the md5sum in local!")
        return False
    print "Local md5sum for %s: %s" % (file_name, local_md5)

    if remote_md5 != local_md5:
        print "The md5sum doesn't match."
        BI_AGENT.fail("The md5sum doesn't match.")
        return False
    print "Copy the file %s successfully!" % file_name

    return True


# to ssh login with 'admin' account and without password.
# the key in dpnid is required.
# this function is just a pre-check for that key.
def sshCheck():
    noAgent = "Could not open a connection to your authentication agent."
    output = runShell("ssh-add -l")
    for line in output:
        if re.search("dpnid", line):
            return True
        if re.search(noAgent, line):
            print "ssh-agent is not running"
    print "dpnid ssh key is not found"
    # there is no checking for return value, exit directly
    BI_AGENT.fail("dpnid ssh key is not found")
    sys.exit(1)


# check if the local server can login to remote server without password.
# in normal cases, the user can be 'admin' and 'root'.
def checkLogin(server, user):
    if any(line.startswith(server) for line in
           runShell("hostname -f", server, user)):
        print "Acount %s can login to %s without password" % (user, server)
        return True
    return False


# copy the local id_rsa.pub key to remote authorized_key file.
# then the user can login to remote server without password.

def enableLoginWithoutPasswd(server, user, passwd):
    check_login = checkLogin(server, user)
    if check_login is True:
        return
    cmd = "cd ~/;pwd"
    output = Popen([cmd], stdout=PIPE, shell=True)
    pwd = output.stdout.read().strip()
    # get the local root id_rsa.pub key
    rsa_pub_file = pwd + '/.ssh/id_rsa.pub'
    if not os.path.isfile(rsa_pub_file):
        print "The local id_rsa.pub file does not exist!"
        sys.exit(1)
    cmd = "/bin/cat " + rsa_pub_file
    output = Popen(cmd, **shellDict)
    rsa_pub_key = output.stdout.read().strip()

    # as the authorized_key file may have different names
    # get the authorized_key file name first.
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=user, password=passwd, look_for_keys=False, allow_agent=False)
        stdin, stdout, stderr = ssh.exec_command('find ~/.ssh/ -name \"*authorized_key*\"')
        stdout = stdout.readlines()
        print stdout
        remote_auth_file = ''
        for line in stdout:
            if re.search('authorized_key', line.strip()):
                remote_auth_file = line.strip()
                print "the line: %s" % remote_auth_file
            
        if remote_auth_file == '':
            print "Failed to find the authorized key file!"
        print "remote auth file %s" % remote_auth_file
        
        if user == 'admin':
            cmd = "echo \'" + passwd + "\' | su -c \'echo \"" + \
              rsa_pub_key + "\" >> " + remote_auth_file + "\' root"
            prompt = '~/>:'
        else:
            cmd = "echo \'" + rsa_pub_key + "\' >> " + remote_auth_file
            prompt = '~/#:'    
        stdin, stdout, stderr = ssh.exec_command(cmd)
        print stdout
        ssh.close()
        return True
    except IOError,e:
        print e
        return False

    check_login = checkLogin(server, user)
    if check_login is False:
        return False

# enable/disable root access for remote server
def handleRootAccess(server, passwd, action='enable'):
    ssh = SSHLibrary.SSHLibrary()
    ssh.open_connection(server)
    # can only use 'admin' account to enable 'root' account
    ssh.login('admin', passwd)
    ssh.write("su -")
    ssh.read_until("Password")
    ssh.write(passwd)
    output = ssh.read_until("/#:")
    if action == 'enable':
        cmd = "sed -i s/^'PermitRootLogin no'/'PermitRootLogin yes'/\
               /etc/ssh/sshd_config"
    else:
        cmd = "sed -i s/^'PermitRootLogin yes'/'PermitRootLogin no'/\
               /etc/ssh/sshd_config"
    ssh.write(cmd)
    ssh.read_until("/#:")
    cmd = "/etc/init.d/sshd restart"
    ssh.write(cmd)
    ssh.read_until("/#:")
    ssh.close_all_connections()


# prepare the login env:
# 1. check if the dpnid is loaded
# 2. enable root access
# 3. enable 'admin' login without password
# 4. enable 'root' login without password
def prepareLogin(server, passwd=default_pass):
    sshCheck()
    handleRootAccess(server, passwd, 'enable')
    enableLoginWithoutPasswd(server, 'admin', passwd)
    enableLoginWithoutPasswd(server, 'root', passwd)


# install avinstaller. the steps:
# 1. copy the AvamarBundle_SLES11_64 to remote server.
# 2. unzip the bundle file.
# 3. execute avinstaller-bootstrap shell script.
# 4. check output
def install_bootstrap(server, version, lab):

    prepareLogin(server)

    bundle_file = "AvamarBundle_SLES11_64-" + version + ".zip"

    # Check qadepot in local host
    ret = mountQadepot(lab)
    if ret is False:
        return ret

    # copy the Bundle zip file to target server
    ret = scpFromQadepot(bundle_file, server, 'root')
    if ret is False:
        return ret

    # install the bootstrap
    # unzip the Bundle first
    cmd = "unzip %s\%s -d %s" % (pathAvamarSrc, bundle_file, pathAvamarSrc)
    output = runShell(cmd, server, 'root')

    # verify the avinstaller bootstrap was extracted successfully
    # avinstaller name
    avinstaller = "avinstaller-bootstrap-" + version + ".sles11_64.x86_64.run"
    found = False
    for line in output:
        print line
        if re.search(avinstaller, line):
            found = True
            print "Succeeded to extract avinstaller installable pkg."
            break

    if found is False:
        print "Failed to extract avinstaller installable pkg."
        BI_AGENT.fail("Failed to extract avinstaller installable pkg.")
        return False
    cmd = pathAvamarSrc + unzipBundleFolder + avinstaller
    output = runShell(cmd, server, 'root', timeout=90)

    # verify the output
    found = False
    for line in output:
        print line
        if re.search('Installation of SLES11 Bootstrap RPMs completed', line):
            print "Secceeded to install avinstaller."
            found = True

    if found is False:
        print "Failed to install avinstaller installable."
        BI_AGENT.fail("Failed to install avinstaller installable.")
        return False

    return True


# during avp installation, the avp status would be checked in multiple
# times. this function would check if the expected status happen.
def checkAVPStatus(server, version, title, passwd, expect_status):
    # get the major version, i.e: 7.4.0
    tmp_arr = version.split('-')
    maj_ver = tmp_arr[0]

    # change the version format, because listhistory will display version
    # as 7.4.0.xx
    version = version.replace('-', '.')

    # check if the avp is expected status
    try_num = 0
    match = False
    while True:
        try_num = try_num + 1
        time.sleep(5)
        print "waiting for status of package..."
        cmd = "avi-cli %s --password %s --supportkey %s --listhistory " \
              "|grep \'%s\' | grep \'%s\'" % (server, passwd,
                                              support_keys[maj_ver],
                                              title, version)
        output = runShell(cmd)
        for line in output:
            if re.search(expect_status, line):
                print line
                print "The status for %s is %s" % (title, expect_status)
                match = True
        if match is True:
            break

        # timeout after 5 minutes
        if try_num > 60:
            print "Timeout for checking AVP status"
            break

    if match is False:
        print "Failed to the status for %s." % title
        BI_AGENT.fail("Failed to the status for %s." % title)
        return False

    return True


# with avi-cli, install a avp package.
# by design, this function can be used to install other avp package.
# not only AvamarInstallSles
def installAvpViaAviCli(server, version, avp_name, passwd, yaml_file):
    # becuase the AVP name is different from
    # avp title. we need to get the avp type firstly,
    # then map to the avp title
    tmp_arr = avp_name.split('-')
    avp_type = tmp_arr[0]
    print "The AVP type is %s" % avp_type

    # get the major version, i.e: 7.4.0
    tmp_arr = version.split('-')
    maj_ver = tmp_arr[0]
    print "The major version is %s" % maj_ver

    # TBD: should use default_pass here?
    # check the avp is ready
    ret = checkAVPStatus(server, version, avp_title[avp_type],
                         default_pass, 'ready')
    if ret is False:
        return ret

    # install the avp
    cmd = "avi-cli %s --password %s --supportkey %s --install %s --userinput" \
          " %s" % (server, default_pass, support_keys[maj_ver],
                   avp_title[avp_type], yaml_file)
    print cmd
    proc = Popen(cmd, **shellDict)
    proc_kill = lambda p: p.kill()
    try:
        # in case the hanging happen,
        # the process will be killed after 90 minutes.
        timer = Timer(5400, proc_kill, [proc])
        timer.start()
        for line in iter(proc.stdout.readline, ""):
            print line.strip()
    finally:
        timer.cancel()

    # check the installation is completed
    ret = checkAVPStatus(server, version, avp_title[avp_type],
                         passwd, 'completed')
    return ret


# check the avamar server is up
def checkAvamarSanity(server, passwd):

    check_points = ['gsan status: up',
                    'MCS status: up',
                    'emt status: up',
                    'Backup scheduler status: up',
                    'Maintenance windows scheduler status: suspended',
                    'Unattended startup status: enabled',
                    'avinstaller status: up',
                    'ddrmaint-service status: up']

    # sleep 30 to wait avinstaller up
    time.sleep(30)

    # there are some issue with runShell for 'dpnctl status'
    # so here using SSHLibrary
    ssh = SSHLibrary.SSHLibrary(timeout=120)
    ssh.open_connection(server)
    ssh.login('admin', passwd)
    ssh.write('dpnctl status')
    output = ssh.read_until("~/>")
    output_arr = output.split('\n')
    ssh.close_all_connections()

    failures = []

    for checkpoint in check_points:
        found = False
        for line in output_arr:
            if re.search(checkpoint, line):
                found = True
                break
        if found is False:
            failures.append(checkpoint)
    # print the results
    print "DPN status:"
    for line in output_arr:
        if not re.search('~/>', line):
            print line

    if len(failures) >= 1:
        print "The following checkpoints have some problems:"
        for checkpoint in failures:
            print checkpoint
        BI_AGENT.fail("Error happened in sanity checking!")
        return False
    return True


# install avamar avp package. the steps:
# 1. copy the avamar avp package into /data01/avamar/repo/packages.
# 2. check if the avp is accepted.
# 3. with avi-cli, install avp with yaml file.
# 4. check if the installation completes.
def install_av_avp(server, version, lab, new_passwd, yaml_file):
    # check the login
    prepareLogin(server)

    # combine the pkg name
    avp_name = "AvamarInstallSles-%s.avp" % version
    print "The AVP package to be installed: %s" % avp_name

    # Check qadepot in local host
    ret = mountQadepot(lab)
    if ret is False:
        return False

    # copy the avp package into repo/packages folder
    ret = scpFromQadepot(avp_name, server, 'root', pathRepoPkg)
    if ret is False:
        return False

    # install a avp via avi-cli
    ret = installAvpViaAviCli(server, version, avp_name, new_passwd, yaml_file)

    if ret is True:
        print "Succeeded to install %s" % avp_name
        handleRootAccess(server, new_passwd, 'disable')
    else:
        # if failed to install avamar, it won't disable root for debugging
        print "Failed to install %s" % avp_name
        BI_AGENT.fail("Failed to install %s" % avp_name)
        return False

    # Check DPN status
    ret = checkAvamarSanity(server, new_passwd)
    return ret
