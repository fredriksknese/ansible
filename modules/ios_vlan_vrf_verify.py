#!/usr/bin/python3

from dataclasses import dataclass
from json import dump
from os import EX_CANTCREAT, readlink
from io import open
from ansible.module_utils.basic import *
from ansible.module_utils.network.ios.ios import run_commands
from ansible.module_utils.basic import AnsibleModule
from hashlib import md5

from re import search as re_search

def GetOrSetCmdFact(module:AnsibleModule,cache:dict,command,force=False):
  key=md5(command.encode('utf-8')).hexdigest()
  if not key in cache or force:
    cache[key] = run_commands(module, [command])[0].split('\n')
  return cache[key]

def GetInterfaces(module,cache):
    interfaces=[]
    cmd = GetOrSetCmdFact(module,cache,"sh run | section interface")
    i=dict()
    for line in cmd:
        if i:
            if i not in interfaces:
                interfaces.append(i)

            r=re_search('description (.*)',line)
            if r:
                i["description"]=r.groups()[0]

            r=re_search(' ip address (.*)',line)
            if r:
                i["ip"]=r.groups()[0]
            
            r=re_search(' vrf forwarding (.*)',line)
            if r:
                i["vrf"]=r.groups()[0]
            
            r=re_search(' name (.*)',line)
            if r:
                i["name"]=r.groups()[0]
            
            r=re_search(' encapsulation dot1Q (\d*)',line)
            if r:
                i["dot1q"]=r.groups()[0]
            
            r=re_search(' switchport trunk allowed vlan (.*)',line)
            if r:
                i["trunk_allowed"]=r.groups()[0]

        sub_r = re_search('interface (.*)\.(\d+)',line)
        if sub_r:
            i=dict()
            i["phys"] = sub_r.groups()[0]
            i["name"] = sub_r.groups()[0] + "." + sub_r.groups()[1]
            i["type"] = "sub"

        vlan_r = re_search('interface Vlan(\d+)',line)
        if vlan_r:
            i=dict()
            i["dot1q"] = int(vlan_r.groups()[0])
            i["name"] = "Vlan" + vlan_r.groups()[0]
            i["type"] = "vlan"
    return interfaces

def GetNumbers(str):
    splits=str.split(",")
    vlist=[]
    for vlan_mark in splits:
        if "-" in vlan_mark:
            vs=vlan_mark.split('-')
            for id in range(int(vs[0]),int(vs[1])):
                vlist.append(id)
        else:
            vlist.append(vlan_mark)
    return vlist
def GetTrunks(module,cache,interfaces):
    output=GetOrSetCmdFact(module,cache,"show interfaces switchport")
    trunks=[]
    i=None
    for line in output:
        name = re_search('Name: (.*)',line)
        if name:
            i=dict()
            i["name"]= name.groups()[0]
        is_trunk = re_search('Administrative Mode: trunk',line)
        if is_trunk:
            trunks.append(i)
        trunk_vlans = re_search("Trunking VLANs Enabled: (.*)",line)
        if trunk_vlans:
            vlan_ids = GetNumbers(trunk_vlans.groups()[0])
            for id in vlan_ids:
                interface = 


def main():
    result=dict(changed=False,ansible_facts=dict())
    cache=dict()
    fields = dict(
        vlan_vrf  = dict(required=True, type="dict"),
        when_vrf  = dict(required=False, type="str"),
    )
    module = AnsibleModule(argument_spec=fields)
    result["subinterfaces"]=GetInterfaces(module,cache)
    result["trunks"] = GetTrunks(module,cache)
    module.exit_json(**result)

if __name__ == '__main__':

    main()
