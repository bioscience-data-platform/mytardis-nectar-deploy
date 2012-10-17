import os
import sys
from time import sleep
import traceback
import ssh
import socket


def deploy_mytardis_with_chef(settings, ip_address, instance_id):
    ssh_client = _open_connection(settings, ip_address)
    os.chdir(settings.PATH_CHEF_CONFIG)
    _set_up_chef_client(settings, ip_address, instance_id, ssh_client)
    
    
def _set_up_chef_client(settings, ip_address, instance_id, ssh_client):  
    command = "knife bootstrap %s -x %s -i %s --sudo"  % (ip_address, settings.USER_NAME, settings.PRIVATE_KEY)
    os.system(command)
    command = "yum install -y git"
    _run_sudo_command(ssh_client, command, settings, instance_id)
    command = "git clone %s\n\
    cd mytardis-chef\n\
    git branch -a\n\
    git checkout %s" % (settings.MYTARDIS_BRANCH_URL, settings.MYTARDIS_BRANCH_NAME)
    _run_sudo_command(ssh_client, command, settings, instance_id)
    
    returned_working_directory = run_command(ssh_client, 'pwd')[0]
    working_directory = returned_working_directory.split("\n")[0]
    print "Working dir %s" % working_directory
    command = "scp -r -i %s %s %s@%s:%s/" % (settings.PRIVATE_KEY, 
                                             settings.PATH_CHEF_CONFIG, 
                                             settings.USER_NAME, 
                                             ip_address, 
                                             working_directory)
    print command
    os.system(command)
    
    command = "knife configure client ./client-config\n"
    _run_sudo_command(ssh_client, command, settings, instance_id)
    command = "unalias cp \n cp -rf .chef/* /etc/chef/\n"
    _run_sudo_command(ssh_client, command, settings, instance_id)
    command = "knife client list\n"
    _run_sudo_command(ssh_client, command, settings, instance_id)
    command = "knife cookbook upload -o ./site-cookbooks/:./cookbooks/ -a -d\n"
    _run_sudo_command(ssh_client, command, settings, instance_id)
    command = "knife role from file %s/mytardis-chef/roles/mytardis-bdp-milestone1.json\n\
    " % working_directory
    _run_sudo_command(ssh_client, command, settings, instance_id)
    command = "knife node run_list add  %s 'role[mytardis-bdp-milestone1]'" % instance_id
    _run_sudo_command(ssh_client, command, settings, instance_id)
    command = "chef-client"
    _run_sudo_command(ssh_client, command, settings, instance_id)
    

def test_mytardis_deployment(settings, ip_address, instance_id):
    ssh_client = _open_connection(settings, ip_address)
    command = "cd /opt/mytardis/current\n\
    sudo -u mytardis bin/django test --settings=tardis.test_settings"
    res = _run_sudo_command(ssh_client, command, settings, instance_id)
    #print res
       
def is_ssh_ready(settings, ip_address):
    ssh_ready = False
    while not ssh_ready:
        try:
            _open_connection(settings, ip_address)
            ssh_ready = True
        except socket.error:
            sleep(settings.CLOUD_SLEEP_INTERVAL)
            print ("Connecting to %s in progress ..." % ip_address)
            #traceback.print_exc(file=sys.stdout)
        except ssh.AuthenticationException:
            sleep(settings.CLOUD_SLEEP_INTERVAL)
            print ("Connecting to %s in progress ..." % ip_address)
        except ssh.SSHException:
            sleep(settings.CLOUD_SLEEP_INTERVAL)
            print ("Connecting to %s in progress ..." % ip_address)            
    return ssh_ready


def customize_prompt(settings, ip_address):
    print("Customizing prompt ... %s " % settings.CUSTOM_PROMPT)
    ssh_ready = is_ssh_ready(settings, ip_address)
    if ssh_ready:
        ssh_client = _open_connection(settings, ip_address)
        home_dir = os.path.expanduser("~")
        command_bash = 'echo \'export PS1="%s"\' >> .bash_profile' % settings.CUSTOM_PROMPT
        command_csh = 'echo \'setenv PS1 "%s"\' >> .cshrc' % settings.CUSTOM_PROMPT
        command = 'cd ~; %s; %s' % (command_bash, command_csh)
        res = run_command(ssh_client, command)
    else:
        print "Unable to customize command prompt for VM instance %s" % (instance_id, ip)


def delete_chef_node_client(settings, instance_id, ip_address):
    ssh_client = _open_connection(settings, ip_address)
    command = "knife node delete -y %s\n" % instance_id
    _run_sudo_command(ssh_client, command, settings, instance_id)
    command = "knife client delete -y %s\n" % instance_id
    _run_sudo_command(ssh_client, command, settings, instance_id)
    

def _open_connection(settings, ip_address):
    # open up the connection
    ssh_client = ssh.SSHClient()
    # autoaccess new keys
    ssh_client.load_system_host_keys(os.path.expanduser(os.path.join("~",
                                                              ".ssh",
                                                              "known_hosts")))
    ssh_client.set_missing_host_key_policy(ssh.AutoAddPolicy())
    
    #TODO: handle exceptions if connection does not work.
    # use private key if exists
    if os.path.exists(settings.PRIVATE_KEY):
        privatekeyfile = os.path.expanduser(settings.PRIVATE_KEY)
        #mykey = ssh_client.RSAKey.from_private_key_file(privatekeyfile)
        ssh_client.connect(ip_address, username=settings.USER_NAME, timeout=60, key_filename=privatekeyfile)#, pkey=mykey)
    else:
        print("%s %s %s" % (ip_address, settings.USER_NAME, settings.PASSWORD))
        print(ssh_client)
        ssh_client.connect(ip_address, username=settings.USER_NAME,
                    password=settings.PASSWORD, timeout=60)
    
    #channel = ssh.invoke_shell().open_session()
    return ssh_client


def run_command(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    res = stdout.readlines()
    print("run_command_stdout=%s" % res)
    return res


def _run_sudo_command(ssh_client, command, settings, instance_id):
    print command
    chan = ssh_client.invoke_shell()
    chan.send('sudo -s\n')
    full_buff = ''
    buff = ''
    buff_size = 9999
    while not settings.CUSTOM_PROMPT in buff:
        resp = chan.recv(buff_size)
        #print("resp=%s" % resp)
        buff += resp
        print resp
    #print("buff = %s" % buff)
    full_buff += buff

    chan.send("%s\n" % command)
    buff = ''
    while not settings.CUSTOM_PROMPT in buff:
        resp = chan.recv(buff_size)
        print(resp)
        buff += resp
    #print("buff = %s" % buff)
    full_buff += buff

    # TODO: handle stderr

    chan.send("exit\n")
    buff = ''
    while not settings.CUSTOM_PROMPT in buff:
        resp = chan.recv(buff_size)
        #print("resp=%s" % resp)
        buff += resp
        print resp
   # print("3buff = %s" % buff)
    full_buff += buff

    chan.close()
    print full_buff
    return (full_buff, '')
