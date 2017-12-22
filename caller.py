#!/usr/bin/env python

# __autor__ = MatiasSp

import base64
from lib.ansclient import AnsApiClient

class Enum(object):
    ansible_connection = ('ssh', 'local')
    ansible_user = 'some_user'
    ansible_ssh_pass = base64.b64decode('some_encoded_password')
    hosts = '/some_path/inventory'
    subset = 'some subset'
    target = 'some target host'
    become = None

def main():
    ans = {'ansible_cnx' : {'ansible_connection': Enum.ansible_connection[0]}}

    inv = {'inventory' : {'hosts': Enum.hosts,
                          'subset': Enum.subset}
                          }
    # Execution line
    module = ('command', 'shell', 'raw')
    pargs = 'uname -a'

    # Intance Base class
    s = AnsApiClient(ans['ansible_cnx'], inv['inventory'], pargs, target=Enum.target, module=module[0])

    # Make the call embebed playbook
    resp = s.run_play(Enum.become, type='embebed', playbook='command.yml')

    # Make the call with a playbook yml file
    #resp = s.run_play(Enum.become, type='playbook', playbook='command.yml')

    print resp

if(__name__ == "__main__"):
    main()

