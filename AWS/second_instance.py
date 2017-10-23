import os
import boto
import boto.ec2


#boto.set_stream_logger('boto')
conn = boto.ec2.connect_to_region('us-east-1',
    aws_access_key_id='AKIAJ4LHSCYIAJBJXW4Q',
    aws_secret_access_key='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'
    )

# Make key pair
if (not conn.get_key_pair('cometSearchKey')):
    newKey = conn.create_key_pair('cometSearchKey')
    # save new key
    if(not newKey.save('')):
        exit()

# Create security group
sec_group = conn.get_all_security_groups(groupnames=['csc326-group24'])
if(not sec_group):
    sec_group = conn.create_security_group(name='csc326-group24',description='For submission and running tests')
else:
    sec_group = sec_group[0]

# Authorize port access
try:
    sec_group.authorize(ip_protocol='icmp', from_port=-1, to_port=-1, cidr_ip='0.0.0.0/0')
except:
    print "{0} at port {1} already exists".format("icmp",-1)

try:
    sec_group.authorize(ip_protocol='tcp', from_port=22, to_port=22, cidr_ip='0.0.0.0/0')
except:
    print "{0} at port {1} already exists".format("tcp",22)

try:
    sec_group.authorize(ip_protocol='tcp', from_port=80, to_port=80, cidr_ip='0.0.0.0/0')
except:
    print "{0} at port {1} already exists".format("tcp",80)


# create instances
reservations = conn.get_all_instances()
if (not reservations):
    reservations = conn.run_instances(image_id='ami-6cd01a16', instance_type='t2.micro', key_name='cometSearchKey', security_groups=['csc326-group24'])
else:
    reservations = reservations[0]

# get instance states
for instance in reservations.instances:
    print 'Instance {0} - {1} is {2} at {3} (initial)'.format(instance.instance_type,instance.image_id,instance.state,instance.ip_address)

    """
    if instance.state == 'running':
        # Allocate Elastic IP
        elastic_address = conn.get_all_addresses()
        if(not elastic_address):
            elastic_address = conn.allocate_address()
            # Associate Elastic IP to instance
            try:
                elastic_address.associate(instance_id = instance.id)
            except:
                print 'EIP already associated'
        else:
            elastic_address = elastic_address[0]

        print 'Instance {0} - {1} is {2} at {3} (final)'.format(instance.instance_type,instance.image_id,instance.state,instance.ip_address)
    """
