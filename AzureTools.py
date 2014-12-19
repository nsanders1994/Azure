__author__ = 'Natalie'

import os
import zipfile
from getpass import getuser
from time    import localtime
import shutil

# The current user on the computer; used to access the right folder under C:/Users
comp_user = getuser()

def timestamp():
    """
    Creates a timestamp
    :return: stamp
    """

    # Simulation name and it's online ID (VM name) is written to the user's project file
    year = str(localtime()[0])[-2:].zfill(2)
    month = str(localtime()[1]).zfill(2)
    date = str(localtime()[2]).zfill(2)
    hour = str(localtime()[3]).zfill(2)
    minute = str(localtime()[4]).zfill(2)
    sec = str(localtime()[5]).zfill(2)

    stamp = month + '/' + date + '/' + year + ' ' + hour + ':' + minute + ':' + sec

    return stamp

def zip_files(user, inputs):
    """
    Zips all input files into one archive
    :param user:
    :param inputs:
    :return:
    """

    inputs_dir = os.path.dirname(inputs)           # ie C:/Users/SomeName
    inputs_folder_name = os.path.basename(inputs)  # ie InputFiles

    os.chdir("C:/Users/" + comp_user + "/Simulations/" + user)

    # Zip the input folder, if not already
    if not zipfile.is_zipfile(inputs):
        print "\nZipping file..."

        z = zipfile.ZipFile("Inputs.zip", "w", zipfile.ZIP_DEFLATED)
        z.write("AzureUserInfo.pickle")

        # If there is one input file...
        if os.path.isfile(inputs_folder_name):
            z.write(inputs, inputs_folder_name)
        # If there are multiple input files/folders in the given folder...
        else:
            for base, dirs, files in os.walk(inputs):
                for f in files:
                    fn = os.path.join(base, f)
                    z.write(fn, f)

    else:
        shutil.copyfile(inputs, "Inputs.zip")
        z = zipfile.ZipFile("Inputs.zip", "a", zipfile.ZIP_DEFLATED)
        z.write("AzureUserInfo.pickle")


    z.close()
    return "C:/Users/" + comp_user + "/Simulations/" + user + "/Inputs.zip"

def extract_files(file_name, username):
    """
    Unzips files from the provided path.
    :param file_name:
    :param username:
    :return:
    """

    output_path = os.path.normpath('C:/Users/' + comp_user + '/Simulations/' + username)
    os.chdir(output_path)

    z = zipfile.ZipFile(file_name + '.zip', 'r')
    z.extractall(file_name)
    z.close()
