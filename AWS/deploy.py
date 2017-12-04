import os,sys,time
import boto, boto.ec2, boto.manage.cmdshell
from clientssh import ssh

# Ensure AWS Security Credentials is given
if len(sys.argv) != 2:
    print('Please provide the security file:\n\tdeploy.py [security_file_name]')
    quit()
securitykey = sys.argv[1]
keyfile = securitykey + '.pem'

#boto.set_stream_logger('boto')
conn = boto.ec2.connect_to_region('us-east-1',
    aws_access_key_id='AKIAJ4LHSCYIAJBJXW4Q',
    aws_secret_access_key='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'
    )

# Create security group
try:
    sec_group = conn.create_security_group(name='cometDev',description='Authorized to develop')
except:
    sec_group = conn.get_all_security_groups(groupnames=['cometDev'])
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
try:
    print "Creating Instance. This may take awhile..."
    reservation = conn.run_instances(
                        image_id='ami-55ef662f', 
                        instance_type='t2.micro', 
                        key_name=securitykey, 
                        security_groups=['cometDev']
                    )
except Exception, e:
    print 'Instance could not be created'
    print str(e)
    quit()


# get instance states
instance = reservation.instances[0]
print 'Instance {0} - {1}(id) is {2} at {3} ({4})'.format(
        instance.instance_type,
        instance.id,
        instance.state,
        instance.ip_address,
        instance.public_dns_name
)

# Ensuring the Instance running
print("Waiting for the instance to be stable...(this may take a while)")
while instance.state != 'running':
    time.sleep(30)
    instance.update()

if instance.state == 'running':
    # Allocate Elastic IP
    elastic_address = conn.get_all_addresses()
    if(not elastic_address):
        pass
    else:
        elastic_address = elastic_address[0]
        elastic_address.associate(instance_id = instance.id)
        instance.update()
        print 'New Address is  {0}  ({1})'.format(instance.ip_address,instance.public_dns_name)

#Ensure instance has passed status checks before proceeding
print "Ensuring instance is reachable... may take a couple of minutes"
def instance_not_reachable():
    status = conn.get_all_instance_status(instance_ids=[instance.id,])[0]
    return status.system_status.details['reachability'] != 'passed' and  status.instance_status.details['reachability'] != 'passed'

while instance_not_reachable():
    time.sleep(30)

#Get an SSHClinet
ssh_client = boto.manage.cmdshell.sshclient_from_instance(
                instance,
                keyfile,
                user_name='ec2-user'
            )
if not ssh_client:
    print "Could not connect to instance"
    quit()

ssh_client_ = ssh(ssh_client)

print "SSH Connection established"
print "Installing packages...(this may take awhile)"

#TODO
# 1. Copy       requirements.txt                        to remote
ssh_client_.put('requirements.txt', 'requirements.txt')
# 2. Install    redis          to remote
ssh_client_.cmd('sudo yum -y --enablerepo=epel install redis')
# 3. run        sudo yum install mysql-devel gcc gcc-devel python-devel
ssh_client_.cmd('sudo yum -y install mysql-devel gcc gcc-devel python-devel')
# 4. run        sudo pip install -r requirements
ssh_client_.cmd('sudo pip install -r requirements.txt')
# 6. copy       files_to_copy   content to      comet
# --- Single Files -----
print "copying files..."
ssh_client_.put_all('../comet','./')

# 7. run        nohup sudo python server.py > server.log &
cmd_str = "nohup sh -c 'cd comet && sudo python server.py' > nohup.out 2> nohup.err < /dev/null &"
ssh_client_.cmd(cmd_str)


print "Instance {0} is set up and running at {1} ({2})".format(instance.id, instance.ip_address, instance.public_dns_name)