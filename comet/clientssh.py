import os
from paramiko import client
from stat import S_ISDIR

# Combined libraries from  Daan Lenaerts and user1041177 (stackoverflow)

class ssh:
    client = None
    sftp = None
 
    def __init__(self, clientInstance):
        self.client = clientInstance
        self.sftp = self.client.open_sftp()
 
    def cmd(self, command):
        if(self.client):
            print "Running command>> ", command
            stdin, stdout, stderr = self.client.run(command)
            if stdout is not '' or stdout is not None: 
                print stdout
            if stderr is not '' or stderr is not None:
                print( "Errors")
                print stderr

    def put(self,localfile,remotefile):
        #  Copy localfile to remotefile, overwriting or creating as needed.
        self.sftp.put(localfile,remotefile)

    def put_all(self,localpath,remotepath):
        remotepath = remotepath.replace('\\', '/')
        #  recursively upload a full directory
        os.chdir(os.path.split(localpath)[0])
        parent=os.path.split(localpath)[1]
        for walker in os.walk(parent):
            try:
                self.sftp.mkdir(os.path.join(remotepath,walker[0]).replace('\\', '/'))
            except:
                pass
            for file in walker[2]:
                print "Copying from:\n\t%s to \n\t%s" % (os.path.join(walker[0],file).replace('\\', '/'),os.path.join(remotepath,walker[0],file).replace('\\', '/'))
                self.put(os.path.join(walker[0],file).replace('\\', '/'),os.path.join(remotepath,walker[0],file).replace('\\', '/'))

    def get(self,remotefile,localfile):
        #  Copy remotefile to localfile, overwriting or creating as needed.
        self.sftp.get(remotefile,localfile)

    def sftp_walk(self,remotepath):
        # Kindof a stripped down  version of os.walk, implemented for 
        # sftp.  Tried running it flat without the yields, but it really
        # chokes on big directories.
        path=remotepath
        files=[]
        folders=[]
        for f in self.sftp.listdir_attr(remotepath.replace('\\', '/')):
            if S_ISDIR(f.st_mode):
                folders.append(f.filename)
            else:
                files.append(f.filename)
        print (path,folders,files)
        yield path,folders,files
        for folder in folders:
            new_path=os.path.join(remotepath.replace('\\', '/'),folder)
            for x in self.sftp_walk(new_path):
                yield x

    def get_all(self,remotepath,localpath):
        #  recursively download a full directory
        #  Harder than it sounded at first, since paramiko won't walk
        #
        # For the record, something like this would gennerally be faster:
        # ssh user@host 'tar -cz /source/folder' | tar -xz

        self.sftp.chdir(os.path.split(remotepath.replace('\\', '/'))[0])
        parent=os.path.split(remotepath.replace('\\', '/'))[1]
        try:
            os.mkdir(localpath)
        except:
            pass
        for walker in self.sftp_walk(parent):
            try:
                os.mkdir(os.path.join(localpath,walker[0]).replace('\\', '/'))
            except:
                pass
            for file in walker[2]:
                self.get(os.path.join(walker[0],file),os.path.join(localpath,walker[0],file).replace('\\', '/'))
                
    def write_command(self,text,remotefile):
        #  Writes text to remotefile, and makes remotefile executable.
        #  This is perhaps a bit niche, but I was thinking I needed it.
        #  For the record, I was incorrect.
        self.sftp.open(remotefile,'w').write(text)
        self.sftp.chmod(remotefile,755)
