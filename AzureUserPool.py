__author__ = 'Natalie'

import os
import AzureUser
from azure           import *
from time            import sleep
from sys             import stderr
from AzureSimulation import sms, blob_service
from AzureTools      import comp_user
from copy            import copy
from validate_email  import validate_email

class AzureUserPool:
    def __init__(self):
        self.user_list = {}
        self.curr_user = AzureUser.AzureUser()

    def add_user(self, name="", ARG=False):
        """
        The provided username is used to to create a new 'account' where simulations
        can be stored and accessed. The client's username is used to create a cloud service
        which will run all their simulations on VMs and to create a storage account where
        input and results files and loaded/downloaded.
        :param name:
        :param ARG:
        :return:
        """

        # Check that there is room for more cloud services.
        subscription = sms.get_subscription()
        services_available = subscription.max_hosted_services - subscription.current_hosted_services

        if ARG:
            self.curr_user.username = name

            if not services_available:
                stderr.write('This Azure subscription has reached capacity. To delete an old account, use the -d flag.')
                exit(1)

            # Check that username has correct syntax and is available
            valid = self.curr_user.check_username()

            # If valid a cloud service is created.
            if valid:
                self.setup_account()
                self.save_user()
            # If not valid, the program exits
            else:
                exit(1)

        else:
            if not services_available:
                stderr.write('This Azure subscription has reached capacity.')
                return 1

            if self.user_getUsername() == 1:
                return 1
            if self.user_getEmail() == 1:
                return 1
            self.setup_account()
            self.save_user()

            return 0

    def user_getUsername(self):
        """
        User chooses a username which is checked for uniqueness and validity
        :return:
        """

        # Choose username
        print "\nRestrictions:\n" \
              "Usernames can only contain numbers, letters, and hyphens.\n" \
              'The first and last characters must be a number or a letter.\n' \
              'Must be between 3 and 10 characters.' \

        # Assign the username
        self.curr_user.username= raw_input('\nChoose username: ')

        # Username is not valid
        while self.curr_user.check_username() == False:
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
                self.curr_user.username= raw_input('\nChoose username: ')
            elif option == '2':
                return 1
            elif option == '3':
                quit(0)

    def user_getEmail(self):
        """
        User gives their email so that results can be sent to the directly
        :return:
        """

        # Assign the username
        self.curr_user.email= raw_input('\nPlease, enter an email address to receive your results: ')

        # Email is not valid
        if not validate_email(self.curr_user.email):
            print "\nEmail invalid"
            option = None
            while option not in ['1', '2', '3']:
                option = raw_input('\n(1) Enter email again\n'
                                   '(2) Back to login\n'
                                   '(3) Quit\n'
                                   '>> ')
                if option not in ['1', '2', '3']:
                    stderr.write("\nInput not recognized.\n")
                    sleep(0.5)
            if option == '1':
                self.curr_user.email= raw_input('\nPlease, enter an email address to receive your results: ')
            elif option == '2':
                return 1
            elif option == '3':
                quit(0)

    def save_user(self):
        """
        The current user is saved to the UserPool list
        :return:
        """

        self.curr_user.save_curr_sim() # saves current simulation of the current user

        key = copy(self.curr_user.username)
        val = copy(self.curr_user)
        self.user_list[key] = val # saves a copy of the user to the user_list

    def logout(self):
        """
        curr_user is given a new object
        :return:
        """

        key = copy(self.curr_user.username)
        val = copy(self.curr_user)

        self.user_list[key] = val # so that changing curr_user when someone logs back in won't alter the dictionary entry
        self.curr_user = AzureUser.AzureUser()

    def setup_account(self):
        """
        Creates a container for the user in a Azure storage account and creates a simulation folder
        for simulation results on the user's computer
        :return:
        """

        ########## Create Cloud Service #############
        label = 'IMOD simulation for ' + self.curr_user.username
        location = 'East US'

        try:
            sms.create_hosted_service(service_name=self.curr_user.username, label=label, description=label, location=location)
        except:
            stderr.write("An error occurred while creating a cloud service for your account")
            exit(1)

        ############ Create User Storage ############
        # Creates a storage container for the user to upload input files
        # and download results files. Named after the username.

        print '\nCreating storage space in cloud...'

        try:
            blob_service.create_container(self.curr_user.username.lower())
        except:
            stderr.write("There was an error creating storage for your account.")
            exit(1)

        ######### Create Simulation Folder ##########
        print '\nCreating simulation folder...'

        new_path = 'C:/Users/' + comp_user + '/Simulations'
        if not os.path.exists(new_path):
            os.makedirs(new_path)

        new_path = 'C:/Users/' + comp_user + '/Simulations/' + self.curr_user.username
        if not os.path.exists(new_path):
            os.makedirs(new_path)

    def sign_in(self, name="", ARG=False):
        """
        User signs in via commandline or UI with their username, loading the appropriate object from the UserPool
        :param name:
        :param ARG:
        :return:
        """

        if(ARG):
            exists = self.check_user_exists(name)

            if not exists:
                stderr.write("Username does not exist. Use the '-new' flag to create a new account.")
                exit(1)
            else:
                self.curr_user = self.user_list[name]
        else:
            while True:
                name = raw_input('\nEnter username: ')

                # Check username exists
                exists = self.check_user_exists(name)

                # Username does not exist
                if not exists:
                    stderr.write('\nUsername does not exist.\n')
                    sleep(0.5)
                    option = None

                    while option not in ['1', '2', '3']:
                        option = raw_input(
                            '(1) Re-enter username\n'
                            '(2) Back to login\n'
                            '(3) Quit\n'
                            '>> ')

                        if option not in ['1', '2', '3']:
                            stderr.write("\nInput not recognized.\n")
                            sleep(0.5)
                        elif option == '2':
                            return 1
                        elif option == '3':
                            quit(0)

                else:
                    self.curr_user = self.user_list[name]
                    return 0

    def check_user_exists(self, name):
        """
        Checks that the username used to login exists, that is that there is a cloud service for this username.
        :param name:
        :return:
        """

        services = sms.list_hosted_services()  # Lists all cloud services

        # Checks that given username exists as a cloud service
        exists1 = False
        exists2 = False

        for hosted_service in services:
            if hosted_service.service_name == name:
                exists1 = True
                break

        if self.user_list.has_key(name):
            exists2 = True

        return (exists1 and exists2)

    def delete_account(self, ARG=False):
        """
        Deletes the specified user account. This includes deleting the associated cloud service, storage container, and
        simulation file.
        :param ARG:
        :return:
        """

        if self.check_user_exists(self.curr_user.username):
            user_input = raw_input("\nAre you sure you want to delete " + self.curr_user.username + "'s account? (y/n): ")

            if user_input == 'y':
                print '\nDeleting ' + self.curr_user.username + '\'s account...'
                wait = True
                first = True

                # Deletes deployment on user's cloud service if needed
                while wait:
                    service = sms.get_hosted_service_properties(self.curr_user.username, True)
                    if service.deployments:
                        try:
                            sms.delete_deployment(self.curr_user.username, self.curr_user.username)
                        except WindowsAzureConflictError:
                            if first:
                                print '\nWindows Azure is currently performing an operation on this account that ' \
                                      'requires exclusive access. \nPlease, wait...'
                                first = False
                        except:
                            stderr.write('\nAn error occurred while deleting your account.')
                            if ARG:
                                exit(1)
                            else:
                                sleep(0.5)
                                return 0

                    else:
                        wait = False

                try:
                    sms.delete_hosted_service(self.curr_user.username)
                    blob_service.delete_container(self.curr_user.username.lower())
                except not WindowsAzureMissingResourceError:
                    stderr.write('\nAn error occurred while deleting your account.')
                    if ARG:
                        exit(1)
                    else:
                        return 0

                #path = 'C:/Users/' + comp_user + '/Simulations/' + self.curr_user.username + '/' + self.curr_user.username + \
                #       '_simulations.txt'
                #if os.path.exists(path):
                #    os.remove(path)

                self.user_list.pop(self.curr_user.username)
                return 1;

            elif user_input == 'n':
                return 0
            else:
                stderr.write('')
        else:
            stderr.write('Account does not exist.')
            if ARG:
                exit(1)
            else:
                return 0
