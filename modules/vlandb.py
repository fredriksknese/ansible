#!/usr/bin/python3

from ansible.module_utils.basic import *
from ansible.module_utils.network.ios.ios import run_commands
from ansible.module_utils.basic import AnsibleModule
from re import search as re_search
from hashlib import md5

def GetFirstVlan(module:AnsibleModule,cache:dict,vlans):
    cmd_vlans = GetOrSetCmdFact(module,cache, "show vlan brief")
    cmd_vlan_groups = GetOrSetCmdFact(module,cache, "show vlan group")

    for vlan in vlans:
        for line in cmd_vlan_groups:
            reg = re_search('vlan group (\w+) : (.*)',line)
            if reg:
                if reg.groups()[0] == vlan:
                    vlan_ids = reg.groups()[1].split(',')
                    for id in vlan_ids:
                            return id
        for line in cmd_vlans[2:]:
            id , name= int(line[0:4].strip()),line[5:33].strip()
            if vlan == name or vlan == id:
                return id
    return None

def GetOrSetCmdFact(module:AnsibleModule,cache:dict,command,force=False):
  key=md5(command.encode('utf-8')).hexdigest()
  if not key in cache or force:
    cache[key] = run_commands(module, [command])[0].split('\n')
  return cache[key]

def HasVlans(module:AnsibleModule,cache:dict,vlans):
  for vlan in vlans:
    if not GetFirstVlan(module,cache,[vlan]):
      return False
  return True

def main():
    result=dict(changed=False,ansible_facts=dict())
    cache=dict()
    fields = dict(
#		lines  = dict(required=False, type="list"),
        firstMatchingVlanId  = dict(required=False, type="list"),
        assert_vlans  = dict(required=False, type="list"),
    )
    module = AnsibleModule(argument_spec=fields)

    if module.params['assert_vlans']:
        if not HasVlans(module,cache,module.params['assert_vlans']):
            module.fail_json(**result,msg="Does not have all vlans")

    if module.params['firstMatchingVlanId']:
        result['firstMatchingVlanId'] = GetFirstVlan(module,cache,module.params['firstMatchingVlanId'])

    module.exit_json(**result)

if __name__ == '__main__':

    main()
