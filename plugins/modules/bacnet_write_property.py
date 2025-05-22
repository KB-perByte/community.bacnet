#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: bacnet_write_property
short_description: Write properties to BACnet objects
description:
    - Writes property values to BACnet objects
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
    object_instance:
        description: Object instance number
        type: int
        required: true
    property_name:
        description: Property name to write
        type: str
        required: true
    value:
        description: Value to write
        required: true
    priority:
        description: Write priority (1-16)
        type: int
        required: false
"""

EXAMPLES = """
- name: Set analog output value
  community.bacnet.bacnet_write_property:
    device_id: 12345
    address: "192.168.1.100"
    object_type: "analogOutput"
    object_instance: 1
    property_name: "presentValue"
    value: 75.5
    priority: 8
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
            value=dict(required=True),
            priority=dict(type="int", required=False),
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

    if module.params["priority"] and not 1 <= module.params["priority"] <= 16:
        module.fail_json(msg="Priority must be between 1 and 16")

    if module.check_mode:
        module.exit_json(changed=True, msg="Would write property")

    # Create BACnet connection
    bacnet_conn = BACnetConnection(module)

    try:
        # Connect to BACnet network
        bacnet_conn.connect(ip=module.params["ip"], port=module.params["port"])

        # Write property
        success = bacnet_conn.write_property(
            module.params["device_id"],
            module.params["object_type"],
            module.params["object_instance"],
            module.params["property_name"],
            module.params["value"],
            module.params["address"],
            module.params["priority"],
        )

        module.exit_json(changed=True, success=success, value=module.params["value"])

    finally:
        bacnet_conn.disconnect()


if __name__ == "__main__":
    main()
