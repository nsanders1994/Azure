#!/usr/bin/python

__author__ = 'Natalie Sanders'

import argparse
import AzureUserPool
import pickle
import os
from azure                   import *
from azure.servicemanagement import *
from azure.storage           import BlobService
from time                    import sleep
from sys                     import stderr
from AzureTools              import comp_user


def menu():
    """
    Beginning menu which prompts the user to sign in with a previous username, create
    an account, or quit the program.
    :return:
    """
    goto = 0

    user_input = raw_input(
        "\n########## LOGIN ##########\n"
        "(1) Sign in\n"
        "(2) New User\n"
        "(3) Quit\n"
        ">> ")

    if user_input == '1':
        # prompts client for username
        goto = users.sign_in()
    elif user_input == '2':
        # creates cloud service and storage container using client specified username
        goto = users.add_user()
        print goto
        pickle.dump(users.user_list, file(f, 'w'))
    elif user_input == '3':
        quit(0)
    else:
        print "\nCommand not recognized."
        goto = 1

    if goto is 1:
        menu()
    elif goto is 0:
        sub_menu(users.curr_user)


def sub_menu(user):
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
        if user.add_sim('EMOD') is 0:
            users.save_user()
            pickle.dump(users.user_list, file(f, 'w'))
        sub_menu(user)
    elif user_input == '2':
        # creates a VM under client's cloud service, running the Open Malaria simulation
        if user.add_sim('OM') is 0:
            users.save_user()
            pickle.dump(users.user_list, file(f, 'w'))
        sub_menu(user)
    elif user_input == '3':
        # returns the results of a previously run simulation specified by the client
        user.user_requestSimResults()
        sub_menu(user)
    elif user_input == '4':
        # deletes the user's account-- cloud service and storage container
        if users.delete_account() is 1:
            pickle.dump(users.user_list, file(f, 'w'))
            menu()
        else:
            sub_menu(user)
    elif user_input == '5':
        users.logout()
        menu()
    elif user_input == '6':
        quit(0)
    else:
        stderr.write("\nCommand not recognized.")
        sleep(0.5)
        sub_menu(user)


########################################################################################################################
##                                                        MAIN                                                        ##
########################################################################################################################

#### GLOBAL VARIABLES ####

# The user pool is imported
global users
global f

f = 'C:/Users/' + comp_user + '/Simulations/AzureUsers.pickle'
if os.path.exists(f):
    users = AzureUserPool.AzureUserPool()
    users.user_list = pickle.load(file(f))
else:
    users = AzureUserPool.AzureUserPool()


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

# Check for command line arguments
UI = True

if len(sys.argv) > 1:
    use_string = 'Setup_Sim.py [-h] [-new] username [ -d | [-ncln] -sE INPUT_FOLDER SIMULATION_NAME N_CORES| [-ncln] ' \
                 '-sOM INPUT_FOLDER SIMULATION_NAME N_CORES | [-ncln] -m INPUT_FOLDER SIMULATION_NAME | -r SIMULATION_NAME ]'
    parser = argparse.ArgumentParser(usage=use_string)

    parser.add_argument("-new", "--new_user", action="store_true",
                        help="New user; create an account")
    parser.add_argument("username", type=str,
                        help="Username for simulation account")
    parser.add_argument("-ncln", "--cleanup_off", action="store_true",
                        help="Turn off automatic cleanup of VM instances (VMs not deleted)")

    options_group = parser.add_mutually_exclusive_group()
    options_group.add_argument("-sOM", "--OpenMalaria", nargs=3, type=str, action="store",
                               help="Runs new Open Malaria simulation; must provide file path to input folder,"
                                    "a new simulation name, and the number of cores needed.")
    options_group.add_argument("-sE", "--EMOD", nargs=3, type=str, action="store",
                               help="Runs new EMOD simulation; must provide file path to input folder, a new "
                                    "simulation name, and the number of cores needed.")
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

    # Check for command line errors
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

    # Start specified tasks
    if args.new_user:
        users.add_user(args.username, True)
    elif args.delete:
        users.delete_account(True)
    else:
        users.sign_in(args.username, True)

    if args.cleanup_off:
        del_VM = False
    else:
        del_VM = True

    if args.EMOD:

        if users.curr_user.add_sim(args.EMOD[1], args.EMOD[0], "EMOD", True, del_VM) is 0:
            users.curr_user.save_sim()
            pickle.dump(users.user_list, file(f, 'w'))
    elif args.OpenMalaria:
        if users.curr_user.add_sim(args.OpenMalaria[1], args.OpenMalaria[0], "OM", True, del_VM) is 0:
            users.curr_user.save_sim()
            pickle.dump(users.user_list, file(f, 'w'))
    elif args.mock_model:
        if users.curr_user.add_sim(args.mock_model[1], args.mock_model[0], "mock", True, del_VM) is 0:
            users.curr_user.save_sim()
            pickle.dump(users.user_list, file(f, 'w'))
    elif args.get_results:
        users.curr_user.user_requestSimResults(True)

pickle.dump(users.user_list,file(f, 'w'))