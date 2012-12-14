from optparse import OptionParser
import getopt

import os
import sys
import time

import logging

from botocloudconnector import create_cloud_connection
from botocloudconnector import create_VM_instance
from botocloudconnector import destroy_VM_instance
from botocloudconnector import get_this_instance

from chefclient import deploy_mytardis_with_chef
from chefclient import test_mytardis_deployment
from chefclient import is_ssh_ready


def start():
    #http://docs.python.org/howto/logging.html#logging-basic-tutorial
    '''
    logging.config.fileConfig('logging.conf')
    '''
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config_file = os.path.expanduser("~/.mytarids-on-nectar/settings")
    if os.path.exists(config_file):
        config.read(config_file)
    else:
        config_file = os.path.expanduser("settings")  # a default config file
        if os.path.exists(config_file):
            config.read(config_file)
        else:
            print("No configuration file found")
            sys.exit(1)

    environ_fields = ['USER_NAME', 'PASSWORD', 'PRIVATE_KEY',
                      'VM_SIZE', 'VM_IMAGE', 'VM_NAME', 'CUSTOM_PROMPT',
                      'SLEEP_TIME', 'RETRY_ATTEMPTS',
                      'EC2_ACCESS_KEY', 'EC2_SECRET_KEY',
                      'CLOUD_SLEEP_INTERVAL', 'PRIVATE_KEY_NAME',
                      'SECURITY_GROUP', 'PATH_CHEF_CONFIG',
                      'MYTARDIS_BRANCH_URL', 'MYTARDIS_BRANCH_NAME']

    import json
    settings = type('', (), {})()
    for field in environ_fields:
        #TODO: add multiple sections
        val = config.get("basic", field)
        if '#' in val:  # remove comments
            val, _ = val.split('#', 1)
        try:
            field_val = json.loads(val)    # use JSON to parse values
        except ValueError, e:
            file_val = ""
        # and make fake object to hold them
        setattr(settings, field, field_val)
        #print("%s %s" % (field, field_val))

    try:
        opts, args = getopt.getopt(sys.argv[1:], "cm:t:d:",
                                   ["create=", "mytardis", "test", "destroy"])
    except getopt.GetoptError:
   #print help info and exit:
        print("Couldn't parse arguments")
        exit(1)

    step = ""
    ip_address = ""
    for opt, val in opts:
        if opt in ("-c", "--create"):
            step = "create"
        if opt in ("-m", "--mytardis"):
            step = "mytardis"
            ip_address = val
        if opt in ("-t", "--test"):
            step = "test"
            ip_address = val
        if opt in ("-d", "--destroy"):
            step = "destroy"
            ip_address = val

    if step == "create":
        create_VM_instance(settings)

    elif step == "mytardis":
        instance = get_this_instance(settings,
            ip_address, ip_given=True)
        if instance:
            deploy_mytardis_with_chef(settings,
                ip_address, instance.id)
        else:
            print "VM with IP [%s] doesn't exist" % ip_address


    elif step == "test":
        instance = get_this_instance(settings,
            ip_address, ip_given=True)
        if instance:
            test_mytardis_deployment(settings,
                ip_address, instance.id)
        else:
            print "VM with IP [%s] doesn't exist" % ip_address

    elif step == "destroy":
        destroy_VM_instance(settings, ip_address)

    else:
        print "Unknown Option"


if __name__ == '__main__':
    begins = time.time()
    start()
    ends = time.time()
    print("Total execution time: %d seconds" % (ends - begins))
