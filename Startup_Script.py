__author__ = 'Natalie Sanders'

from azure.servicemanagement import *
from azure.storage import *
from subprocess import call
from os import chdir
import os
import socket
import zipfile

##### Service Management Object #####
machine_name = socket.gethostname()
split = machine_name.split('-')
container_name = '-'.join(split[:-1]).lower()
username = '-'.join(split[:-1])

call(['certutil', '-user', '-f', '-p', '1', '-importPFX', 'c:/temp/azure.pfx'])

subscription_id = 'a9401417-cb08-4e67-bc2a-613f49b46f8a'
certificate_path = 'CURRENT_USER\\my\\AzureCertificate'

sms = ServiceManagementService(subscription_id, certificate_path)

####### Download Input Files ########
blob_service = BlobService(
    account_name='portalvhdsd3d1018q65tg3',
    account_key='cAT5jbypcHrN7sbW/CHgGFDGSvOpyhw6VE/yHubS799egkHfvPeeXuK7uzc6H2C8ZU1ALiyOFEZkjzWuSyfc+A==')

blob_service.get_blob_to_path(container_name, machine_name, 'c:/Users/Public/Sim/Input.zip')

chdir("C:/Users/Public/Sim")
z = zipfile.ZipFile('Input.zip', 'r')
z.extractall()
z.close()

########### Run Simulation ##########

# Change working directory path

# Redirect simulation output to file stdout.txt
output = open("Output/stdout.txt", "wb")
# Run simulation
call(["eradication.exe", "-C",  "config.json", "-O", "Output"], stdout=output)
output.close()

####### Upload Final Results ########

# Zip output directory
z = zipfile.ZipFile('Output.zip', "w", zipfile.ZIP_DEFLATED)
for result in os.listdir('Output'):
    chdir("c:/Users/Public/Sim/Output")
    z.write(result)
z.close()

result = 'r-' + machine_name
blob_service.put_block_blob_from_path(container_name, result, 'c:/Users/Public/Sim/Output.zip')

hosted_service = sms.get_hosted_service_properties(service_name=username, embed_detail=True)
if hosted_service.deployments:
    deployment = sms.get_deployment_by_name(username, username)
    roles = deployment.role_list

    for instance in roles:
        if machine_name == instance.role_name:
            if len(roles) == 1:
                sms.delete_deployment(service_name=username, deployment_name=username)
            else:
                sms.delete_role(service_name=username, deployment_name=username, role_name=machine_name)
            break
