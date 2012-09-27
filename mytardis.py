from optparse import OptionParser
import getopt

import os 
import sys
import time

import logging
import boto

from nectarconnector import *

def start():

    #http://docs.python.org/howto/logging.html#logging-basic-tutorial
    '''
    logging.config.fileConfig('logging.conf')
    '''
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config_file = os.path.expanduser("~/.cloudenabling/config.sys")
    if os.path.exists(config_file):
        config.read(config_file)
    else:
        config_file = os.path.expanduser("settings")  # a default config file
        if os.path.exists(config_file):
            config.read(config_file)
        else:
            print("no configuration file found")
            sys.exit(1)

    environ_fields = ['USER_NAME', 'PASSWORD', 'PRIVATE_KEY',
                      'VM_SIZE', 'VM_IMAGE',
                      'SLEEP_TIME', 'RETRY_ATTEMPTS',
                      'EC2_ACCESS_KEY', 'EC2_SECRET_KEY',
                      'CLOUD_SLEEP_INTERVAL', 'PRIVATE_KEY_NAME',
                      'SECURITY_GROUP']

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
        #print("%s" % field_val)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ct:d:",\
                                   ["create=", "test", "destroy"])
    except getopt.GetoptError:
   #print help info and exit:
        print("Couldn't parse arguments")
        
        exit(1)

    step = ""
    ip_address = ""
    for opt, val in opts:
        if opt in ("-c", "--create"):
            step = "create"
        if opt in ("-t", "--test"):
            step = "test"
            ip_address = val
        if opt in ("-d", "--destroy"):
            step = "destroy"
            ip_address = val
            
    if step == "create":
        connection = create_cloud_connection(settings)
        create_VM_instance(settings, connection)
        
        print step
    elif step == "test":
        print step, ip_address
    elif step == "destroy":
        connection = create_cloud_connection(settings)
        destroy_VM_instance(settings, connection, ip_address)
        print step, ip_address
    
    else:
        print "Not create"
        
    '''
        connection.run_instances(image_id="ami-0000000d",
                                 min_count=number_vm,
                                 max_count=number_vm,
                                 key_name="nana-sync", 
                                 security_groups=["ssh","http","icmp"], 
                                 instance_type='m1.small')
        while 1:
            reservations = connection.get_all_instances()
            instances = reservations[0].instances
            instance = instances[0]
            if instance:   
                 state = instance.state
                 print state, instance.ip_address
                 if state == "running":
                     break
                 else:
                     time.sleep(1)
        time.sleep(10)
    '''
    
        
        
    """      
    # get command line options
    parser = OptionParser()
    parser.add_option("-n", "--nodeid", dest="instance_id",
                      help="The instance id from the cloud infrastructure")
    parser.add_option("-i", "--inputdir", dest="input_dir",
                      help="The local directory holding \
                      input files for the task")
    parser.add_option("-o", "--outputdir", dest="output_dir",
                      help="The local directory which will \
                      hold output files for the task")
    parser.add_option("-g", "--group", dest="group_id",
                      help="The group id from the cloud infrastructure")
    parser.add_option("-v", "--number-vm-instances", type="int",
                      dest="number_vm_instances",
                      help="The number of VM instances to " +
                      "be created as a group")
    parser.add_option("-s", "--seed", dest="seed",
                      help="The master seed that generates all other seeds")

    (options, args) = parser.parse_args()

    if 'create' in args:
        if options.number_vm_instances:
            res = create_environ(options.number_vm_instances, settings)
            logger.debug(res)
        else:
            logging.error("enter number of VM instances to be created")
            parser.print_help()
            sys.exit(1)

    elif 'setup' in args:
        if options.group_id:
            group_id = options.group_id
            setup_multi_task(group_id, settings)
        else:
            logging.error("enter nodeid of the package")
            parser.print_help()
            sys.exit(1)

    elif 'run' in args:
        if options.group_id:

            group_id = options.group_id

            if not options.output_dir:
                logging.error("specify output directory")
                parser.print_help()
                sys.exit(1)
            elif os.path.isdir(options.output_dir):
                logging.error("output directory already exists")
                sys.exit(1)
            else:
                try:
                    os.mkdir(options.output_dir)
                except OSError:
                    logger.error("output directory %s already exists" % options.output_dir)
                    sys.exit(1)

            prepare_multi_input(group_id, options.input_dir,
                                settings, options.seed)

            try:
                pids = run_multi_task(group_id, options.input_dir, settings)
            except PackageFailedError, e:
                logger.error(e)
                logger.error("unable to start packages")
                #TODO: cleanup node of copied input files etc.
                sys.exit(1)

            while (not packages_complete(group_id,
                                         options.output_dir,
                                         settings)):
                print("job is running.  Wait or CTRL-C to exit here. \
                 run 'check' command to poll again")
                time.sleep(settings.SLEEP_TIME)

        else:
            logging.error("enter group id of the run")
            parser.print_help()
            sys.exit(1)

    elif 'check' in args:
        if options.group_id:
            if not options.output_dir:
                logging.error("specify output directory")
                parser.print_help()
                sys.exit(1)

            group_id = options.group_id
            is_finished = packages_complete(group_id,
                                            options.output_dir,
                                            settings)

            if is_finished:
                print "done. output is available at %s" % options.output_dir
            else:
                print "job still running"
        else:
            logger.error("enter group id of the run")
            parser.print_help()
            sys.exit(1)

    elif 'teardown' in args or 'teardown_all' in args:
        # TODO: make sure that the instance we are tearing down is the one
        # that is running the package and no some random VM, probably by
        # logging in and checking state.
        if options.group_id:
            all_instances = collect_instances(settings, group_id=options.group_id)
            if confirm_teardown(settings, all_instances):
                destroy_environ(settings, all_instances)
        elif options.instance_id:
            all_instances = collect_instances(settings, instance_id=options.instance_id)
            if confirm_teardown(settings, all_instances):
                destroy_environ(settings, all_instances)
        elif 'teardown_all' in args:
            all_instances = collect_instances(settings, all_VM=True)
            if confirm_teardown(settings, all_instances):
                destroy_environ(settings, all_instances)
        else:
            logger.error("Enter either group id or instance id of the package")
            parser.print_help()
            sys.exit(1)

#    elif 'print' in args:
#        print_running_node_id(settings)

    elif 'info' in args:
        print "Summary of Computing Environment"
        all_instances = collect_instances(settings, all_VM=True)
        print_all_information(settings, all_instances)

    else:
        parser.print_help()

   """
if __name__ == '__main__':
    begins = time.time()
    start()
    ends = time.time()
    print("Total execution time: %d seconds" % (ends-begins))
