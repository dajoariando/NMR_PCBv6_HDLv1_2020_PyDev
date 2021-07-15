import paramiko
from scp import SCPClient


# execute ssh_cmd in data directory given by nmrObj
def exec_rmt_ssh_cmd_in_datadir ( nmrObj, ssh_cmd ):
    exec_rmt_ssh_cmd ( nmrObj, "cd " + nmrObj.data_folder + " && " + ssh_cmd )


# execute ssh_cmd
def exec_rmt_ssh_cmd ( nmrObj, ssh_cmd ):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    ssh.connect( hostname=nmrObj.server_ip , username=nmrObj.ssh_usr, password=nmrObj.ssh_passwd, look_for_keys=False )

    stdin, stdout, stderr = ssh.exec_command( ssh_cmd )
    stdout.channel.recv_exit_status()  # Blocking call

    ssh.close()


# copy file from server to client
def cp_rmt_file( nmrObj, server_path, client_path, filename ):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    ssh.connect( hostname=nmrObj.server_ip , username=nmrObj.ssh_usr, password=nmrObj.ssh_passwd, look_for_keys=False )

    scp = SCPClient( ssh.get_transport() )
    scp.get( server_path + "/" + filename, client_path + "\\" + filename )

    scp.close()
    ssh.close()


# copy folder from server to client
def cp_rmt_folder( nmrObj, server_path, client_path, foldername ):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    ssh.connect( hostname=nmrObj.server_ip , username=nmrObj.ssh_usr, password=nmrObj.ssh_passwd, look_for_keys=False )

    scp = SCPClient( ssh.get_transport() )
    scp.get( server_path + "/" + foldername, client_path , recursive=True )

    scp.close()
    ssh.close()
