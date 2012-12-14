import sys
import time
import traceback
import boto

from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError

from chefclient import delete_chef_node_client
from chefclient import customize_prompt

def create_cloud_connection(settings):
    region = RegionInfo(name="NeCTAR", endpoint="nova.rc.nectar.org.au")
    connection = boto.connect_ec2(
        aws_access_key_id=settings.EC2_ACCESS_KEY,
        aws_secret_access_key=settings.EC2_SECRET_KEY,
        is_secure=True,
        region=region,
        port=8773,
        path="/services/Cloud")

    #print("Connecting to... %s" % region.name)
    return connection


def create_VM_instance(settings):
    """
           Create a Nectar VM instance
    """
    connection = create_cloud_connection(settings)
    try:
        print "Creating VM instance"
        reservation = connection.run_instances(
            image_id=settings.VM_IMAGE,
            min_count=1,
            max_count=1,
            key_name=settings.PRIVATE_KEY_NAME,
            security_groups=settings.SECURITY_GROUP,
            instance_type=settings.VM_SIZE)
        #print ("Created Reservation %s" % reservation)
        new_instance = reservation.instances[0]
        print ("Created Instance: %s" % new_instance)
        _wait_for_instance_to_start_running(settings, new_instance)
        ip_address = get_instance_ip(new_instance,
            refresh=True, settings=settings)
        customize_prompt(settings, ip_address)
        print 'Created VM instance with IP: %s' % ip_address

    except EC2ResponseError, e:
        if "Quota" in e.body:
            print 'Quota Limit Reached'
        else:
            raise


def destroy_VM_instance(settings, ip_address):
    """
        Terminate a VM instance
    """
    print("Terminating VM instance %s" % ip_address)
    if _is_instance_running(settings, ip_address, ip_given=True):
        try:
            if not confirm_teardown():
                return
            instance = get_this_instance(settings, ip_address,
                ip_given=True)
            instance_id = instance.id
            ip_address = get_instance_ip(instance)
            delete_chef_node_client(settings, instance_id, ip_address)
            connection = create_cloud_connection(settings)
            connection.terminate_instances([instance_id])
            _wait_for_instance_to_terminate(settings, ip_address)
        except Exception:
            traceback.print_exc(file=sys.stdout)
            raise
    else:
        print "VM instance with IP %s doesn't exist" % ip_address


def get_all_instances(settings):
    connection = create_cloud_connection(settings)
    reservations = connection.get_all_instances()
    #print("Reservation %s" % reservations)
    all_instances = []
    for reservation in reservations:
        nodes = reservation.instances
        #print("Nodes %s" % nodes)
        for i in nodes:
            all_instances.append(i)
    return all_instances


def get_this_instance(settings, instance_id_ip, ip_given=False):
    """
       Get a reference to node with instance_id
   """
    instances = get_all_instances(settings)
    for instance in instances:
        if ip_given:
            current_ip = get_instance_ip(instance)
            if current_ip == instance_id_ip:
                return instance
        else:
            if instance.id == instance_id_ip:
                return instance


def get_instance_ip(instance, refresh=False, settings={}):
    """
        Get the ip address of an instance
    """
    #TODO: throw exception if can't find instance_id
    ip_address = ''
    if refresh and settings:
        all_instances = get_all_instances(settings)
        for i in all_instances:
            if i.id == instance.id:
                ip_address = i.ip_address
                break
    else:
        ip_address = instance.ip_address

    return ip_address


def _is_instance_running(settings, instance_id_ip,
                         ip_given=False):
    """
        Checks whether an instance with @instance_id
        is running or not
    """
    instance = get_this_instance(settings,
        instance_id_ip, ip_given)
    if instance:
        if ip_given:
            ip_address = instance_id_ip
        else:
            ip_address = get_instance_ip(instance)
        state = instance.state
        print  'Current status of Instance'\
               ' with IP [%s]: %s' %(ip_address, state)
        if state == "running" and ip_address:
            return True
    return False


def _wait_for_instance_to_start_running(settings, instance):
    #FIXME: add final timeout for when VMs fail to initialise properly
    while True:
        if _is_instance_running(settings, instance.id):
            return
        time.sleep(settings.CLOUD_SLEEP_INTERVAL)


def _wait_for_instance_to_terminate(settings, ip_address):
    #FIXME: add final timeout for when VMs fail to terminate properly
    while True:
        if not _is_instance_running(settings, ip_address, ip_given=True):
            print  'Current status of Instance'\
                   ' with IP [%s]: terminated' %ip_address
            return
        time.sleep(settings.CLOUD_SLEEP_INTERVAL)


def confirm_teardown():
    teardown_confirmation = None
    while not teardown_confirmation:
        question = "Are you sure you want to delete (yes/no)? "
        teardown_confirmation = raw_input(question)
        if teardown_confirmation != 'yes' and teardown_confirmation != 'no':
            teardown_confirmation = None
    if teardown_confirmation == 'yes':
        return True
    else:
        return False

