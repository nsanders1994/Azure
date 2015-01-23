__author__ = 'Natalie Sanders'

from azure.servicemanagement import *
from azure.storage import *
from subprocess import call
from os import chdir
import os
import socket
import zipfile
import pickle
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

global user_info

def send_mail( send_from, send_to, subject, text, files=[], server="localhost", port=587, username='', password='', isTls=True):
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = send_to
    msg['Date'] = formatdate(localtime = True)
    msg['Subject'] = subject

    msg.attach( MIMEText(text) )

    for f in files:
        part = MIMEBase('application', "octet-stream")
        part.set_payload( open(f,"rb").read() )
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="{0}"'.format(os.path.basename(f)))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if isTls: smtp.starttls()
    smtp.login(username,password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()

    print "emailed\n"

def upload_results():
    z = zipfile.ZipFile(user_info["sim"]+'_Results.zip', "w", zipfile.ZIP_DEFLATED)

    for f in os.listdir("Input"):
        chdir("c:/Users/Public/Sim/Input")
        z.write(f)
    chdir("c:/Users/Public/Sim/Output")
    z.write("stdout.txt")
    z.close()

    result = 'r-' + machine_name
    blob_service.put_block_blob_from_path(container_name, result, 'c:/Users/Public/Sim/Output.zip')

    print "uploaded\n"

def download_input():
    blob_service.get_blob_to_path(container_name, machine_name, 'c:/Users/Public/Sim/Input.zip')

    chdir("C:/Users/Public/Sim")
    z = zipfile.ZipFile('Input.zip', 'r')
    z.extractall('Input')
    z.close()

    print "downloaded\n"


########################################################################################################################
##                                                        MAIN                                                        ##
########################################################################################################################

##### Service Management Object #####
machine_name = socket.gethostname()
split = machine_name.split('-')
container_name = '-'.join(split[:-1]).lower()
username = '-'.join(split[:-1])

subscription_id = 'a9401417-cb08-4e67-bc2a-613f49b46f8a'
certificate_path = 'CURRENT_USER\\my\\AzureCertificate'

call(['certutil', '-user', '-f', '-p', '1', '-importPFX', 'c:/temp/azure.pfx'])
sms = ServiceManagementService(subscription_id, certificate_path)

###### Redirect stdout to File ######
chdir('C:/Users/Public/Sim')
output = open("Output/stdout.txt", "w+")

####### Download Input Files ########
blob_service = BlobService(
        account_name='portalvhdsd3d1018q65tg3',
        account_key='cAT5jbypcHrN7sbW/CHgGFDGSvOpyhw6VE/yHubS799egkHfvPeeXuK7uzc6H2C8ZU1ALiyOFEZkjzWuSyfc+A==')

#try:
download_input()
f = "C:/Users/Public/Sim/Input/AzureUserInfo.pickle"
user_info = pickle.load(file(f))

output.write('Mock model executed correctly.')
output.close()
print "download input"
#except:
#    output.write('Could not download input from the cloud.\n')
#    output.close()

try:
    ########### Upload Results ##########
    upload_results()

    ########### Email Results ###########
    send_mail( send_from   = 'vecnet.results@gmail.com',
               send_to     = user_info["email"],
               subject     = 'The results for your ' + user_info["sim"] + ' simulation are ready!',
               text        = 'Hi ' + user_info['username'] + ',\n\nYour ' + user_info["sim"] + ' simulation has '
                             'finished running. Look for your results below.\n\nThanks for using VecNet Azure '
                             'resources!\nThe VecNet Team',
               files       = ['c:/Users/Public/Sim/' + user_info["sim"] + '_Results.zip'],
               server      = "smtp.gmail.com",
               port        = 587,
               username    = 'vecnet.results',
               password    = 'Lgfak_1994',
               isTls       = True)
    print "sent mail"

############# Exit Script #############
finally:
    print "unable to send email"