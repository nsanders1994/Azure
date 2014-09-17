__author__ = 'Natalie'

from time import sleep
from subprocess import call, PIPE, Popen

output = open('C:/Users/Natalie/Simulations/throughput_test.txt', 'a+')
call(['python', 'Setup_Sim.py', '-new', 'VecNet6', 'sim', '-s', 'C:/Users/Natalie/Solomons.zip'], stdout=output)

for vm_num in range(0, 29):
    call(['python', 'Setup_Sim.py', 'VecNet6', 'sim' + str(vm_num), '-s', 'C:/Users/Natalie/Solomons.zip'], stdout=output)
    sleep(30)
    vm_num += 1

vm_list = []
for num in range(0, 29):
    vm_list.append(num)

while 1:
    if len(vm_list) > 0:
        for num in vm_list:
            call(['python', 'Setup_Sim.py', 'VecNet5', 'sim' + str(num), '-r'], stdout=output)

            if "Your results are in!" in output:
                vm_list.remove(num)

    else:
        break

output.close()