import os, sys, time
import boto
import boto.ec2

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

# Ask for instance id
instance_id = raw_input("Instance to kill: ")
reservations = conn.get_all_instances(instance_ids=[instance_id,])
instance = reservations[0].instances[0]

try:
    instance.terminate()
    print "Termination of Instance {0} initiated.".format(instance_id,)
except Exception, e:
    print "Instance termination failed"
    print str(e)

print "Awaiting confirmation...(may take awhile)"
while instance.state != 'terminated':    
    time.sleep(30)
    instance.update()

print "Instance {0} has been successfully terminated".format(instance_id,)

