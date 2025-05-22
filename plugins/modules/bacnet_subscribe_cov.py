#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: bacnet_subscribe_cov
short_description: Subscribe to BACnet Change of Value notifications
description:
    - Subscribes to Change of Value (COV) notifications from BACnet objects
    - Useful for monitoring critical points for changes
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
    subscriber_process_id:
        description: Subscriber process identifier
        type: int
        default: 1
    confirmed:
        description: Use confirmed COV notifications
        type: bool
        default: false
    lifetime:
        description: Subscription lifetime in seconds (0 for indefinite)
        type: int
        default: 0
"""

EXAMPLES = """
- name: Subscribe to temperature sensor COV
  community.bacnet.bacnet_subscribe_cov:
    device_id: 12345
    address: "192.168.1.100"
    object_type: "analogInput"
    object_instance: 1
    lifetime: 3600
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
            subscriber_process_id=dict(type="int", default=1),
            confirmed=dict(type="bool", default=False),
            lifetime=dict(type="int", default=0),
        ),
        supports_check_mode=True,
    )

    if module.params["address"] and not validate_bacnet_address(
        module.params["address"]
    ):
        module.fail_json(msg="Invalid BACnet address format")

    if not validate_object_identifier(
        module.params["object_type"], module.params["object_instance"]
    ):
        module.fail_json(msg="Invalid object identifier")

    if module.check_mode:
        module.exit_json(changed=True, msg="Would subscribe to COV notifications")

    bacnet_conn = BACnetConnection(module)

    try:
        bacnet_conn.connect(ip=module.params["ip"], port=module.params["port"])

        # Subscribe to COV
        try:
            if module.params["address"]:
                device_address = (
                    f"{module.params['address']}:{module.params['device_id']}"
                )
            else:
                device_address = module.params["device_id"]

            # Build COV subscription request
            obj_id = (
                f"{module.params['object_type']}:{module.params['object_instance']}"
            )

            # Note: This is a simplified example. Full COV implementation would require
            # more complex BACnet service handling
            bacnet_conn.bacnet.subscribeCOV(
                device_address,
                obj_id,
                module.params["subscriber_process_id"],
                module.params["confirmed"],
                module.params["lifetime"],
            )

            module.exit_json(
                changed=True,
                subscribed=True,
                device_id=module.params["device_id"],
                object_type=module.params["object_type"],
                object_instance=module.params["object_instance"],
                lifetime=module.params["lifetime"],
            )

        except Exception as e:
            module.fail_json(msg=f"COV subscription failed: {str(e)}")

    finally:
        bacnet_conn.disconnect()


if __name__ == "__main__":
    main()
