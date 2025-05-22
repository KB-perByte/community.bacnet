#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: bacnet_object_list
short_description: Get list of objects from BACnet device
description:
    - Retrieves the complete object list from a BACnet device
version_added: "1.0.0"
options:
    ip:
        description: Local IP address to bind to
        type: str
        required: false
    port:
        description: Local port to bind to
        type: int
        default: 47808
    device_id:
        description: Target device ID
        type: int
        required: true
    address:
        description: Target device address
        type: str
        required: false
'''

EXAMPLES = '''
- name: Get object list from device
  community.bacnet.bacnet_object_list:
    device_id: 12345
    address: "192.168.1.100"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.bacnet.plugins.module_utils.bacnet_utils import (
    BACnetConnection, validate_bacnet_address
)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(type='str', required=False),
            port=dict(type='int', default=47808),
            device_id=dict(type='int', required=True),
            address=dict(type='str', required=False)
        ),
        supports_check_mode=True
    )

    if module.params['address'] and not validate_bacnet_address(module.params['address']):
        module.fail_json(msg="Invalid BACnet address format")

    bacnet_conn = BACnetConnection(module)

    try:
        bacnet_conn.connect(ip=module.params['ip'], port=module.params['port'])
        objects = bacnet_conn.get_object_list(
            module.params['device_id'],
            module.params['address']
        )

        module.exit_json(
            changed=False,
            objects=objects,
            object_count=len(objects)
        )

    finally:
        bacnet_conn.disconnect()

if __name__ == '__main__':
    main()

---
# File: plugins/modules/bacnet_who_is.py
#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: bacnet_who_is
short_description: Send BACnet Who-Is request
description:
    - Sends a BACnet Who-Is request to discover devices
    - Can target specific device ID ranges or broadcast to all
version_added: "1.0.0"
options:
    ip:
        description: Local IP address to bind to
        type: str
        required: false
    port:
        description: Local port to bind to
        type: int
        default: 47808
    low_limit:
        description: Lower device ID limit for Who-Is request
        type: int
        required: false
    high_limit:
        description: Upper device ID limit for Who-Is request
        type: int
        required: false
    timeout:
        description: Timeout for responses in seconds
        type: int
        default: 30
'''

EXAMPLES = '''
- name: Broadcast Who-Is to all devices
  community.bacnet.bacnet_who_is:

- name: Who-Is for specific device range
  community.bacnet.bacnet_who_is:
    low_limit: 1000
    high_limit: 2000
    timeout: 15
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.bacnet.plugins.module_utils.bacnet_utils import BACnetConnection

def main():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(type='str', required=False),
            port=dict(type='int', default=47808),
            low_limit=dict(type='int', required=False),
            high_limit=dict(type='int', required=False),
            timeout=dict(type='int', default=30)
        ),
        supports_check_mode=True
    )

    bacnet_conn = BACnetConnection(module)

    try:
        bacnet_conn.connect(ip=module.params['ip'], port=module.params['port'])

        # Send Who-Is request
        try:
            if module.params['low_limit'] is not None and module.params['high_limit'] is not None:
                devices = bacnet_conn.bacnet.whois(
                    lowLimit=module.params['low_limit'],
                    highLimit=module.params['high_limit'],
                    timeout=module.params['timeout']
                )
            else:
                devices = bacnet_conn.bacnet.whois(timeout=module.params['timeout'])

            device_list = []
            for device in devices:
                device_list.append({
                    'device_id': device.deviceInstanceNumber,
                    'address': str(device.address),
                    'name': getattr(device, 'deviceName', 'Unknown'),
                    'vendor': getattr(device, 'vendorName', 'Unknown')
                })

            module.exit_json(
                changed=False,
                devices=device_list,
                device_count=len(device_list)
            )

        except Exception as e:
            module.fail_json(msg=f"Who-Is request failed: {str(e)}")

    finally:
        bacnet_conn.disconnect()

if __name__ == '__main__':
    main()
