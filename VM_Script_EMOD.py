__author__ = 'Natalie Sanders'

from azure.servicemanagement import *
from azure.storage import *
from subprocess import call
from os import chdir
import os
import socket
import zipfile


def upload_results():

    ####### Upload Final Results ########

    # Zip output directory
    z = zipfile.ZipFile('Output.zip', "w", zipfile.ZIP_DEFLATED)
    for result in os.listdir('Output'):
        chdir("c:/Users/Public/Sim/Output")
        z.write(result)
    z.close()

    result = 'r-' + vm_name
    blob_service.put_block_blob_from_path(container_name, result, 'c:/Users/Public/Sim/Output.zip')


def download_input():
    blob_service.get_blob_to_path(container_name, vm_name, 'c:/Users/Public/Sim/Input.zip')
    chdir("C:/Users/Public/Sim")
    z = zipfile.ZipFile('Input.zip', 'r')
    z.extractall()
    z.close()


def delete_vm():
    hosted_service = sms.get_hosted_service_properties(service_name=username, embed_detail=True)

    if hosted_service.deployments:
        deployment = sms.get_deployment_by_name(username, username)
        roles = deployment.role_list

        for instance in roles:
            if vm_name == instance.role_name:
                if len(roles) == 1:
                    sms.delete_deployment(service_name=username, deployment_name=username)
                else:
                    sms.delete_role(service_name=username, deployment_name=username, role_name=vm_name)
                    break


########################################################################################################################
##                                                        MAIN                                                        ##
########################################################################################################################

##### Service Management Object #####
vm_name = socket.gethostname()
split = vm_name.split('-')
username = '-'.join(split[:-1])
container_name = '-'.join(split[:-1]).lower()

subscription_id = 'a9401417-cb08-4e67-bc2a-613f49b46f8a'
certificate_path = 'CURRENT_USER\\my\\AzureCertificate'

# Import service management certificate
call(['certutil', '-user', '-f', '-p', '1', '-importPFX', 'c:/temp/azure.pfx'])

sms = ServiceManagementService(subscription_id, certificate_path)

###### Redirect stdout to File ######
chdir('C:/Users/Public/Sim')
output = open("Output/stdout.txt", "wb")

####### Download Input Files ########
blob_service = BlobService(
    account_name='portalvhdsd3d1018q65tg3',
    account_key='cAT5jbypcHrN7sbW/CHgGFDGSvOpyhw6VE/yHubS799egkHfvPeeXuK7uzc6H2C8ZU1ALiyOFEZkjzWuSyfc+A==')

try:
    download_input()
except:
    output.write('Could not download input from the cloud.\n')
    output.close()
    upload_results()
    delete_vm()

########### Run Simulation ##########
call(["eradication.exe", "-C",  "config.json", "-O", "Output"], stdout=output)
output.close()

########### Upload Results ##########
try:
    upload_results()

############# Delete VM #############
finally:
    delete_vm()