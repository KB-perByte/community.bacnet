#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: bacnet_read_property
short_description: Read properties from BACnet objects
description:
    - Reads property values from BACnet objects
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
    object_type:
        description: BACnet object type
        type: str
        required: true
        choices: ['analogInput', 'analogOutput', 'analogValue', 'binaryInput', 'binaryOutput', 'binaryValue', 'multiStateInput', 'multiStateOutput', 'multiStateValue', 'device']
    object_instance:
        description: Object instance number
        type: int
        required: true
    property_name:
        description: Property name to read
        type: str
        required: true
"""

EXAMPLES = """
- name: Read present value from analog input
  community.bacnet.bacnet_read_property:
    device_id: 12345
    address: "192.168.1.100"
    object_type: "analogInput"
    object_instance: 1
    property_name: "presentValue"

- name: Read device name
  community.bacnet.bacnet_read_property:
    device_id: 12345
    object_type: "device"
    object_instance: 12345
    property_name: "deviceName"
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.bacnet.plugins.module_utils.bacnet_utils import (
    BACnetConnection,
    validate_bacnet_address,
    validate_object_identifier,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(type="str", required=False),
            port=dict(type="int", default=47808),
            device_id=dict(type="int", required=True),
            address=dict(type="str", required=False),
            object_type=dict(type="str", required=True),
            object_instance=dict(type="int", required=True),
            property_name=dict(type="str", required=True),
        ),
        supports_check_mode=True,
    )

    # Validate parameters
    if module.params["address"] and not validate_bacnet_address(
        module.params["address"]
    ):
        module.fail_json(msg="Invalid BACnet address format")

    if not validate_object_identifier(
        module.params["object_type"], module.params["object_instance"]
    ):
        module.fail_json(msg="Invalid object identifier")

    # Create BACnet connection
    bacnet_conn = BACnetConnection(module)

    try:
        # Connect to BACnet network
        bacnet_conn.connect(ip=module.params["ip"], port=module.params["port"])

        # Read property
        result = bacnet_conn.read_property(
            module.params["device_id"],
            module.params["object_type"],
            module.params["object_instance"],
            module.params["property_name"],
            module.params["address"],
        )

        module.exit_json(changed=False, **result)

    finally:
        bacnet_conn.disconnect()


if __name__ == "__main__":
    main()
