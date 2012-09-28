import paramiko
import os

def deploy_mytardis_with_chef(settings, ip_address, instance_id):
    ssh = _open_connection(settings, ip_address)
    os.chdir("/home/centos/chef-repo")
    _set_up_chef_client(settings, ip_address, instance_id, ssh)
    
def _set_up_chef_client(settings, ip_address, instance_id, ssh):   
    command = "knife bootstrap %s -x %s -i %s --sudo"  % (ip_address, settings.USER_NAME, settings.PRIVATE_KEY)
    os.system(command)
    command = "yum install -y git"
    _run_sudo_command(ssh, command, settings, instance_id)
    command = "git clone https://github.com/mytardis/mytardis-chef.git\n\
    cd mytardis-chef\n\
    git branch -a\n\
    git checkout app_revert"
    _run_sudo_command(ssh, command, settings, instance_id)
    
    command = "scp -r -i %s /home/centos/chef-repo/.chef %s@%s:/home/centos/" % (settings.PRIVATE_KEY, settings.USER_NAME, ip_address)
    print command
    os.system(command)
    
    command = "knife configure client ./client-config\n\
    sudo  cp -r .chef/* /etc/chef/\n\
    knife client list\n\
    knife cookbook upload -o ./site-cookbooks/:./cookbooks/ -a -d\n\
    knife role from file /home/centos/mytardis-chef/roles/mytardis.json\n\
    knife node run_list add  %s 'role[mytardis]'" % instance_id
    _run_sudo_command(ssh, command, settings, instance_id)
    command = "sudo chef-client"
    _run_sudo_command(ssh, command, settings, instance_id)
    

def test_mytardis_deployment(settings, ip_address, instance_id):
    ssh = _open_connection(settings, ip_address)
    command = "cd /opt/mytardis/current\n\
    sudo -u mytardis bin/django test --settings=tardis.test_settings"
    res = _run_sudo_command(ssh, command, settings, instance_id)
    print res
       
    
def _open_connection(settings, ip_address):
    # open up the connection
    ssh = paramiko.SSHClient()
    # autoaccess new keys
    ssh.load_system_host_keys(os.path.expanduser(os.path.join("~",
                                                              ".ssh",
                                                              "known_hosts")))
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    #TODO: handle exceptions if connection does not work.
    # use private key if exists
    if os.path.exists(settings.PRIVATE_KEY):
        privatekeyfile = os.path.expanduser(settings.PRIVATE_KEY)
        mykey = paramiko.RSAKey.from_private_key_file(privatekeyfile)
        ssh.connect(ip_address, username=settings.USER_NAME, timeout=60, pkey=mykey)
    else:
        print("%s %s %s" % (ip_address, settings.USER_NAME, settings.PASSWORD))
        print(ssh)
        ssh.connect(ip_address, username=settings.USER_NAME,
                    password=settings.PASSWORD, timeout=60)

    #channel = ssh.invoke_shell().open_session()
    return ssh


def _run_sudo_command(ssh, command, settings, instance_id):

    chan = ssh.invoke_shell()
    chan.send('sudo -s\n')
    full_buff = ''
    buff = ''
    buff_size = 9999
    while not '[%s@%s ~]$ ' % (settings.USER_NAME, instance_id) in buff:
        resp = chan.recv(buff_size)
        #print("resp=%s" % resp)
        buff += resp
    #print("buff = %s" % buff)
    full_buff += buff

    chan.send("%s\n" % command)
    buff = ''
    while not '[root@%s %s]# ' % (instance_id, settings.USER_NAME) in buff:
        resp = chan.recv(buff_size)
        print(resp)
        buff += resp
    #print("buff = %s" % buff)
    full_buff += buff

    # TODO: handle stderr

    chan.send("exit\n")
    buff = ''
    while not '[%s@%s ~]$ ' % (settings.USER_NAME, instance_id) in buff:
        resp = chan.recv(buff_size)
        #print("resp=%s" % resp)
        buff += resp
   # print("3buff = %s" % buff)
    full_buff += buff

    chan.close()
    return (full_buff, '')

