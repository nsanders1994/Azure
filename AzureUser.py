__author__ = 'Natalie'


import os
import AzureTools
import AzureSimulation
from re              import search
from time            import sleep
from sys             import stderr
from AzureTools      import comp_user
from AzureSimulation import sms, blob_service
from copy            import copy


class AzureUser:
    def __init__(self):
        self.simulations = {}
        self.username = ""
        self.curr_sim = AzureSimulation.AzureSimulation()
        self.email = ""
        self.user_info = {}

    def add_sim(self, proj_name="", user_input="", sim_type="mock", ARG=False, DEL=False):
        """
        Adds simulation to the user's list of projects. Calls setup_sim and curr_sim.simulation to configure the new
        project and actually deploy the simulation
        :param sim_type:
        :param proj_name:
        :param user_input:
        :param ARG:
        :param DEL:
        :return:
        """

        ###### Create Unique VM ID ######
        self.curr_sim.generate_vm_id(self.username)

        ##### If accessed through command-line #####
        if ARG:
            self.curr_sim.name   = proj_name
            self.curr_sim.input  = user_input
            self.curr_sim.cores  = 1
            self.curr_sim.tstamp = AzureTools.timestamp()

            print proj_name

            ## Check Project Name is Unique and Valid ###
            valid = self.curr_sim.check_name(proj_name)
            unique = self.check_sim(proj_name)

            ##### Update Simulation File ######
            # The Simulation name has invalid syntax...
            if not valid:
                stderr.write("\nSimulation name has invalid syntax.")
                exit(1)
            elif not unique:
                stderr.write("Simulation name already exists.")
                exit(1)
            else:
                self.user_info["username"] = self.username
                self.user_info["email"]    = self.email
                self.user_info["sim"]      = self.curr_sim.name

                self.curr_sim.upload_input(self.user_info)
                success = self.curr_sim.simulation(self.username, sim_type, ARG, DEL)
                return success
        else:
            # Get user input for simulation name and check if name is unique
            if self.user_giveSimName() is 1:
                return 1

            # Get user input for input files
            if self.user_giveSimInput() is 1:
                return 1

            # Get user input for core count
            self.user_giveSimCores()

            # Generate timestamp
            self.curr_sim.tstamp = AzureTools.timestamp()

            # Run simulation
            success = self.curr_sim.simulation(self.username, sim_type)
            return success

    def save_curr_sim(self):
        """
        Saves the simulation in the user's list of projects
        :return:
        """

        # Add new, configured simulation to the user's simulation list
        key = copy(self.curr_sim.name)
        val = copy(self.curr_sim)

        self.simulations[key] = val

    def user_giveSimCores(self):
        """
        User assigns a number of cores to the simulation VM
        :return:
        """

        user_input = int(raw_input("\nHow many cores? (Options: 1, 2, 4, 8, 16): "))

        while user_input not in (1, 2, 4, 8, 16):
            print('Not a valid core size.\n')
            user_input = int(raw_input("\nHow many cores? (Options: 1, 2, 4, 8, 16): "))

        self.cores = user_input

    def user_giveSimName(self):
        """
        User gives the new simulation a name; checks validity and uniqueness respectively with calls to
        curr_sim.check_name and check_sim
        :return:
        """

        ######## Choose Simulation Name ########
        sim_name = "1"
        while sim_name == '1':
            sim_name = raw_input("\nRestrictions: Cannot contain spaces or the following reserved characters \ / < "
                                     "> : \" | ? * \nPress 1 to list existing simulations or enter a name for your new "
                                     "simulation: ")
            if sim_name == '1':
                self.list_projects()

        # Check that project name doesn't exist and has valid syntax
        valid = self.curr_sim.check_name(sim_name)
        unique = self.check_sim(sim_name)

        # The Simulation name is not valid or unique...
        while not unique or not valid:
            # The Simulation name has invalid syntax...
            if not valid:
                stderr.write("\nSimulation name has invalid syntax.")
                sleep(0.5)
            # The Simulation name already exists...
            elif not unique:
                stderr.write("\nSimulation name already exists.")
                sleep(0.5)

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
                sim_name = "1"
                while sim_name == "1":
                    sim_name = raw_input("\nRestrictions: Cannot contain spaces or the following reserved "
                                                   "characters \ / < > : \" | ? * \nPress 1 to list existing "
                                                   "simulations or enter a name for your new simulation: ")
                    if sim_name == "1":
                        self.list_projects()
                        print sim_name

                # Check that project name doesn't exist and has valid syntax
                valid = self.curr_sim.check_name(sim_name)
                unique = self.check_sim(sim_name)

            elif option == '2':
                return 1
            elif option == '3':
                quit(0)

        # Once valid, update current simulation's name
        self.curr_sim.name = sim_name

    def user_giveSimInput(self):

        """
        Asks the user for the path to their input necessary to run the simulation. Calls curr_sim.upload_input to
        upload the input files.
        :return:
        """

        i = raw_input("\nEnter path to your input folder/file: ")

        # Convert path to Windows format
        norm_inputs = os.path.normpath(i)  # C:/Users/SomeName/InputFiles

        # Check that path exists
        while not os.path.exists(i):
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
                i = raw_input("\nEnter path to your input folder/file: ")
            elif option == "2":
                return 1
            elif option == "3":
                quit(0)

        # Once valid, update current simulation's input files
        self.curr_sim.input = i
        # Upload files
        self.user_info["username"] = self.username
        self.user_info["email"]    = self.email
        self.user_info["sim"]      = self.curr_sim.name
        self.curr_sim.upload_input(self.user_info)

    def user_requestSimResults(self, ARG=False):
        """
        Checks if the specified simulation is done running and if its results file has been uploaded
        to the client's storage container. If the simulation has finished, the results are downloaded
        to the clients computer.
        :param ARG:
        :return:
        """

        if ARG:
            print "Checking for " + self.curr_sim.name + " results..."
            # Check if project is listed in client's simulation file
            not_listed = self.check_sim(self.curr_sim.name)

            ######## Get Results if Ready ########
            if not_listed:
                stderr.write("\nProject does not exist.")
                exit(1)
            else:
                # Retrieve names of all user's files in their container
                try:
                    blobs = blob_service.list_blobs(container_name=self.username.lower())
                except:
                    stderr.write('An error occurred while accessing your storage.')
                    exit(1)

                sim_results = 'r-' + self.curr_sim.vm_id
                results_in = False

                # Check if results are in
                for uploaded_file in blobs:
                    if uploaded_file.name == sim_results:
                        # Download results file
                        file_path = 'c:/Users/' + comp_user + '/Simulations/' + self.username + '/' + self.curr_sim.name + \
                                    '_results.zip'
                        try:
                            blob_service.get_blob_to_path(self.username.lower(), sim_results, file_path)
                        except:
                            stderr.write('An error occurred while downloading your results.')
                            exit(1)

                        AzureSimulation.extract_files(self.curr_sim.name + '_results')
                        results_in = True
                        break

                if results_in:
                    print "\nYour results are in! Check C:/Users/" + comp_user + "/Simulations/" + self.username + " for " \
                          "the " + self.curr_sim.name + "_results folder."
                else:
                    # If the results are not in and the VM is still running...
                    try:
                        sms.get_role(self.username, self.username, self.curr_sim.vm_id)
                        # The simulation is still running
                        print "\nThe simulation is still running. Check back later to retrieve results."

                    # If the results are not in but the VM is already deleted...
                    except:
                        # The results did not upload
                        print "Your results were unable to be uploaded. Try running the simulation again."

        elif not ARG:

            ######## Get Simulation Name #########
            requested_sim = "1"
            while requested_sim == '1':
                requested_sim = raw_input("\nSelect a project to check for results.\n"
                                          "Press '1' to list projects or enter project name: ")
                if requested_sim == '1':
                    self.list_projects()

            ######## Get Results if Ready ########
            while self.check_sim(requested_sim) == True:
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
                if option == 1:
                    requested_sim = "1"
                    while requested_sim == '1':
                        requested_sim = raw_input("\nSelect a project to check for results.\n"
                                                  "Press '1' to list projects or enter project name: ")
                        if requested_sim == '1':
                            self.list_projects()
                elif option == '2':
                    return
                elif option == '3':
                    quit(0)

            # Retrieve all user's files from their container
            try:
                blobs = blob_service.list_blobs(container_name=self.username.lower())
            except:
                stderr.write('An error occurred while trying to access your storage.')
                exit(1)

            sim_results = 'r-' + self.curr_sim.vm_id
            results_in = False

            # Check if results are in
            for uploaded_file in blobs:
                if uploaded_file.name == sim_results:
                    # Download results file
                    file_path = 'c:/Users/' + comp_user + '/Simulations/' + self.username + '/' + requested_sim + \
                                '_results.zip'
                    try:
                        blob_service.get_blob_to_path(self.username.lower(), sim_results, file_path)
                    except:
                        stderr.write('An error occurred when trying to download your results.')
                        exit(1)

                    # Extract results
                    AzureTools.extract_files(requested_sim + '_results', self.username)
                    results_in = True

                    break

            if results_in:
                print "\nYour results are in! Check C:/Users/" + comp_user + "/Simulations/" + self.username + " for " \
                      "the " + requested_sim + "_results folder."
                return
            else:
                # If the results are not in and the VM is still running...
                try:
                    sms.get_role(self.username, self.username, self.curr_sim.vm_id)
                    # The simulation is still running
                    print "\nThe simulation is still running. Check back later to retrieve results."

                # If the results are not in but the VM is already deleted...
                except:
                    # The results did not upload
                    print "Your results were unable to be uploaded. Try running the simulation again."

                return

    def check_username(self):

        """
        Checks that the syntax in the client chosen username is valid. If the username is valid, a cloud service will
        be created for the client and a boolean 'True' will be returned
        :return: is_valid
        """

        is_valid = True

        # Check username for invalid characters
        if not search('^[a-zA-Z0-9-]+$', self.username):
            is_valid = False
            stderr.write('\nUsername can only contain numbers, letters, and dashes.\n')

        # Check username length
        elif len(self.username) > 10 or len(self.username) < 3:
            is_valid = False
            stderr.write('\nUsername must be between 3 and 10 characters.\n')

        # Check username starting/ending characters
        elif not search('^[a-zA-Z].*\w$', self.username):
            is_valid = False
            stderr.write('\nUsername must start with a letter and end with a letter or a number.\n')

        # Check if username (cloud service) already exists in Azure
        elif not sms.check_hosted_service_name_availability(self.username).result:
            is_valid = False
            stderr.write('\nUsername is not available.\n')

        sleep(0.5)
        return is_valid

    def check_sim(self, sim_name):
        """
        Checks that the project name chosen by the user is unique within their account.
        :return: unique
        """

        unique = True

        # Check if the project name already exists under this account
        if sim_name in self.simulations.keys():
            unique = False

        return unique

    def remove_proj(self, del_proj):
        """
        Removes specified project from the user's simulation file
        :param del_proj:
        :return:
        """

        self.simulations.pop(del_proj)

    def list_projects(self):
        """
        Lists all the client's simulations and their time stamps.
        :return:
        """

        print '\n  ' + self.username + '\'s Projects:'
        for proj in self.simulations:
            print "    " + self.simulations[proj].tstamp + "  " + self.simulations[proj].name
