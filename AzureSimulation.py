__author__ = 'Natalie'

import hashlib
import os
import AzureTools
import pickle
from AzureTools              import comp_user
from azure                   import *
from azure.servicemanagement import *
from azure.storage           import BlobService
from re                      import search
from time                    import time, sleep
from sys                     import stderr


# Create service management object
subscription_id = 'a9401417-cb08-4e67-bc2a-613f49b46f8a'
certificate_path = 'CURRENT_USER\\my\\AzureCertificate'
sms = ServiceManagementService(subscription_id, certificate_path)

# Create blob service object
blob_service = BlobService(
    account_name='portalvhdsd3d1018q65tg3',
    account_key='cAT5jbypcHrN7sbW/CHgGFDGSvOpyhw6VE/yHubS799egkHfvPeeXuK7uzc6H2C8ZU1ALiyOFEZkjzWuSyfc+A==')

class AzureSimulation:
    def __init__(self):
        self.name   = ""
        self.vm_id  = ""
        self.input  = ""
        self.cores  = 1
        self.tstamp = ""

    def upload_input(self, user_info):
        """
        Calls to zip the provided input files then uploads them to the user's storage container.
        :param user_info:
        :return:
        """

        # Convert to Windows format
        norm_inputs = (os.path.normpath(self.input))

        # Create pickle file for user_info
        f = 'C:/Users/' + comp_user + '/Simulations/' + user_info["username"] + '/AzureUserInfo.pickle'
        pickle.dump(user_info,file(f, 'w'))

        # Zip input files
        inputs_zip = AzureTools.zip_files(user_info["username"], norm_inputs)

        # Try uploading the specified input
        #try:
        print user_info["username"]
        blob_service.put_block_blob_from_path(user_info["username"].lower(), self.vm_id, inputs_zip)
        '''
        except:
            stderr.write('An error occurred uploading your input.')
            exit(1)
        '''
    def generate_vm_id(self, username):
        """
        Generates a name for the VM that will run the simulation. The name is created by add random hex to the client's
        username to create a 15 character string
        :param username:
        :return:
        """

        hash_obj = hashlib.sha1()
        hash_obj.update(str(time()))

        length = 14 - len(username)           # specifies length of rand such that VM name will be 15 characters long
        rand = hash_obj.hexdigest()[:length]  # creates n random digits of hex
        self.vm_id = username + '-' + rand       # appends random hex number to the username to create a unique VM name

    def check_name(self, name):
        """
        Checks that the project name is valid
        :return:
        """

        #print self.name
        valid = True

        # Check that the project name is valid
        val = search('[ <>:"/\\\|?*]', name)
        print val
        if val:
            valid = False

        return valid

    def simulation(self, username, sim_type="EMOD", ARG=False, DEL=True):
        """
        Uploads a client's input files for a new simulation to the client's storage container and then creates a VM
        under the client's cloud service on which the simulation will be run.
        :param username:
        :param sim_type:
        :param ARG:
        :param DEL:
        :return:
        """

        ######### Create OS Hard Disk #########
        if DEL:
            if sim_type == "EMOD":
                image_name = 'EMOD-w-email-os-2014-11-25' #'EMOD-OS-os-2014-07-09'
            elif sim_type == "OM":
                image_name = 'Mock-w-email-os-2014-11-25' #'mock-model2-os-2014-07-10'
            elif sim_type == "mock":
                image_name = 'Mock-w-email-os-2014-11-25' #'mock-model2-os-2014-07-10'
            else:
                stderr.write('Error')
                exit(1)
        else:
            if sim_type == "EMOD":
                image_name = 'no-del-EMOD-w-email-os-2014-11-25' #'no-delete-EMOD2-os-2014-09-19'
            elif sim_type == "OM":
                image_name = 'no-del-Mock-w-email-os-2014-11-25' #'no-delete-Mock-os-2014-09-17'
            elif sim_type == "mock":
                image_name = 'no-del-Mock-w-email-os-2014-11-25' #'no-delete-Mock-os-2014-09-17'
            else:
                stderr.write('Error')
                exit(1)

        storage_account = 'portalvhdsd3d1018q65tg3'
        blob = self.vm_id + '-blob.vhd'
        media_link = "https://" + storage_account + ".blob.core.windows.net/vhds/" + blob

        os_hd = OSVirtualHardDisk(image_name, media_link)

        ###### Windows VM configuration #####
        windows_config = WindowsConfigurationSet(
            computer_name=self.vm_id,
            admin_password="Bbsitdon-1994",
            admin_username="Natalie")

        windows_config.domain_join = None
        windows_config.win_rm = None

        ### Endpoints for Remote Connection ###
        endpoint_config = ConfigurationSet()
        endpoint_config.configuration_set_type = 'NetworkConfiguration'

        endpoint1 = ConfigurationSetInputEndpoint(
            name='rdp',
            protocol='tcp',
            port='33890',
            local_port='3389',
            load_balanced_endpoint_set_name=None,
            enable_direct_server_return=False)

        endpoint_config.input_endpoints.input_endpoints.append(endpoint1)

        ############# Create VM #############
        if self.cores == 1:
            core_size = 'Small'
        elif self.cores == 2:
            core_size = 'Medium'
        elif self.cores == 4:
            core_size = 'Large'
        elif self.cores == 8:
            core_size = 'Extra Large'
        elif self.cores == 16:
            core_size = 'A9'
        else:
            stderr.write('Core size not available. Options: 1, 2, 4, 8, 16\n')
            exit(1)

        # Check that there are cores available
        timed_out = True
        message_given = False
        start_time = time()
        while (time() - start_time) < 180:
            subscription = sms.get_subscription()
            cores_available = subscription.max_core_count - (subscription.current_core_count + self.cores)
            if cores_available < 0:
                if not message_given:
                    print 'No cores are available for usage at this time. Please, wait until a ' + str(self.cores) + '-core VM can be generated...\n'
                    message_given = True
            else:
                print "\nCreating VM..."
                timed_out = False
                break

        if timed_out:
            stderr.write("Request timed out: Windows Azure is a bit backlogged at the moment. Try again later.")
            sleep(0.5)
            if ARG:
                exit(1)
            else:
                return 1

        # Wait until a role can be added to the deployment
        first = True
        timed_out = True
        start_time = time()
        deployment_result = 0
        while (time() - start_time) < 180: # will try to create role for 3 minutes before timing out
            service = sms.get_hosted_service_properties(username, True)
            # If there's a VM running on the client's service, add a VM to the pre-existing deployment
            if service.deployments:
                #try:
                deployment_result = sms.add_role(
                    service_name=username,
                    deployment_name=username,
                    role_name=self.vm_id,
                    system_config=windows_config,
                    os_virtual_hard_disk=os_hd,
                    role_size=core_size)
                timed_out = False
                    #break
                '''
                except WindowsAzureConflictError:
                    if first:
                        print '\nWindows Azure is currently performing an operation on this deployment that requires ' \
                              'exclusive access. \nPlease, wait...'
                        first = False

                except:
                    stderr.write("There was an error creating a virtual machine to run your simulation.")
                    sleep(0.5)
                    if ARG:
                        exit(1)
                    else:
                        return 1
                '''

            # If no VMs are deployed, a VM is deployed on the client's service
            elif not service.deployments:
                #try:
                deployment_result = sms.create_virtual_machine_deployment(
                    service_name=username,
                    deployment_name=username,
                    deployment_slot='production',
                    label=self.vm_id,
                    role_name=self.vm_id,
                    network_config=endpoint_config,
                    system_config=windows_config,
                    os_virtual_hard_disk=os_hd,
                    role_size=core_size)
                timed_out = False
                #break
                '''
                except:
                    stderr.write("There was an error creating a virtual machine to run your simulation.")
                    sleep(0.5)
                    if ARG:
                        exit(1)
                    else:
                        return 1
                '''
        if timed_out:
            stderr.write("Request timed out: Windows Azure is a bit backlogged at the moment. Try again later.")
            sleep(0.5)
            if ARG:
                exit(1)
            else:
                return 1

        # Check that the VM was created properly
        status = sms.get_operation_status(deployment_result.request_id)
        try:
            stderr.write(vars(status.error))
            exit(1)
        except:
            print "\nSimulation Running! Check back later to retrieve results."
            return 0
