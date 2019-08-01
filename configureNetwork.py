import argparse
import sys
import socket
import os
import subprocess
from pprint import pprint

user = os.getenv('SUDO_USER')
if (user is None):
    print('Root priviliges are needed')
    exit()

#Parse arguments
parser = argparse.ArgumentParser(description='Configures IP addresses and routing tables for proxy server instances')
parser.add_argument('-i', '--interface', help='Network interface name. Example: eth0', required=True)
parser.add_argument('-ipgw', '--ip-address-with-gateway', action='append', help='An IP address and its gateway in notation IP:GW/MASK. Can be specified multiple times to add more sets. Example: 10.0.0.2:10.0.0.1/30', required=True)
parser.add_argument('-fwStart', '--fwmark-start', type=int, default=500, help='The initial fwmark which will be incremented by 1 for each IP:GW set. Default: 500')
parser.add_argument('-tableStart', '--iptableid-start', type=int, default=500, help='The initial ip table ID which will be incremented by 1 for each IP:GW set. Default: 500')
parser.add_argument('-prioStart', '--ipruleprio-start', type=int, default=500, help='The initial ip rule priority which will be incremented by 1 for each IP:GW set. Default: 500')
args = parser.parse_args()

class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def parse_ip_set(ip_set):
    splitIps = ip_set.split(':')
    if(len(splitIps) != 2):
        raise Exception('Error while parsing ' + ip_set + ' - invalid set. You need to separate the ip and the gateway with :')
    splitGw = splitIps[1].split('/')
    if(len(splitGw) != 2):
        raise Exception('Error while parsing ' + ip_set + ' - invalid gateway notation. It must contain the mask in CIDR notation')
    mask = splitGw[1]
    ip = splitIps[0]
    gateway = splitGw[0]
    if (len(gateway.split('.')) != 4 or len(ip.split('.')) != 4):
        raise Exception('Error while parsing ' + ip_set + ' - invalid number of dots in the gateway or the ip')
    maskInt = int(mask)
    if (maskInt < 1 or maskInt > 32):
        raise Exception('Error while parsing ' + ip_set + ' - wrong mask. Min 1, max 32')
    try:
        socket.inet_aton(gateway)
        socket.inet_aton(ip)
    except:
        raise Exception('Error while parsing ' + ip_set + ' - ip or gateway are invalid')
    return Namespace(ip = ip, mask = mask, gateway = gateway)

#Check the arguments
parsed_ip_sets = list()
for ip_set in args.ip_address_with_gateway:
    try:
        parsed_ip_set = parse_ip_set(ip_set)
        parsed_ip_sets.append(parsed_ip_set)
    except Exception as e:
        print(e)
        exit()

commands_to_execute = list()
print(args)
for parsed_ip_set in parsed_ip_sets:
    ip_command = 'ip addr add {}/{} dev {}'.format(parsed_ip_set.ip, parsed_ip_set.mask, args.interface)
    ip_rule_command = 'ip rule add fwmark {} table {} prio {}'.format(args.fwmark_start, args.iptableid_start, args.ipruleprio_start)
    ip_route_command = 'ip route add default via {} table {}'.format(parsed_ip_set.gateway, args.iptableid_start)
    commands_to_execute.append(ip_command)
    commands_to_execute.append(ip_rule_command)
    commands_to_execute.append(ip_route_command)
    args.fwmark_start = args.fwmark_start + 1;
    args.iptableid_start = args.iptableid_start + 1;
    args.ipruleprio_start = args.ipruleprio_start + 1;
    print('\n{}\n{}\n{}'.format(ip_command, ip_rule_command, ip_route_command))

print('\nExecute the above commands (yes/no)? ')
yes = {'yes','y', 'ye', ''}
no = {'no','n'}
choice = False
while (choice not in yes and choice not in no):
    choice = input().lower()
    if (choice in no):
        print('ABORTING')
        exit()
    elif (choice not in yes):
        sys.stdout.write("Please respond with 'yes' or 'no' ")

for command_to_execute in commands_to_execute:
    subprocess.run(command_to_execute.split())
