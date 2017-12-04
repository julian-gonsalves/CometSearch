import os,sys,time
import boto, boto.ec2, boto.manage.cmdshell
from clientssh import ssh

# Ensure AWS Security Credentials is given
if len(sys.argv) != 2:
    print('Please provide the security file:\n\tdeploy.py [security_file_name]')
    quit()
securitykey = sys.argv[1]
keyfile = securitykey + '.pem'
instance_id = 'i-05bc8c3b1ab445c3c'

#boto.set_stream_logger('boto')
conn = boto.ec2.connect_to_region('us-east-1',
    aws_access_key_id='AKIAJ4LHSCYIAJBJXW4Q',
    aws_secret_access_key='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'
    )

reservations = conn.get_all_instances(instance_ids=[instance_id,])
instance = reservations[0].instances[0]

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
