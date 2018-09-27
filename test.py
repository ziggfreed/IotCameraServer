from netifaces import interfaces, ifaddresses, AF_INET6
from sys import platform
from subprocess import check_output 

def ip4_addresses():
    ip_list = []
    for interface in interfaces():
        for link in ifaddresses(interface)[AF_INET6]:
            ip_list.append(link['addr'])
    return ip_list

print(ip4_addresses())