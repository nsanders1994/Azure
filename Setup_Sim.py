#!/usr/bin/python

__author__ = 'Natalie Sanders'

from azure import *
from azure.servicemanagement import *
from azure.storage import BlobService
from getpass import getuser
from re import search
from time import localtime, time, sleep
from sys import stderr
import hashlib
import os
import zipfile
import argparse


def menu():

        """
        Beginning menu which prompts the user to sign in with a previous username, create
        an account, or quit the program.
        :return:
        """

        user_input = raw_input(
            "\n########## LOGIN ##########\n"
            "(1) Sign in\n"
            "(2) New User\n"
            "(3) Quit\n"
            ">> ")

        if user_input == '1':
            # prompts client for username
            sign_in()
        elif user_input == '2':
            # creates cloud service and storage container using client specified username
            new_user()
        elif user_input == '3':
            quit(0)
        else:
            print "\nCommand not recognized."
            menu()


def sub_menu():

        """
        The menu displayed after a client has signed-in or has created an account. Gives the
        client the option to run a new simulation, retrieve simulation results for a previously
        run simulation, or logout.
        :return:
        """

        user_input = raw_input(
            '\n########### MENU ########### \n'
            '(1) Start new EMOD simulation\n'
            '(2) Start new Open Malaria simulaion\n'
            '(3) Check for simulation results\n'
            '(4) Delete account\n'
            '(5) Logout\n'
            '(6) Quit\n'
            '>> ')

        if user_input == '1':
            # creates a VM under client's cloud service, running the EMOD simulation
            vm_name, proj_name = setup_proj()
            simulation(vm_name, 'EMOD')
            update_proj_file(vm_name, proj_name)
            sub_menu()
        elif user_input == '2':
            # creates a VM under client's cloud service, running the Open Malaria simulation
            vm_name, proj_name = setup_proj()
            simulation(vm_name, 'OM')
            update_proj_file(vm_name, proj_name)
            sub_menu()
        elif user_input == '3':
            # returns the results of a previously run simulation specified by the client
            get_results()
        elif user_input == '4':
            # deletes the user's account-- cloud service and storage container
            delete_account(username)
            menu()
        elif user_input == '5':
            menu()
        elif user_input == '6':
            quit(0)
        else:
            stderr.write("\nCommand not recognized.")
            sleep(0.5)
            sub_menu()


def ARG_sign_in(user):

        """
        Returning clients are signed-in with the provided username to gain access to previous simulations and to run new
        simulations.
        :param user:
        :return:
        """

        global username
        username = user

        exists = check_user_exists(username)

        if not exists:
            stderr.write("Username does not exist. Use the '-new' flag to create a new account.")
            exit(1)


def sign_in():

        """
        Returning clients can sign-in with a username to gain access to previous simulations
        and to run new simulations.
        :return:
        """

        global username
        username = raw_input('\nEnter username: ')

        # Check username exists
        exists = check_user_exists(username)

        # Username does not exist
        if not exists:
            stderr.write('\nUsername does not exist.\n')
            sleep(0.5)
            while 1:
                user_input = raw_input(
                    '(1) Re-enter username\n'
                    '(2) Back to login\n'
                    '(3) Quit\n'
                    '>> ')
                if user_input == '1':
                    sign_in()
                elif user_input == '2':
                    menu()
                elif user_input == '3':
                    quit(0)
                else:
                    stderr.write('\nInput not recognized.\n')
                    sleep(0.5)
        else:
            sub_menu()


def check_user_exists(user):

        """
        Checks that the username used to login exists, that is that there is a cloud service for this username.
        :return:
        """

        services = sms.list_hosted_services()  # Lists all cloud services

        # Checks that given username exists as a cloud service
        exists = False
        for hosted_service in services:
            if hosted_service.service_name == user:
                exists = True
                break

        return exists


def ARG_new_user(user):

        """
        The provided username is used to to create a new 'account' where simulations
        can be stored and accessed. The client's username is used to create a cloud service
        which will run all their simulations on VMs and to create a storage account where
        input and results files and loaded/downloaded.
        :param user:
        :return:
        """

        # Check that there is room for more cloud services.
        subscription = sms.get_subscription()
        services_available = subscription.max_hosted_services - subscription.current_hosted_services
        if not services_available:
            stderr.write('This Azure subscription has reached capacity. To delete an old account, use the -d flag.')
            exit(1)

        # Assign the username
        global username
        username = user

        # Check that username has correct syntax and is available
        valid = check_username()

        # If valid a cloud service is created.
        if valid:
            setup_account()

        # If not valid, the program exits
        else:
            exit(1)


def new_user():

        """
        New clients create a username in order to create an 'account' where simulations
        can be stored and accessed. Their username is used to create a cloud service
        which will run all their simulations on VMs and to create a storage account where
        input and results files and loaded/downloaded.
        :return:
        """

        # Check that there is room for more cloud services.
        subscription = sms.get_subscription()
        services_available = subscription.max_hosted_services - subscription.current_hosted_services
        if not services_available:
            stderr.write('This Azure subscription has reached capacity. To delete an old account, use the -d flag.')
            exit(1)

        # Choose username
        print "\nRestrictions:\n" \
              "Usernames can only contain numbers, letters, and hyphens.\n" \
              'The first and last characters must be a number or a letter.\n' \
              'Must be between 3 and 10 characters.' \

        # Assign the username
        global username
        username = raw_input('\nChoose username: ')

        # Checks that username syntax is valid.
        valid = check_username()

        # If valid an Azure cloud service, Azure user storage container, and user folder are created.
        if valid:
            setup_account()
            sub_menu()

        # Username is not valid
        if not valid:
            option = None
            while option not in ['1', '2', '3']:
                option = raw_input('(1) Choose another username\n'
                                   '(2) Back to login\n'
                                   '(3) Quit\n'
                                   '>> ')
                if option not in ['1', '2', '3']:
                    stderr.write("\nInput not recognized.\n")
                    sleep(0.5)

            if option == '1':
                new_user()
            elif option == '2':
                menu()
            elif option == '3':
                quit(0)


def setup_account():

        """
        Creates a container for the user in a Azure storage account and creates a simulation folder
        for simulation results on the user's computer
        :return:
        """

        ########## Create Cloud Service #############
        label = 'IMOD simulation for ' + username
        location = 'East US'

        try:
            sms.create_hosted_service(service_name=username, label=label, description=label, location=location)
        except:
            stderr.write("An error occurred while creating a cloud service for your account")
            exit(1)

        ############ Create User Storage ############
        # Creates a storage container for the user to upload input files
        # and download results files. Named after the username.

        print '\nCreating storage space in cloud...'

        try:
            blob_service.create_container(username.lower())
        except:
            stderr.write("There was an error creating storage for your account.")
            exit(1)

        ######### Create Simulation Folder ##########
        print '\nCreating simulation folder...'

        new_path = 'C:/Users/' + comp_user + '/Simulations'
        if not os.path.exists(new_path):
            os.makedirs(new_path)

        new_path = 'C:/Users/' + comp_user + '/Simulations/' + username
        if not os.path.exists(new_path):
            os.makedirs(new_path)


def check_username():

        """
        Checks that the syntax in the client chosen username is valid. If the username is valid, a cloud service will
        be created for the client and a boolean 'True' will be returned
        :return is_valid:
        """

        is_valid = True

        # Check username for invalid characters
        if not search('^[a-zA-Z0-9-]+$', username):
            is_valid = False
            stderr.write('\nUsername can only contain numbers, letters, and dashes.\n')

        # Check username length
        elif len(username) > 10 or len(username) < 3:
            is_valid = False
            stderr.write('\nUsername must be between 3 and 10 characters.\n')

        # Check username starting/ending characters
        elif not search('^[a-zA-Z].*\w$', username):
            is_valid = False
            stderr.write('\nUsername must start with a letter and end with a letter or a number.\n')

        # Check if username (cloud service) already exists in Azure
        elif not sms.check_hosted_service_name_availability(username).result:
            is_valid = False
            stderr.write('\nUsername is not available.\n')

        sleep(0.5)
        return is_valid


def get_vm_name():

        """
        Generates a name for the VM that will run the simulation. The name is created by add random hex to the client's
        username to create a 15 character string
        :return:
        """

        hash_obj = hashlib.sha1()
        hash_obj.update(str(time()))

        length = 14 - len(username)           # specifies length of rand such that VM name will be 15 characters long
        rand = hash_obj.hexdigest()[:length]  # creates n random digits of hex
        vm_name = username + '-' + rand       # appends random hex number to the username to create a unique VM name

        return vm_name


def check_proj_name(project_name):

        """
        Checks that the project name chosen by the user is unique within their account.
        :param project_name:
        :return:
        """

        name_match = False
        valid = True

        #check_for_file()
        f = open('C:/Users/' + comp_user + '/Simulations/' + username + '/' + username + '_simulations.txt', 'a+')
        f.seek(0)

        # Check if the project name already exists under this account
        for line in f:
            # If the project name is found...
            if search('\t' + project_name.lower() + '$', line.lower()):
                name_match = line.split()[0]  # name_match is the project's associated vm_name
                break

        f.close()

        # Check that the project name is valid
        if search('[ <>:"/\\\|?*]', project_name):
            valid = False

        return name_match, valid


def update_proj_file(vm_name, project_name):

        """
        A timestamp, the simulation project name and its corresponding VM's name is added to a file containing a list of
        all the client's simulation projects. The file is used in retrieving results.
        :param vm_name:
        :param project_name:
        :return:
        """

        #check_for_file()
        f = open('C:/Users/' + comp_user + '/Simulations/' + username + '/' + username + '_simulations.txt', 'a+')
        f.seek(0)

        # Simulation name and it's online ID (VM name) is written to the user's project file
        year = str(localtime()[0])[-2:].zfill(2)
        month = str(localtime()[1]).zfill(2)
        date = str(localtime()[2]).zfill(2)
        hour = str(localtime()[3]).zfill(2)
        minute = str(localtime()[4]).zfill(2)
        sec = str(localtime()[5]).zfill(2)

        timestamp = month + '/' + date + '/' + year + ' ' + hour + ':' + minute + ':' + sec
        f.write(vm_name + " " + timestamp + '\t' + project_name + "\n")
        f.close()


def ARG_setup_proj(project_name, input_f):

        """
        Set up the necessary conditions to run a new simulation. These include generating a name for a new VM, updating
        the client's simulation project file, and zipping and uploading the user specified input
        :param project_name:
        :param input_f:
        :return:
        """

        ###### Create Unique VM Name ######
        vm_name = get_vm_name()

        ## Check Project Name is Unique ###
        exists, valid = check_proj_name(project_name)

        ##### Update Simulation File ######
        # The Simulation name has invalid syntax...
        if not valid:
            stderr.write("\nSimulation name has invalid syntax.")
            exit(1)
        elif exists:
            stderr.write("Simulation name already exists.")
            exit(1)
        else:
            ARG_upload_input(vm_name, input_f)

        return vm_name


def setup_proj():

        """
        Sets up the necessary conditions to run a new simulation. These include generating a name for a new VM, the
        client choosing a simulation project name to associate with this VM, updating the client's simulation project
        file, and zipping and uploading the user specified input
        :return:
        """

        ###### Create Unique VM Name ######
        vm_name = get_vm_name()

        ######## Choose Simulation Name ########
        while 1:
            project_name = raw_input("\nRestrictions: Cannot contain spaces or the following reserved characters \ / < "
                                     "> : \" | ? * \nPress 1 to list existing simulations or enter a name for your new "
                                     "simulation: ")

            if project_name == '1':
                list_projects()
            else:
                break

        # Check that project name doesn't exist and has valid syntax
        name_match, valid = check_proj_name(project_name)

        # The Simulation name has invalid syntax...
        if not valid:
            stderr.write("\nSimulation name has invalid syntax.")
            sleep(0.5)
        # The Simulation name already exists...
        elif name_match:
            stderr.write("\nSimulation name already exists.")
            sleep(0.5)

        # The Simulation name is not valid...
        if name_match or not valid:
            option = None
            while option not in ['1', '2', '3']:
                option = raw_input("\n(1) Re-enter simulation name\n"
                                       "(2) Back to menu\n"
                                       "(3) Quit\n"
                                       ">> ")
                if option not in ['1', '2', '3']:
                    stderr.write("\nInput not recognized.\n")
                    sleep(0.5)

            if option == '1':
                vm_name, project_name = setup_proj()
                return vm_name, project_name
            elif option == '2':
                sub_menu()
            elif option == '3':
                quit(0)


        # Simulation name is valid
        upload_input(vm_name)

        return vm_name, project_name


def ARG_upload_input(vm_name, input_path):

        """
        Calls to zip the provided input files then uploads them to the user's storage container.
        :param vm_name:
        :param input_path:
        :return:
        """

        # Convert to Windows format
        norm_inputs = os.path.normpath(input_path)  # ie C:/Users/SomeName/InputFiles

        # Zip input files
        norm_inputs = zip_files(norm_inputs)

        # If the input path does not exist...
        if not os.path.exists(input_path):
            stderr.write("Input path " + input_path + " does not exist.")
            exit(1)

        # If the input path exists...
        else:
            # Try uploading the specified input
            try:
                blob_service.put_block_blob_from_path(username.lower(), vm_name, norm_inputs)
            except:
                stderr.write('An error occurred uploading your input.')
                exit(1)


def upload_input(vm_name):

        """
        Asks the user for the path to their input necessary to run the simulation. Uploads the folder after calling to
        zip the files.
        :param vm_name:
        :return:
        """

        inputs = raw_input("\nEnter path to your input folder/file: ")

        # Convert path to Windows format
        norm_inputs = os.path.normpath(inputs)  # C:/Users/SomeName/InputFiles

        # Check that path exists
        if not os.path.exists(norm_inputs):
            stderr.write("\nCould not find file.\n")
            sleep(0.5)

            option = None
            while option not in ['1', '2', '3']:
                option = raw_input("(1) Re-enter file path\n"
                                   "(2) Back to menu\n"
                                   "(3) Quit\n"
                                   ">> ")
                if option not in ['1', '2', '3']:
                    stderr.write("\nInput not recognized.\n")
                    sleep(0.5)

            if option == "1":
                upload_input(vm_name)
                return
            elif option == "2":
                sub_menu()
                return
            elif option == "3":
                quit(0)

        # Zip input files
        zipped_inputs = zip_files(norm_inputs)

        # Upload zipped input file to the client's container to be used on the new VM
        # to run the simulation
        try:
            blob_service.put_block_blob_from_path(username.lower(), vm_name, zipped_inputs)
        except:
            stderr.write("An error occurred while uploading your input.")
            exit(1)


def zip_files(inputs):

        """
        Zips the specified folder if necessary.
        :param inputs:
        :return:
        """

        inputs_dir = os.path.dirname(inputs)           # ie C:/Users/SomeName
        inputs_folder_name = os.path.basename(inputs)  # ie InputFiles

        # Zip the input folder, if not already
        if not zipfile.is_zipfile(inputs):

            os.chdir(inputs_dir)
            print "\nZipping file..."

            z = zipfile.ZipFile(inputs_folder_name + '.zip', "w", zipfile.ZIP_DEFLATED)

            # If there is one input file...
            if os.path.isfile(inputs_folder_name):
                z.write(inputs_folder_name)
            # If there are multiple input files in a folder...
            else:
                for user_input in os.listdir(inputs_folder_name):
                    os.chdir(inputs)
                    z.write(user_input)

            z.close()
            zipped_inputs = inputs + '.zip'
            return zipped_inputs

        else:
            return inputs


def remove_proj(vm):

        """
        Removes specified project from the user's simulation file
        :param vm:
        :return:
        """

        #check_for_file()

        f = open('C:/Users/' + comp_user + '/Simulations/' + username + '/' + username + '_simulations.txt', 'r')
        proj_list = f.readlines()
        f.close()

        f = open('C:/Users/' + comp_user + '/Simulations/' + username + '/' + username + '_simulations.txt', 'w')
        for line in proj_list:
            if not search('^' + vm, line):
                f.write(line)
        f.close()


def simulation(vm_name, sim_type, arg=False, del_VM=True):

        """
        Uploads a client's input files for a new simulation to the client's storage container and then creates a VM
        under the client's cloud service on which the simulation will be run.
        :return:
        """

        ######### Create OS Hard Disk #########
        if del_VM:
            if sim_type == "EMOD":
                image_name = 'EMOD-OS-os-2014-07-09'
            elif sim_type == "OM":
                image_name = 'mock-model2-os-2014-07-10'
            elif sim_type == "mock":
                image_name = 'mock-model2-os-2014-07-10'
            else:
                stderr.write('Error')
                exit(1)
        else:
            if sim_type == "EMOD":
                image_name = 'no-delete-EMOD-OS-os-2014-09-17'
            elif sim_type == "OM":
                image_name = 'no-delete-Mock-os-2014-09-17'
            elif sim_type == "mock":
                image_name = 'no-delete-Mock-os-2014-09-17'
            else:
                stderr.write('Error')
                exit(1)

        storage_account = 'portalvhdsd3d1018q65tg3'
        blob = vm_name + '-blob.vhd'
        media_link = "https://" + storage_account + ".blob.core.windows.net/vhds/" + blob

        os_hd = OSVirtualHardDisk(image_name, media_link)

        ###### Windows VM configuration #####
        windows_config = WindowsConfigurationSet(
            computer_name=vm_name,
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

        # Check that there are cores available
        subscription = sms.get_subscription()
        cores_available = subscription.max_core_count - subscription.current_core_count

        if not cores_available:
            stderr.write('No cores are available for usage at this time. Please, wait until a VM can be generated...')

        print "\nCreating VM..."

        # If there's a VM running on the client's service, add a VM to the pre-existing deployment
        wait = True
        first = True

        # Wait until a role can be added to the deployment
        while wait:
            service = sms.get_hosted_service_properties(username, True)
            if service.deployments:
                try:
                    result = sms.add_role(
                        service_name=username,
                        deployment_name=username,
                        role_name=vm_name,
                        system_config=windows_config,
                        os_virtual_hard_disk=os_hd,
                        role_size='Small')
                    wait = False

                except WindowsAzureConflictError:
                    if first:
                        print '\nWindows Azure is currently performing an operation on this deployment that requires ' \
                              'exclusive access. \nPlease, wait...'
                        first = False

                except:
                    stderr.write("There was an error creating a virtual machine to run your simulation.")
                    sleep(0.5)
                    if arg:
                        exit(1)
                    else:
                        sub_menu()
            else:
                wait = False

        # If no VMs are deployed, a VM is deployed on the client's service
        service = sms.get_hosted_service_properties(username, True)
        if not service.deployments:
            try:
                result = sms.create_virtual_machine_deployment(
                        service_name=username,
                        deployment_name=username,
                        deployment_slot='production',
                        label=vm_name,
                        role_name=vm_name,
                        network_config=endpoint_config,
                        system_config=windows_config,
                        os_virtual_hard_disk=os_hd,
                        role_size='Small')

            except:
                stderr.write("There was an error creating a virtual machine to run your simulation.")
                sleep(0.5)
                if arg:
                    exit(1)
                else:
                    sub_menu()

        # Check that the VM was created properly
        status = sms.get_operation_status(result.request_id)
        try:
            stderr.write(vars(status.error))
            exit(1)
        except:
            print "\nSimulation Running! Check back later to retrieve results."


def ARG_get_results(requested_sim):

        """
        Checks if the specified simulation is done running and if its results file has been uploaded
        to the client's storage container. If the simulation has finished, the results are downloaded
        to the clients computer.
        :return:
        """

        print "Checking for " + requested_sim + " results..."
        # Check if project is listed in client's simulation file
        proj_match, valid = check_proj_name(requested_sim)

        ######## Get Results if Ready ########
        if not proj_match:
            stderr.write("\nProject does not exist.")
            exit(1)
        elif proj_match:
            # Retrieve names of all user's files in their container
            try:
                blobs = blob_service.list_blobs(container_name=username.lower())
            except:
                stderr.write('An error occurred while accessing your storage.')
                exit(1)

            sim_results = 'r-' + proj_match
            results_in = False

            # Check if results are in
            for uploaded_file in blobs:
                if uploaded_file.name == sim_results:
                    # Download results file
                    file_path = 'c:/Users/' + comp_user + '/Simulations/' + username + '/' + requested_sim + \
                                '_results.zip'
                    try:
                        blob_service.get_blob_to_path(username.lower(), sim_results, file_path)
                    except:
                        stderr.write('An error occurred while downloading your results.')
                        exit(1)

                    extract_files(requested_sim + '_results')

                    results_in = True
                    break

            if results_in:
                print "\nYour results are in! Check C:/Users/" + comp_user + "/Simulations/" + username + " for " \
                      "the " + requested_sim + "_results folder."
            else:
                print "\nThe simulation is still running. Check back later to retrieve results."


def get_results():

        """
        Checks if the specified simulation is done running and if its results file has been uploaded
        to the client's storage container. If the simulation has finished, the results are downloaded
        to the clients computer.
        :return:
        """

        ######## Get Simulation Name #########
        requested_sim = raw_input("\nSelect a project to check for results.\n"
                                  "Press '1' to list projects or enter project name: ")
        if requested_sim == '1':
            list_projects()
            get_results()

        # Check if project is listed in client's simulation file
        name_match, valid = check_proj_name(requested_sim)

        ######## Get Results if Ready ########
        if not name_match:
            print "\nProject does not exist."

            option = None
            while option not in ['1', '2', '3']:
                option = raw_input("(1) Check another project\n"
                                       "(2) Back to menu\n"
                                       "(3) Quit\n"
                                       ">> ")
                if option not in ['1', '2', '3']:
                    stderr.write("\nInput not recognized.\n")
                    sleep(0.5)

            if option == '1':
                get_results()
                return
            elif option == '2':
                sub_menu()
            elif option == '3':
                quit(0)

        elif name_match:
            # Retrieve all user's files from their container
            try:
                blobs = blob_service.list_blobs(container_name=username.lower())
            except:
                stderr.write('An error occurred while trying to access your storage.')
                exit(1)

            sim_results = 'r-' + name_match
            results_in = False

            # Check if results are in
            for uploaded_file in blobs:
                if uploaded_file.name == sim_results:
                    # Download results file
                    file_path = 'c:/Users/' + comp_user + '/Simulations/' + username + '/' + requested_sim + \
                                '_results.zip'
                    try:
                        blob_service.get_blob_to_path(username.lower(), sim_results, file_path)
                    except:
                        stderr.write('An error occurred when trying to download your results.')
                        exit(1)

                    # Extract results
                    extract_files(requested_sim + '_results')
                    results_in = True

                    break

            if results_in:
                print "\nYour results are in! Check C:/Users/" + comp_user + "/Simulations/" + username + " for " \
                      "the " + requested_sim + "_results folder."
                sub_menu()
            else:
                # If the results are not in and the VM is still running...
                try:
                    sms.get_role(username, username, name_match)
                    # The simulation is still running
                    print "\nThe simulation is still running. Check back later to retrieve results."

                # If the results are not in but the VM is already deleted...
                except:
                    # The results did not upload
                    print "Your results were unable to be uploaded. Try running the simulation again."

                sub_menu()


def extract_files(file_name):

        """
        Unzips files from the provided path.
        :param file_name:
        :return:
        """

        output_path = os.path.normpath('C:/Users/' + comp_user + '/Simulations/' + username)
        os.chdir(output_path)

        z = zipfile.ZipFile(file_name + '.zip', 'r')
        z.extractall(file_name)
        z.close()

        os.remove(file_name + '.zip')


def list_projects():
        """
        Lists all the client's simulations and their time stamps.
        :return:
        """

        print '\n  ' + username + '\'s Projects:'
        project_file = 'C:/Users/' + comp_user + '/Simulations/' + username + '/' + username + '_simulations.txt'
        if not os.path.exists(project_file):
            print '    None'
        else:
            #check_for_file()
            f = open('C:/Users/' + comp_user + '/Simulations/' + username + '/' + username + '_simulations.txt', "r")

            if os.path.getsize(project_file) > 0:
                for line in f:
                    split_line = line.split()
                    length = len(split_line)
                    sim_name = ' '.join(split_line[1:length])
                    print '    ' + sim_name
            else:
                print '    None'

            f.close()


def delete_account(account_name, arg=False):

        """
        Deletes the specified user account. This includes deleting the associated cloud service, storage container, and
        simulation file.
        :param account_name:
        :param arg:
        :return:
        """

        if check_user_exists(account_name):
            user_input = raw_input("\nAre you sure you want to delete " + account_name + "'s account? (y/n): ")

            if user_input == 'y':
                print '\nDeleting ' + account_name + '\'s account...'
                wait = True
                first = True

                # Deletes deployment on user's cloud service if needed
                while wait:
                    service = sms.get_hosted_service_properties(account_name, True)
                    if service.deployments:
                        try:
                            sms.delete_deployment(account_name, account_name)
                        except WindowsAzureConflictError:
                            if first:
                                print '\nWindows Azure is currently performing an operation on this account that ' \
                                      'requires exclusive access. \nPlease, wait...'
                                first = False
                        except:
                            stderr.write('\nAn error occurred while deleting your account.')
                            if arg:
                                exit(1)
                            else:
                                sub_menu()

                    else:
                        wait = False

                try:
                    sms.delete_hosted_service(account_name)
                    blob_service.delete_container(account_name.lower())
                except not WindowsAzureMissingResourceError:
                    stderr.write('\nAn error occurred while deleting your account.')
                    if arg:
                        exit(1)
                    else:
                        sub_menu()

                path = 'C:/Users/' + comp_user + '/Simulations/' + account_name + '/' + account_name + \
                       '_simulations.txt'
                if os.path.exists(path):
                    os.remove(path)
            elif user_input == 'n':
                sub_menu()
            else:
                stderr.write('')
        else:
            stderr.write('Account does not exist.')
            if arg:
                exit(1)
            else:
                menu()


########################################################################################################################
##                                                        MAIN                                                        ##
########################################################################################################################


# Create service management object
subscription_id = 'a9401417-cb08-4e67-bc2a-613f49b46f8a'
certificate_path = 'CURRENT_USER\\my\\AzureCertificate'
sms = ServiceManagementService(subscription_id, certificate_path)

# Create blob service object
blob_service = BlobService(
    account_name='portalvhdsd3d1018q65tg3',
    account_key='cAT5jbypcHrN7sbW/CHgGFDGSvOpyhw6VE/yHubS799egkHfvPeeXuK7uzc6H2C8ZU1ALiyOFEZkjzWuSyfc+A==')

# Test the service management object
try:
    sms.get_subscription()
except:
    stderr.write("An error occurred while connecting to Azure Service Management. Please, check your service "
                 "management certificate.")
    exit(1)

# The current user on the computer; used to access the right folder under C:/Users
global comp_user
global comp_user
comp_user = getuser()

# Check for command line arguments
UI = True

if len(sys.argv) > 1:
    use_string = 'Setup_Sim.py [-h] [-new] username [ -d | [-ncln] -sE INPUT_FOLDER SIMULATION_NAME | [-ncln] ' \
                 '-sOM INPUT_FOLDER SIMULATION_NAME | [-ncln] -m INPUT_FOLDER SIMULATION_NAME | -r SIMULATION_NAME ]'
    parser = argparse.ArgumentParser(usage=use_string)

    parser.add_argument("-new", "--new_user", action="store_true",
                        help="New user; create an account")
    parser.add_argument("username", type=str,
                        help="Username for simulation account")
    parser.add_argument("-ncln", "--cleanup_off", action="store_true",
                        help="Turn off automatic cleanup of VM instances (VMs not deleted)")

    options_group = parser.add_mutually_exclusive_group()
    options_group.add_argument("-sOM", "--OpenMalaria", nargs=2, type=str, action="store",
                               help="Runs new Open Malaria simulation; must provide file path to input folder and "
                                    "a new simulation name")
    options_group.add_argument("-sE", "--EMOD", nargs=2, type=str, action="store",
                               help="Runs new EMOD simulation; must provide file path to input folder and a new "
                                    "simulation name")
    options_group.add_argument("-r", "--get_results", nargs=1, type=str, action="store",
                               help="Get simulation results; must provide simulation name")
    options_group.add_argument("-d", "--delete", action="store_true",
                               help="Delete account")
    options_group.add_argument("-m", "--mock_model", nargs=2, type=str, action="store",
                               help="mock model; returns uploaded input")

    args = parser.parse_args()
    UI = False


# Begin Tasks
if UI:
    menu()
else:
    if not args.delete and not (args.EMOD or args.OpenMalaria or args.mock_model) and not args.get_results:
        stderr.write(use_string + '\nSetup_Sim.py: error: too few arguments.\n')
        exit(2)

    if args.new_user and args.delete:
        stderr.write(use_string + '\nSetup_Sim.py: error: argument -new/--new_user: not allowed with argument '
                     '-d/--delete')
        exit(2)

    if args.cleanup_off and args.get_results:
        stderr.write(use_string + '\nSetup_Sim.py: error: argument -ncln/--cleanup_off: not allowed with argument '
                     '-r/--get_results')
        exit(2)

    if args.cleanup_off and not (args.cleanup_off and (args.EMOD or args.OpenMalaria or args.mock_model)):
        stderr.write(use_string + '\nSetup_Sim.py: error: -ncln/--cleanup_off: must use additional argument '
                     '-sE/--EMOD, -sOM/--OpenMalaria, or -m/--mock_model')
        exit(2)


    if args.new_user:
        ARG_new_user(args.username)

    elif args.delete:
        delete_account(args.username, True)

    else:
        ARG_sign_in(args.username)

    if args.cleanup_off:
        del_VM = False
    else:
        del_VM = True

    if args.EMOD:
        vm_name = ARG_setup_proj(args.EMOD[1], args.EMOD[0].strip('"'))
        simulation(vm_name, "EMOD", True, del_VM)
        update_proj_file(vm_name, args.EMOD[1])

    elif args.OpenMalaria:
        vm_name = ARG_setup_proj(args.OpenMalaria[1], args.OpenMalaria[0])
        simulation(vm_name, "OM", True, del_VM)
        update_proj_file(vm_name, args.OpenMalaria[1])

    elif args.mock_model:
        vm_name = ARG_setup_proj(args.mock_model[1], args.mock_model[0])
        simulation(vm_name, "mock", True, del_VM)
        update_proj_file(vm_name, args.mock_model[1])

    elif args.get_results:
        ARG_get_results(args.get_results[0])