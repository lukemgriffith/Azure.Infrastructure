#!/usr/bin/python
'''
    azure dynamic inventory for ansible.
'''
import os
import sys
import argparse
import json
import configparser
from pprint import PrettyPrinter
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient


class Azure_Machine:
    def __init__(self, name, location, tags, public_ip, private_ip):
        self.name = name
        self.location = location
        self.tags = tags
        self.public_ip = public_ip
        self.private_ip = private_ip

class Azure_Inventory():
    ''' Dynamic inventory class used to query Azure for virtual machines. '''
    def __init__(self):

        args = self.parse_args()

        ini_path = os.path.dirname(os.path.realpath(__file__)) + "/.azureSubscription"

        config = self.getConfiguration(ini_path)
        client_id = config.get("accountDetails", "client_id")
        secret = config.get("accountDetails", "secret")
        tenant = config.get("accountDetails", "tenant")
        subscription = config.get("accountDetails", "subscription")


        credentials = ServicePrincipalCredentials(client_id=client_id,
                                                       secret=secret,
                                                       tenant=tenant)

        self.computeManager = ComputeManagementClient(credentials=credentials,
                                                      subscription_id=subscription)

        self.networkManager = NetworkManagementClient(credentials=credentials,
                                                      subscription_id=subscription)

        

        inventory = list()

        self.get_machines(inventory)

        if args.print:
            self.prettyPrint(inventory)

        if args.list:
            self.output_inventory(inventory)


        

    def get_machines(self, inventory_list):

        machines = self.computeManager.virtual_machines.list_all()

        for m in machines:

            m_name = str()
            m_location = str()
            m_tags = list()
            m_public_ip = str()
            m_private_ip = str()

            m_name = m.name
            m_location = m.location
            m_tags = m.tags


            ### ID In this object, has the ID of the network interface.
            ### Use this to identify ip addresses.
            network = m.network_profile.network_interfaces

            # this is a horrible itteration. want to remove.
            for n in network:
                interfaces = self.networkManager.network_interfaces.list_all()
                ip_config = self.networkManager.public_ip_addresses.list_all()

                for inter in interfaces:
                    if inter.id == n.id:
                        for x in inter.ip_configurations:
                            m_private_ip = x.private_ip_address

                            for pip in ip_config:
                                if pip.id == x.public_ip_address.id:
                                    m_public_ip = pip.ip_address

            azure_host = AzureMachine(name=m_name, location=m_location,
                                      tags=m_tags, public_ip=m_public_ip,
                                      private_ip=m_private_ip)

            inventory_list.append(azure_host)

    def parse_args(self):

        parser = argparse.ArgumentParser(description="Azure dynamic inventory script.")
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--host', type=str, required=False)
        parser.add_argument('--ToggleBoundry', action='store_true',)
        parser.add_argument('--print', action='store_true')
        return parser.parse_args()



    def getConfiguration(self, ini_path):

        config = configparser.RawConfigParser(allow_no_value=False)
        file = open(ini_path)
        config.read_file(file)
        return config



    def prettyPrint(self, inventory):

        pp = PrettyPrinter(indent=2)

        for i in inventory:
            pp.pprint(i)


    def output_inventory(inventory):
        
        inv = { "hosts": [] }

        for i in inventory:
            
            inv["hosts"].append(i.public_ip)


        print(inv)

Azure_Inventory()
