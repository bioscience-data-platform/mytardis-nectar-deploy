#import paramiko
import time

import boto
from boto.ec2.connection import EC2Connection
from boto.ec2.regioninfo import *


def create_cloud_connection(settings):
    region = RegionInfo(name="NeCTAR", endpoint="nova.rc.nectar.org.au")
    #logger.debug("Connecting to region... %s" % region)
    print("Connecting to region... %s" % region)
    connection = boto.connect_ec2(
                                  aws_access_key_id=settings.EC2_ACCESS_KEY,
                                  aws_secret_access_key=settings.EC2_SECRET_KEY,
                                  is_secure=False,
                                  region=region,
                                  port=8773,
                                  path="/services/Cloud")
    #logger.debug("Connected")
    print("Connected")
    return connection


def create_VM_instance(settings, connection):
    connection.run_instances(image_id=settings.VM_IMAGE,
                             key_name=settings.PRIVATE_KEY_NAME, 
                             security_groups=settings.SECURITY_GROUP, 
                             instance_type=settings.VM_SIZE)
    while True:
        reservations = connection.get_all_instances()
        instance = reservations[0].instances[0]
        if instance:   
             state = instance.state
             print state, instance.ip_address
             if state == "running":
                 break
             else:
                 time.sleep(settings.CLOUD_SLEEP_INTERVAL)
        #check until successfull connection can be made
                 
def destroy_VM_instance(settings, connection, ip_address):
    instance = _get_this_instance(connection, ip_address)
    if not instance:
        print "VM instance %s Unknown " % ip_address
    else:
        instance_list=[]
        instance_list.append(instance.id)
        connection.terminate_instances(instance_list)
        _wait_for_instance_to_terminate(connection, ip_address)
        
        


def _get_this_instance(connection, ip_address):
    reservations = connection.get_all_instances()
    for reservation in reservations:
        instances = reservation.instances
        for instance in instances:
            if ip_address == instance.ip_address:
                print instance
                return instance
    return None

def _wait_for_instance_to_terminate(connection, instance_ip_address):
    instance = _get_this_instance(connection, instance_ip_address)
    while instance.state == running:
        print('Current status of Instance %s: %s'
                % (instance_ip_address, instance.state))
        
        time.sleep(settings.CLOUD_SLEEP_INTERVAL)
    

