#!/usr/bin/python
# Copyright (c) Atos Global Delivery Center
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '0.1',
                    'status': ['preview']}


DOCUMENTATION = '''
---
module: os_rbac
short_description: Manage OpenStack Network RBAC policies
version_added: "0.1"
author: "Piotr Kochanowski piotr.kochanowski@atos.net"
description:
    - Manage OpenStack Network RBAC. RBACs can be created  or deleted using this module.
options:
   object_id:
     description:
        - ID of the object that this RBAC policy affects.
     required: true
   target_project_id:
     description:
        - ID of the project to which this RBAC will be enforced.
     required: true
   object_type:
     description:
        - Type of the object that this RBAC policy affects.
     choices: [qos_policy, network]
     default: network
   action:
     description:
        - Action for the RBAC policy.
     choices: [access_as_external, access_as_shared]
     default: access_as_shared
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
requirements:
    - "python >= 2.7"
    - "openstacksdk"
'''

EXAMPLES = '''
# Create rbac policy
- os_rbac:
    cloud: mycloud
    endpoint_type: admin
    state: present
    object_id: 3e456c40-b262-4ae0-baba-c46461e7501b
    target_project_id: 1d162522f42e48dcbc6b0bf318b5b2e3
    action: access_as_external

# Delete rbac policy
- os_rbac:
    cloud: mycloud
    endpoint_type: admin
    state: absent
    action: acces_as_external
    object_id: 3e456c40-b262-4ae0-baba-c46461e7501b
    target_project_id: 1d162522f42e48dcbc6b0bf318b5b2e3

'''

RETURN = '''
rbac:
    description: Dictionary describing the policy.
    returned: On success when state is 'present'
    type: complex
    contains:
        object_id:
            description: ID of the object that this RBAC policy affects.
            type: str
            sample: 3e456c40-b262-4ae0-baba-c46461e7501b
        target_project_id:
            description: ID of the project to which this RBAC will be enforced.
            type: str
            sample: 1d162522f42e48dcbc6b0bf318b5b2e3 
        object_type:
            description: Type of the object that this RBAC policy affects.
            type: str
            sample: network
        action:
            description: Action for the RBAC policy.
            type: str
            sample: access_as_shared
	id:
            description: ID of the created/existing policy
	    type: str
	    example: 5635c465-5ba3-438f-b6db-3c3f9afcd91f
	project_id: 
	    description: ID of the owner project
	    type: str
	    example: dff12333df7d4a26bd9e9cfdcf489faa
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module

def main():
    argument_spec = openstack_full_argument_spec(
        object_id=dict(required=True),
        target_project_id=dict(required=True),
        object_type=dict(required=False, default='network', choices=['network','qos_policy']),
        action=dict(required=False, default='access_as_shared', choices=['access_as_shared','access_as_external']),
        state=dict(default='present', choices=['absent', 'present'])
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(
        argument_spec,
        **module_kwargs
    )

    object_id = module.params['object_id']
    target_project_id = module.params['target_project_id']
    object_type = module.params.get('object_type')
    action = module.params['action']
    state = module.params['state']
    query = dict(action = action, object_type = object_type, target_project_id = target_project_id)
    create_query = dict(object_id = object_id, target_project_id = target_project_id, object_type = object_type, action = action )

 
    sdk, cloud = openstack_cloud_from_module(module)
    try:
        project_rbacs = list(cloud.network.rbac_policies(**query))
        rbac_exists = False
        for item in project_rbacs:
            if item['target_project_id'] == target_project_id: # for some reason rbac_policies() does not filter by target_project_id that's why this if
                if item['object_id'] == object_id:
                    rbac_exists = True
                    rbac = item 
        if state == 'present':
            if rbac_exists is False:
                rbac = cloud.network.create_rbac_policy(**create_query)
                rbac = cloud.network.get_rbac_policy(rbac)
                changed = True
            else:
                changed = False
            module.exit_json(changed=changed, rbac=rbac)

        elif state == 'absent':
            if rbac_exists is False:
                changed = False
            else:
                cloud.network.delete_rbac_policy(rbac['id'])
                changed = True
            module.exit_json(changed=changed)

    except sdk.exceptions.OpenStackCloudException as e:
        module.fail_json(msg=e.message, extra_data=e.extra_data)

if __name__ == '__main__':
    main()
