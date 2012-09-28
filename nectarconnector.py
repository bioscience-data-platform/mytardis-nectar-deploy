#import paramiko
import sys
import time
import traceback

from libcloud.compute.types import Provider
from libcloud.compute.types import NodeState
from libcloud.compute.providers import get_driver

NODE_STATE = ['RUNNING', 'REBOOTING', 'TERMINATED', 'PENDING', 'UNKNOWN']

def create_cloud_connection(settings):
    OpenstackDriver = get_driver(Provider.EUCALYPTUS)
    print("Connecting... %s" % OpenstackDriver)
    connection = OpenstackDriver(settings.EC2_ACCESS_KEY, secret=settings.EC2_SECRET_KEY,
                           host="nova.rc.nectar.org.au", secure=False,
                           port=8773, path="/services/Cloud")
    #logger.debug("Connected")
    print("Connected")
    return connection


def create_VM_instance(settings, connection):
    """
        Create the Nectar VM instance and return ip_address
    """
    images = connection.list_images()
    sizes = connection.list_sizes()

    image1 = [i for i in images if i.id == settings.VM_IMAGE][0]
    size1 = [i for i in sizes if i.id == settings.VM_SIZE][0]
    
    new_instance = None
    try:
        print("Creating VM instance")
        new_instance = connection.create_node(name="New Centos VM instance",
                                              size=size1, 
                                              image=image1, 
                                              ex_keyname=settings.PRIVATE_KEY_NAME,
                                              ex_securitygroup=settings.SECURITY_GROUP)
    except Exception, e:
        if "QuotaError" in e[0]:
            print " Quota Limit Reached: "
        else:
            traceback.print_exc(file=sys.stdout)
       
    if new_instance:
        ip_address = _wait_for_instance_to_start_running(settings, connection, new_instance)
        print 'Created VM instance with IP: %s' % ip_address
        return ip_address
              
def destroy_VM_instance(settings, connection, ip_address):
    """
        Terminate
            - all instances, or
            - a group of instances, or
            - a single instance
    """
    print("Terminating VM instance %s" % ip_address)
    if _is_instance_running(connection, ip_address):
        try:
            instance = _get_this_instance(connection, ip_address, ip_given=True)
            if not confirm_teardown(settings):
                return
            connection.destroy_node(instance)
            _wait_for_instance_to_terminate(settings, connection, ip_address)
        except Exception:
            traceback.print_exc(file=sys.stdout)
    else:
        print "VM instance with IP %s doesn't exist" % ip_address


def _get_this_instance(connection, instance_id_ip, ip_given=False):
    instances = connection.list_nodes()
    for instance in instances:
        if ip_given:
            if instance.public_ips[0] == instance_id_ip:
                return instance
        else:
            if instance.name == instance_id_ip:
                return instance
    return None


def _wait_for_instance_to_start_running(settings, connection, instance):
    instance_id = instance.name
    while True:
        instance = _get_this_instance(connection, instance_id)
        instance_state = instance.state
        instance_ip_list = instance.public_ips
        print('Current status of Instance %s: %s, IP: %s'
                % (instance_id, NODE_STATE[instance_state], instance_ip_list))
        if instance_state == NodeState.RUNNING and len(instance_ip_list)>0:
            return instance_ip_list[0]
        time.sleep(settings.CLOUD_SLEEP_INTERVAL)


def _wait_for_instance_to_terminate(settings, connection, ip_address):
    instance = _get_this_instance(connection, ip_address, ip_given=True)
    instance_id = instance.name
    
    while _is_instance_running(connection, ip_address):
        print('Current status of Instance %s: %s, IP: [%s]'
                % (instance_id, NODE_STATE[NodeState.RUNNING], ip_address))
        time.sleep(settings.CLOUD_SLEEP_INTERVAL)
    
    print('Current status of Instance %s: %s, IP: [%s]'
                % (instance_id, NODE_STATE[NodeState.TERMINATED], ip_address))


def confirm_teardown(settings):
    teardown_confirmation = None
    while not teardown_confirmation:
        teardown_confirmation = raw_input(
                                "Are you sure you want to delete (yes/no)? ")
        if teardown_confirmation != 'yes' and teardown_confirmation != 'no':
            teardown_confirmation = None
            
    if teardown_confirmation == 'yes':
        return True
    else:
        return False 

    
def _is_instance_running(connection, ip_address):
    """
        Checks whether an instance with @instance_id
        is running or not
    """
    instance_running = False
    all_instances = connection.list_nodes()
    for instance in all_instances:
        if instance.public_ips[0] == ip_address and instance.state == NodeState.RUNNING:
            return True
    return False
       

