import paramiko
from scp import SCPClient

'''
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname= nmrObj.server_ip , username='root', password='dave', look_for_keys=False)
scp = SCPClient(ssh.get_transport())

stdin, stdout, stderr = ssh.exec_command('cd ' + nmrObj.server_path + " && python3 nmr_noise.py")
stdout.channel.recv_exit_status()          # Blocking call

scp.get("/root/NMR_DATA/current_folder.txt",data_folder+"\\current_folder.txt")

meas_folder = parse_simple_info( data_folder, 'current_folder.txt' )
scp.get("/root/NMR_DATA/"+meas_folder[0],data_folder, recursive=True)

scp.close()

ssh.close()
'''


def exec_rmt_ssh_command ( nmrObj, ssh_cmd ):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    ssh.connect( hostname=nmrObj.server_ip , username=nmrObj.ssh_usr, password=nmrObj.ssh_passwd, look_for_keys=False )

    stdin, stdout, stderr = ssh.exec_command( "cd " + nmrObj.data_folder + " && " + ssh_cmd )
    stdout.channel.recv_exit_status()  # Blocking call

    ssh.close()


def cp_rmt_file( nmrObj, server_path, client_path, filename ):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    ssh.connect( hostname=nmrObj.server_ip , username=nmrObj.ssh_usr, password=nmrObj.ssh_passwd, look_for_keys=False )

    scp = SCPClient( ssh.get_transport() )
    scp.get( server_path + "/" + filename, client_path + "\\" + filename )

    scp.close()
    ssh.close()


def cp_rmt_folder( nmrObj, server_path, client_path, foldername ):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    ssh.connect( hostname=nmrObj.server_ip , username=nmrObj.ssh_usr, password=nmrObj.ssh_passwd, look_for_keys=False )

    scp = SCPClient( ssh.get_transport() )
    scp.get( server_path + "/" + foldername, client_path , recursive=True )

    scp.close()
    ssh.close()
