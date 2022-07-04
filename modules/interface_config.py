#!/usr/bin/python3

#from ansible.module_utils.basic import *
from ansible.module_utils.network.ios.ios import run_commands
from ansible.module_utils.network.ios.ios import get_connection
from ansible.module_utils.basic import AnsibleModule

from re import search as re_search

debug=[]

def GetMissingLinesInSection(module,config,section,lines):
  lines_copy=list(lines)
  inSection = False
  for config_line in config:
    if config_line == section:
      inSection = True
      continue
    elif config_line.startswith(' ') and inSection:
      inSection = True
      
      #raise Exception(config_line)
      if config_line.strip() in lines_copy:
        lines_copy.remove(config_line.strip())
    else:
      inSection=False
  return lines_copy

def	GetInterfacesWithStatus(module,status_list):
  cmd_vlan_groups=run_commands(module, [f"show interfaces status "])[0].split('\n')
  interface_list=[]
  for line in cmd_vlan_groups:
    port,status = line[0:10].strip(),line[42:53].strip()
    if status in [str(x) for x in status_list ]:
      port = port.replace('Fa','FastEthernet')
      port = port.replace('Gi','GigabitEthernet')
      port = port.replace('Te','TenGigabitEthernet')
      interface_list.append(port)
  return interface_list

def GetVlanIds(module):
  vlan_list=[]
  global debug
  if module.params['vlans']:
    cmd_vlans = run_commands(module, [f"show vlan brief"])[0].split('\n')[2:]
    for line in cmd_vlans:
      id,name= int(line[0:4].strip()),line[5:33].strip()
      for vlan in module.params['vlans']:
        if type(vlan) is str and vlan == name:
          vlan_list.append(id)
        if type(vlan) is int and vlan == id:
          vlan_list.append(id)
    
    cmd_vlan_groups=run_commands(module, [f"show vlan group"])[0].split('\n')
    for line in cmd_vlan_groups:
      reg = re_search('vlan group (\w+) : (.*)',line)
      if reg:
        if reg.groups()[0] in module.params['vlans']:
          vlan_ids = reg.groups()[1].split(',')
          for id in vlan_ids:
            vlan_list.append(int(id))

  vlan_list=list(dict.fromkeys(vlan_list)) # remove duplicated vlan ids
  return vlan_list

def main():
  fields = dict(
    lines  = dict(required=True, type="list"),
    vlans  = dict(required=False, type="list"),
    #names  = dict(required=False, type="list"),
    trunk  = dict(required=False, type="bool"),
    monitoring  = dict(required=False, type="bool"),
    replace  = dict(required=False, choice=['line','block'],default="line"),
    running_config  = dict(required=False, type="str"),
    default_interface= dict(required=False, type="bool")
  )
  module = AnsibleModule(argument_spec=fields)

  status_list = GetVlanIds(module)
  if module.params['monitoring']:
    status_list.append('monitoring')
  if module.params['trunk']:
    status_list.append('trunk')

  interfaces = GetInterfacesWithStatus(module,status_list)
  
  cmd_list=[]
  if module.params['running_config']:
    config = module.params['running_config'].split('\n')
  else:
    config = run_commands(module,['show running-config'])[0].split('\n')
  for interface in interfaces:
    section=f"interface {interface}"
    missing_lines=GetMissingLinesInSection(module,config,section, module.params['lines'])
    if missing_lines:
      if module.params['default_interface']:
        cmd_list.append(f"default {section}")

      cmd_list.append(section)
      if module.params['replace']=="block":
        cmd_list.extend(module.params['lines'])	
      if module.params['replace']=="line":
        cmd_list.extend(missing_lines)
      cmd_list.append("exit")

  if cmd_list:
    conn = get_connection(module)
    result = conn.edit_config(cmd_list)
    module.exit_json(changed=True,params=module.params,cmd_list=result["request"],applied_vlan=status_list,debug=debug)
  else:
    module.exit_json(changed=False, params=module.params)

if __name__ == '__main__':
  main()