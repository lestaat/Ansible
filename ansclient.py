#!/usr/bin/env python

# __autor__ = MatiasSp

import json, os, sys
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
from ansible.playbook.play import Play
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible.plugins import callback

class Enum(object):

    base_conf = [{'ansible_cnx' : {'ansible_connection': 'ssh', 'ansible_user': 'some_user', 'ansible_ssh_pass': 'some_passwd'}},
                 {'inventory' : {'hosts': 'some_inventory', 'subset': 'some_subset'}},
                 {'pargs' : 'some_module_arg'},
                 {'target' : 'some_endpoint'},
                 {'module' : 'some_module'}, # either command | shell | raw are allowed so far
                 {'embebed' : 'embebed'},
                 {'playbook' : 'playbook'}
                ]


# Custom callback
class ResultCallback(CallbackBase):

    def __init__(self):
        super(ResultCallback, self).__init__()
        self.results = []

    def v2_runner_on_ok(self, result, **kwargs):

        self.results.append(result._result['stdout_lines'])

class AnsApiClient(object):

    def __init__(self, ansible_cnx=None, inventory=None, pargs=None, target=None, module=None):

        if ansible_cnx:
            self.ansible_cnx = ansible_cnx
        else:
            self.ansible_cnx = Enum.base_conf[0]['ansible_cnx']

        if inventory:
            self.inventory = inventory
        else:
            self.inventory = Enum.base_conf[1]['inventory']

        if pargs:
            self.pargs = pargs
        else:
            self.pargs = Enum.base_conf[2]['pargs']

        if target:
            self.target = target
        else:
            self.target =  Enum.base_conf[3]['target']

        if module:
            self.module = module
        else:
            self.module =  Enum.base_conf[4]['module']


    def run_play(self, become, type=None, playbook=None):

        ret = None

        Options = namedtuple('Options', ['connection', 'module_path', 'forks', 'become', 'become_method',
                                         'become_user', 'check', 'listtags', 'listtasks', 'listhosts', 'syntax',])

        if become is True:
            options = Options(connection=self.ansible_cnx['ansible_connection'], module_path='mymodules', forks=100, become=True, become_method='sudo', become_user='root', check=False, listtags=False, listtasks=False, listhosts=False, syntax=False)
        else:
            options = Options(connection=self.ansible_cnx['ansible_connection'], module_path='mymodules', forks=100, become=None, become_method=None, become_user=None, check=False, listtags=False, listtasks=False, listhosts=False, syntax=False)

        passwords = {}

        def run_embebed_playb(self, options, passwords):

            # initialize needed objects
            variable_manager = VariableManager()
            loader = DataLoader()

            # Instantiate our ResultCallback for handling results as they come in
            results_callback = ResultCallback()

            # create inventory and pass to var manager
            inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=self.inventory['hosts'])
            inventory.subset(self.inventory['subset'])

            variable_manager.set_inventory(inventory)
            variable_manager.extra_vars = {'ansible_connection': self.ansible_cnx['ansible_connection']}

            # create play with tasks
            play_source =  dict(
                   name = "RUN PLAY",
                   hosts = self.target,
                   #remote_user = self.ansible_cnx['ansible_user'],
                   gather_facts = 'false',
                   tasks = [
                        dict(action=dict(module=self.module, args=self.pargs), register='module_out'),
                   ]
                )

            play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

            # actually run it
            tqm = None
            try:
                tqm = TaskQueueManager(
                          inventory=inventory,
                          variable_manager=variable_manager,
                          loader=loader,
                          options=options,
                          passwords=passwords,
                          stdout_callback=results_callback,  # custom callback
                      )

                result = tqm.run(play)

            finally:
                if tqm is not None:
                    tqm.cleanup()

            return results_callback.results


        def run_yml_playb(self, options, passwords, playbook=None):

            # initialize needed objects
            variable_manager = VariableManager()
            loader = DataLoader()

            # Instantiate our ResultCallback for handling results as they come in
            results_callback = ResultCallback()

            # create inventory and pass to var manager
            inventory = Inventory(loader=loader, variable_manager=variable_manager, host_list=self.inventory['hosts'])
            inventory.subset(self.inventory['subset'])

            variable_manager.set_inventory(inventory)

            # Currently support target = servers, cmd = commands, dir = args: dir
            variable_manager.extra_vars = {'target': self.target, 'cmd': self.pargs, 'dir': '/bin'}

            # Playbook
            if playbook is None:
                playbook_path = 'playbooks/commands.yml'
            else:
                playbook_path = 'playbooks/' + playbook

            if not os.path.exists(playbook_path):
                print '[INFO] The playbook does not exist'
                sys.exit()

            pexec = PlaybookExecutor(playbooks=[playbook_path], inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=passwords)

            results = pexec.run()

        if type is Enum.base_conf[5]['embebed'] or None:
            ret = run_embebed_playb(self, options, passwords)
        elif type is Enum.base_conf[6]['playbook']:
            ret = run_yml_playb(self, options, passwords, playbook)

        return ret

class ResponseContainer(object):
    def __init__(self, result):
        self.result = result

    def __str__(self):
        return "%s" % (self.result)

