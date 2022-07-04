#!/usr/bin/python3

from ansible.module_utils.common.text.converters import container_to_bytes

from selinux import context_range_get
from ansible.module_utils.network.ios.ios import run_commands
from ansible.module_utils.network.ios.ios import get_connection
from ansible.module_utils.basic import AnsibleModule
from dataclasses import dataclass
from io import open
from re import search as re_search
from hashlib import md5

@dataclass
class IOSFile:
    IsDir:bool
    Name:str
    Size:int

def GetOrSetCmdFact(module:AnsibleModule,cache:dict,command,force=False):
  key=md5(command.encode('utf-8')).hexdigest()
  if not key in cache or force:
    cache[key] = run_commands(module, [command])[0].split('\n')
  return cache[key]

def GetFiles(module,cache):
  output = GetOrSetCmdFact(module,cache,"show flash:")
  files = []
  for line in output:
    re = re_search("^\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+\s\S+\s\S+\s\S+\s\S+)\s\s(.*)$",line)
    if re:
      dir="d" in str(re.group(2))
      name=str(re.group(5))
      size=int(str(re.group(3)))
      files.append({'IsDir':dir,'Name': name,'Size': size})
  return files

def SanitizeName(module,name:str):
  if module.params['allow_name_cleanup']:
    name = name.replace('flash:/','')
    name = name.replace('flash:','')
  return name


debug=[]
def main():
  fields = dict(
    delete = dict(required=False, type="list"),
    allow_name_cleanup = dict(required=False, type="bool"),
    ignore = dict(required=False, type="list"),
  )
  module = AnsibleModule(argument_spec=fields)

  cache=dict()
  
  files = GetFiles(module,cache)

  deletes=[]
  ignores=[]
  for f in files:
    allowDelete=True
    if module.params['ignore']:
      for i in module.params['ignore']:
        param=SanitizeName(module,i)
        re = re_search(param,f['Name'])
        if re:
          ignores.append(f['Name'])
          allowDelete=False

    if module.params['delete'] and allowDelete:
      for d in module.params['delete']:
        param=SanitizeName(module,d)
        re = re_search(param,f['Name'])
        if re:
          deletes.append(f['Name'])
          GetOrSetCmdFact(module,cache,f"delete /recursive /force flash:{f['Name']}")
    
  module.exit_json(changed=False,debug=debug,deletes=deletes,files=files,ignores=ignores)

if __name__ == '__main__':
  main()