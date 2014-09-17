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
            '(4) Logout\n'
            '(5) Quit\n'
            '>> ')

        if user_input == '1':
            # creates a VM under client's cloud service, running the EMOD simulation
            vm_name = setup_proj()
            simulation(vm_name, 'EMOD')
            sub_menu()
        elif user_input == '2':
            # creates a VM under client's cloud service, running the Open Malaria simulation
            vm_name = setup_proj()
            simulation(vm_name, 'OM')
            sub_menu()
        elif user_input == '3':
            # returns the results of a previously run simulation specified by the client
            get_results()
        elif user_input == '4':
            menu()
        elif user_input == '5':
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

    exists = check_user_exists()

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
        exists = check_user_exists()

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


def check_user_exists():

        """
        Checks that the username used to login exists, that is that there is a cloud service for this username.
        :return:
        """
        services = sms.list_hosted_services()  # Lists all cloud services
        exists = False

        # Checks that given username exists as a cloud service
        for hosted_service in services:
            if hosted_service.service_name == username:
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
        global username
        username = user

        # Check that username has correct syntax
        valid = check_syntax()

        # If valid a cloud service is created.
        if valid:
            label = 'IMOD simulation for ' + username
            location = 'East US'
            sms.create_hosted_service(service_name=username, label=label, description=label, location=location)
            setup_account()

        elif not valid:
            exit(1)


def new_user():

        """
        New clients create a username in order to create an 'account' where simulations
        can be stored and accessed. Their username is used to create a cloud service
        which will run all their simulations on VMs and to create a storage account where
        input and results files and loaded/downloaded.
        :return:
        """

        # Choose username
        print "\nRestrictions:\n" \
              "Usernames can only contain numbers, letters, and hyphens.\n" \
              'The first and last characters must be a number or a letter.\n' \
              'Must be between 3 and 10 characters.' \

        global username
        username = raw_input('\nChoose username: ')

        # Checks that username syntax is valid.
        valid = check_syntax()

        # If valid a cloud service is created.
        if valid:
            label = 'IMOD simulation for ' + username
            location = 'East US'
            sms.create_hosted_service(service_name=username, label=label, description=label, location=location)

            setup_account()
            sub_menu()

        # Username is not valid
        elif not valid:
            while 1:
                user_input = raw_input('(1) Choose another username\n'
                                       '(2) Back to login\n'
                                       '(3) Quit\n'
                                       '>> ')
                if user_input == '1':
                    new_user()
                elif user_input == '2':
                    menu()
                elif user_input == '3':
                    quit(0)
                else:
                    stderr.write("\nInput not recognized.\n")
                    sleep(0.5)


def setup_account():

        """
        Creates a container for the user in a Azure storage account and creates a simulation folder
        for simulation results on the user's computer
        :return:
        """

        ############ Create User Storage ############
        # Creates a storage container for the user to upload input files
        # and download results files. Named after the username.

        print 'Creating storage space in cloud...'
        blob_service = BlobService(
            account_name='portalvhdsd3d1018q65tg3',
            account_key='cAT5jbypcHrN7sbW/CHgGFDGSvOpyhw6VE/yHubS799egkHfvPeeXuK7uzc6H2C8ZU1ALiyOFEZkjzWuSyfc+A==')
        blob_service.create_container(username.lower())

        ######### Create Simulation Folder ##########
        print 'Creating simulation folder...'
        new_path = 'C:/Users/' + comp_user + '/Simulations'
        if not os.path.exists(new_path):
            os.makedirs(new_path)

        new_path = 'C:/Users/' + comp_user + '/Simulations/' + username
        if not os.path.exists(new_path):
            os.makedirs(new_path)
            f1 = open(new_path + "/" + username + "_simulations.txt", "w+")
            f1.close()

def check_syntax():

        """
        Checks that the syntax in the client chosen username is valid. If the username is valid, a cloud service will
        be created for the client and a boolean 'True' will be returned
        :return is_valid:
        """

        is_valid = True

        # Check username length
        if len(username) > 10 or len(username) < 3:
            is_valid = False
            stderr.write('\nUsername must be between 3 and 10 characters.\n')

        # Check username starting/ending characters
        elif not search('^[a-zA-Z].*\w$', username):
            is_valid = False
            stderr.write('\nUsername must start with a letter and end with a letter or a number.\n')

        # Check username for invalid characters
        elif not search('^[a-zA-Z0-9-]+$', username):
            is_valid = False
            stderr.write('\nUsername can only contain numbers, letters, and dashes.\n')

        # Check if username (cloud service) already exists in Azure
        elif not sms.check_hosted_service_name_availability(username).result:
            is_valid = False
            stderr.write('\nUsername already exists.\n')

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

        f = open('C:/Users/' + comp_user + '/Simulations/' + username + '/' + username + '_simulations.txt', 'a+')
        f.seek(0)

        # Check if the project name already exists under this account
        for line in f:
            if search('\t' + project_name.lower() + '$', line.lower()):
                name_match = line.split()[0]  # project name was found; indicates 'True'
                break

        f.close()

        # Check that the project name is valid
        if search('[ <>:"/\\\|?*]', project_name):
            valid = False

        return name_match, valid


def update_proj_file(vm_name, project_name, saved_input):

        """
        A timestamp, the simulation project name and its corresponding VM's name is added to a file containing a list of
        all the client's simulation projects. The file is used in retrieving results.
        :param vm_name:
        :param project_name:
        :return:
        """

        f = open('C:/Users/' + comp_user + '/Simulations/' + username + '/' + username + '_simulations.txt', 'a+')
        f.seek(0)

        # Simulation name and it's online ID (VM name) is written to the user's project file
        year = str(localtime()[0])[-2:].zfill(2)
        month = str(localtime()[1]).zfill(2)
        date = str(localtime()[2]).zfill(2)
        hour = str(localtime()[3]).zfill(2)
        minute = str(localtime()[4]).zfill(2)
        sec = str(localtime()[5]).zfill(2)

        timestamp = month + '/' + date + '/' + year + ' ' + hour + ':' + minute + ':' + sec + '\t'

        # If user chose to save the new input, check that the input name doesn't already exist
        if not saved_input == ".":
            saved_input = os.path.basename(saved_input)
            saved_input_exists = check_saved_inputs(saved_input)

            # If the input name exists, get new name to save under or quit the save
            if saved_input_exists:
                user_input = raw_input("The input name " + saved_input + " already exists. Enter a new name to call this "
                                        "input or cancel save (q): ")
                if user_input == "q":
                    saved_input = "."
                else:
                    saved_input = user_input
                    update_proj_file(vm_name, project_name, saved_input)

        f.write(vm_name + "|" + saved_input + "|" + timestamp + project_name + "\n")
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
        name_match, valid = check_proj_name(project_name)

        if not valid:
            stderr.write("Simulation name has invalid syntax.")
            exit(1)
        elif name_match:
            stderr.write("Simulation name already exists.")
            exit(1)

        else:
            save_input = ARG_upload_input(vm_name, input_f)
            update_proj_file(vm_name, project_name, save_input)
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
            project_name = raw_input("\nRestrictions: Cannot contain spaces or the following reserved characters \ / < > : \" | ? *\n"
                                     "Press 1 to list existing simulations or enter a name for your new simulation: ")

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

        # User options if provided simulation name is invalid
        if name_match or not valid:
            while 1:
                user_input = raw_input("\n(1) Re-enter simulation name\n"
                                       "(2) Back to menu\n"
                                       "(3) Quit\n"
                                       ">> ")
                if user_input == '1':
                    setup_proj()
                elif user_input == '2':
                    sub_menu()
                elif user_input == '3':
                    quit(0)
                else:
                    stderr.write("\nInput not recognized.\n")
                    sleep(0.5)

        # Simulation name is valid
        else:
            new_save = upload_input(vm_name)
            update_proj_file(vm_name, project_name, new_save)

            return vm_name


def ARG_upload_input(vm_name, input_path):

        """
        Calls to zip the provided input files then uploads them to the user's storage container.
        :param vm_name:
        :param input_path:
        :return:
        """
        blob_service = BlobService(
            account_name='portalvhdsd3d1018q65tg3',
            account_key='cAT5jbypcHrN7sbW/CHgGFDGSvOpyhw6VE/yHubS799egkHfvPeeXuK7uzc6H2C8ZU1ALiyOFEZkjzWuSyfc+A==')

        # Convert to Windows format
        norm_inputs = os.path.normpath(input_path)  # ie C:\Users\SomeName\Input instead of C:/Users/SomeName/Input

        # Zip input files
        norm_inputs = zip_files(norm_inputs)

        # If input path does not exist...
        if not os.path.exists(input_path):
            stderr.write("Input path " + input_path + " does not exist.")
            exit(1)
        else:
            blob_service.put_block_blob_from_path(username.lower(), vm_name, norm_inputs)


def upload_input(vm_name):

        """
        Asks the user for the path to their input necessary to run the simulation. Uploads the folder after calling to
        zip the files.
        :param vm_name:
        :return:
        """

        new_save = "."
        saved_input = None

        blob_service = BlobService(
            account_name='portalvhdsd3d1018q65tg3',
            account_key='cAT5jbypcHrN7sbW/CHgGFDGSvOpyhw6VE/yHubS799egkHfvPeeXuK7uzc6H2C8ZU1ALiyOFEZkjzWuSyfc+A==')

        inputs = raw_input("\nEnter path to your input or the name of a saved input. To list saved inputs, press 1: ")

        if inputs == '1':
            list_saved_inputs()
            upload_input(vm_name)
        else:
            saved_input = check_saved_inputs(inputs)

            if saved_input is None:
                # Convert file path to Windows format
                norm_inputs = os.path.normpath(inputs)  # ie C:\Users\SomeName\Input instead of C:/Users/SomeName/Input

                # If path does not exist...
                if not os.path.exists(norm_inputs):
                    stderr.write("\nCould not find file.\n")
                    sleep(0.5)
                    while 1:
                        user_input = raw_input("(1) Re-enter file path\n"
                                               "(2) Back to menu\n"
                                               "(3) Quit\n"
                                               ">> ")
                        if user_input == "1":
                            upload_input(vm_name)
                        elif user_input == "2":
                            sub_menu()
                        elif user_input == "3":
                            quit(0)
                        else:
                            stderr.write("\nInput not recognized.\n")
                            sleep(0.5)
                # If path exists...
                else:
                    # Zip input files
                    zipped_inputs = zip_files(norm_inputs)

                    # Upload zipped input file to the client's container to be used on the new VM to run the simulation
                    blob_service.put_block_blob_from_path(username.lower(), vm_name, zipped_inputs)

                    save = raw_input("\nDo you want to save these input/s to the cloud for future use? Saved inputs will"
                                     " only be uploaded once. (y/n): ")

                    if save == 'y':
                        new_save = inputs
                    elif save == 'n':
                        new_save = "."

            # If the requested input is saved...
            else:
                path = "C:/Users/" + comp_user + "/Simulations/" + username
                os.chdir(path)
                f = open('INPUT_TO_USE.txt', 'w+')
                f.write(saved_input)
                f.close()

                zipped_inputs = zip_files(path + '/INPUT_TO_USE.txt')
                blob_service.put_block_blob_from_path(username.lower(), vm_name, zipped_inputs)

                os.remove(zipped_inputs)
                os.remove('INPUT_TO_USE.txt')

        return new_save


def check_saved_inputs(input_name):
    os.chdir('C:/Users/' + comp_user + '/Simulations/' + username)
    f = open(username + "_simulations.txt", 'r')

    cloud_input_name = None
    for line in f:
        match = search(".{15}\|" + input_name + "\|\d\d", line)
        if match:
            cloud_input_name = line.split("|")[0]
            break

    f.close()
    return cloud_input_name

def zip_files(inputs):

        """
        Zips the specified folder if necessary.
        :param inputs:
        :return:
        """
        inputs_dir = os.path.dirname(inputs)           # ie C:/Users/SomeName
        inputs_folder_name = os.path.basename(inputs)  # ie InputFiles

        # Zip the input folder/file, if not already
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


def simulation(vm_name, sim_type):

        """
        Uploads a client's input files for a new simulation to the client's storage container and then creates a VM
        under the client's cloud service on which the simulation will be run.
        :return:
        """

        ######### Create OS Hard Disk #########
        if sim_type == "EMOD":
            image_name = 'emod-simulation-os-2014-06-30'
        elif sim_type == "OM":
            image_name = 'Open-Malaria-os-2014-07-07'  #OM-test3-os-2014-07-02'

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
        result = sms.get_hosted_service_properties(username, True)

        # If there's a VM running on the client's service, add a VM to the pre-existing deployment
        if result.deployments:
            print "\nCreating VM..."
            sms.add_role(
                service_name=username,
                deployment_name=username,
                role_name=vm_name,
                system_config=windows_config,
                os_virtual_hard_disk=os_hd,
                role_size='Small')

        # Otherwise, no VMs are deployed and a VM is deployed on the client's service
        else:
            print "\nCreating VM..."
            sms.create_virtual_machine_deployment(
                service_name=username,
                deployment_name=username,
                deployment_slot='production',
                label=vm_name,
                role_name=vm_name,
                network_config=endpoint_config,
                system_config=windows_config,
                os_virtual_hard_disk=os_hd,
                role_size='Small')

        print "\nSimulation Running! Check back later to retrieve results."


def ARG_get_results(requested_sim):

        """
        Checks if the specified simulation is done running and if its results file has been uploaded
        to the client's storage container. If the simulation has finished, the results are downloaded
        to the clients computer.
        :return:
        """

        # Check if project is listed in client's simulation file
        proj_exists, valid = check_proj_name(requested_sim)

        ######## Get Results if Ready ########
        if not proj_exists:
            stderr.write("\nProject does not exist.")
            exit(1)
        elif proj_exists:
            vm_name = proj_exists  # if project exists the vm name is returned
            blob_service = BlobService(
                account_name='portalvhdsd3d1018q65tg3',
                account_key='cAT5jbypcHrN7sbW/CHgGFDGSvOpyhw6VE/yHubS799egkHfvPeeXuK7uzc6H2C8ZU1ALiyOFEZkjzWuSyfc+A==')

            # Retrieve names of all user's files in their container
            blobs = blob_service.list_blobs(container_name=username.lower())
            sim_results = 'r-' + vm_name
            results_in = False

            # Check if results are in
            for uploaded_file in blobs:
                if uploaded_file.name == sim_results:
                    # Download results file
                    file_path = 'c:/Users/' + comp_user + '/Simulations/' + username + '/' + requested_sim + '_results.zip'
                    blob_service.get_blob_to_path(username.lower(), sim_results, file_path)

                    extract_files(requested_sim + '_results')

                    results_in = True
                    break

            if results_in:
                print "\nYour results are in! Check C:/Users/" + comp_user + "/Simulations/" + username + " for " + \
                      requested_sim + "_results."
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
        proj_exists, valid = check_proj_name(requested_sim)

        ######## Get Results if Ready ########
        if not proj_exists:
            print "\nProject does not exist."
            while 1:
                user_input = raw_input("(1) Check another project\n"
                                       "(2) Back to menu\n"
                                       "(3) Quit\n"
                                       ">> ")
                if user_input == '1':
                    get_results()
                elif user_input == '2':
                    sub_menu()
                elif user_input == '3':
                    quit(0)
                else:
                    print "\nInput not recognized.\n"
        elif proj_exists:
            vm_name = proj_exists
            blob_service = BlobService(
                account_name='portalvhdsd3d1018q65tg3',
                account_key='cAT5jbypcHrN7sbW/CHgGFDGSvOpyhw6VE/yHubS799egkHfvPeeXuK7uzc6H2C8ZU1ALiyOFEZkjzWuSyfc+A==')

            # Retrieve all user's files from their container
            blobs = blob_service.list_blobs(container_name=username.lower())
            sim_results = 'r-' + vm_name
            results_in = False

            # Check if results are in
            for uploaded_file in blobs:
                if uploaded_file.name == sim_results:
                    # Download results file
                    file_path = 'c:/Users/' + comp_user + '/Simulations/' + username + '/' + requested_sim + '_results.zip'
                    blob_service.get_blob_to_path(username.lower(), sim_results, file_path)

                    # Extract results
                    extract_files(requested_sim + '_results')
                    results_in = True
                    break

            if results_in:
                print "\nYour results are in! Check C:/Users/" + comp_user + "/Simulations/" + username + " for " + \
                      requested_sim + "_results."
                sub_menu()
            else:
                print "\nThe simulation is still running. Check back later to retrieve results."
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

        f = open('C:/Users/' + comp_user + '/Simulations/' + username + '/' + username + '_simulations.txt', "r")

        for line in f:
            split_line = line.split("|")
            print split_line[2].strip()

        f.close()


def list_saved_inputs():
        """
        Lists all the client's saved inputs
        :return:
        """

        f = open('C:/Users/' + comp_user + '/Simulations/' + username + '/' + username + '_simulations.txt', "r")

        for line in f:
            split_line = line.split('|')
            if not split_line[1] == ".":
                print split_line[1].strip()

        f.close()


########################################################################################################################
#                                                         MAIN                                                         #
########################################################################################################################


# Create service management object
subscription_id = 'a9401417-cb08-4e67-bc2a-613f49b46f8a'
certificate_path = 'CURRENT_USER\\my\\azure'
sms = ServiceManagementService(subscription_id, certificate_path)

# The current user on the computer; used to access the right folder under C:/Users
global comp_user
comp_user = getuser()

# Check for command line arguments
UI = True

if len(sys.argv) > 1:
    use_string = 'Setup_Sim.py [-h] [-new] username sim_name [-sE INPUT_FOLDER | -sOM INPUT_FOLDER | -r]'
    parser = argparse.ArgumentParser(usage=use_string)

    parser.add_argument("-new", "--new_user", action="store_true",
                        help="New user; create an account")
    parser.add_argument("username", type=str,
                        help="Username for simulation account")
    parser.add_argument("simulation_name", type=str,
                        help="Simulation name")

    options_group = parser.add_mutually_exclusive_group()
    options_group.add_argument("-sOM", "--OpenMalaria", nargs=1, type=str, action="store", dest='OM_input',
                               help="Runs new Open Malaria simulation; must provide file path to input folder")
    options_group.add_argument("-sE", "--EMOD", nargs=1, type=str, action="store", dest='E_input',
                               help="Runs new EMOD simulation; must provide file path to input folder")
    options_group.add_argument("-r", "--get_results", action="store_true",
                               help="Get simulation results")

    args = parser.parse_args()
    UI = False


# Begin Tasks
if UI:
    menu()
else:
    new = getattr(args, 'new_user')
    username = getattr(args, 'username')
    input_EMOD = getattr(args, 'E_input')
    input_OM = getattr(args, 'OM_input')
    sim_name = getattr(args, 'simulation_name')
    results = getattr(args, 'get_results')

    if not (input_EMOD or input_OM) and not results:
        stderr.write(use_string + '\nSetup_Sim.py: error: too few arguments.\n')
        exit(2)

    if new:
        ARG_new_user(username)
    else:
        ARG_sign_in(username)

    if input_EMOD:
        vm_name = ARG_setup_proj(sim_name, input_EMOD[0])
        simulation(vm_name, "EMOD")
    elif input_OM:
        vm_name = ARG_setup_proj(sim_name, input_EMOD[0])
        simulation(vm_name, "OM")
    elif results:
        ARG_get_results(sim_name)