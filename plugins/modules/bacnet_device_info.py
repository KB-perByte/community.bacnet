#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: bacnet_device_info
short_description: Gather information about BACnet devices
description:
    - Discovers and retrieves information about BACnet devices on the network
    - Can target specific devices or discover all devices
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
        description: Specific device ID to query
        type: int
        required: false
    address:
        description: Specific device address
        type: str
        required: false
    timeout:
        description: Discovery timeout in seconds
        type: int
        default: 30
    bbmd_address:
        description: BBMD (BACnet Broadcast Management Device) address
        type: str
        required: false
    bbmd_ttl:
        description: BBMD Time To Live
        type: int
        required: false
"""

EXAMPLES = """
- name: Discover all BACnet devices
  community.bacnet.bacnet_device_info:

- name: Get info for specific device
  community.bacnet.bacnet_device_info:
    device_id: 12345
    address: "192.168.1.100"

- name: Discover devices through BBMD
  community.bacnet.bacnet_device_info:
    bbmd_address: "192.168.1.1:47808"
    bbmd_ttl: 30
"""

RETURN = """
devices:
    description: List of discovered BACnet devices
    returned: always
    type: list
    elements: dict
    contains:
        device_id:
            description: Device instance number
            type: int
        address:
            description: Device network address
            type: str
        name:
            description: Device name
            type: str
        vendor:
            description: Device vendor name
            type: str
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.community.bacnet.plugins.module_utils.bacnet_utils import (
    BACnetConnection,
    validate_bacnet_address,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ip=dict(type="str", required=False),
            port=dict(type="int", default=47808),
            device_id=dict(type="int", required=False),
            address=dict(type="str", required=False),
            timeout=dict(type="int", default=30),
            bbmd_address=dict(type="str", required=False),
            bbmd_ttl=dict(type="int", required=False),
        ),
        supports_check_mode=True,
    )

    # Validate parameters
    if module.params["address"] and not validate_bacnet_address(
        module.params["address"]
    ):
        module.fail_json(msg="Invalid BACnet address format")

    if module.params["bbmd_address"] and not validate_bacnet_address(
        module.params["bbmd_address"]
    ):
        module.fail_json(msg="Invalid BBMD address format")

    # Create BACnet connection
    bacnet_conn = BACnetConnection(module)

    try:
        # Connect to BACnet network
        bacnet_conn.connect(
            ip=module.params["ip"],
            port=module.params["port"],
            bbmdAddress=module.params["bbmd_address"],
            bbmdTTL=module.params["bbmd_ttl"],
        )

        if module.params["device_id"]:
            # Get specific device info
            device = bacnet_conn.get_device(
                module.params["device_id"], module.params["address"]
            )
            devices = [
                {
                    "device_id": device.deviceInstanceNumber,
                    "address": str(device.address),
                    "name": getattr(device, "deviceName", "Unknown"),
                    "vendor": getattr(device, "vendorName", "Unknown"),
                }
            ]
        else:
            # Discover all devices
            devices = bacnet_conn.discover_devices(module.params["timeout"])

        module.exit_json(changed=False, devices=devices, device_count=len(devices))

    finally:
        bacnet_conn.disconnect()


if __name__ == "__main__":
    main()
