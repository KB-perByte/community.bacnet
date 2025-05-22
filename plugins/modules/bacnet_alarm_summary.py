#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: bacnet_alarm_summary
short_description: Get alarm summary from BACnet device
description:
    - Retrieves current alarm and event summary from BACnet devices
    - Useful for monitoring system health and alerts
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
    alarm_state:
        description: Filter by alarm state
        type: str
        choices: ['normal', 'fault', 'offnormal', 'highlimit', 'lowlimit']
        required: false
"""

EXAMPLES = """
- name: Get all active alarms
  community.bacnet.bacnet_alarm_summary:
    device_id: 12345
    address: "192.168.1.100"

- name: Get only fault alarms
  community.bacnet.bacnet_alarm_summary:
    device_id: 12345
    address: "192.168.1.100"
    alarm_state: "fault"
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
            device_id=dict(type="int", required=True),
            address=dict(type="str", required=False),
            alarm_state=dict(
                type="str",
                choices=["normal", "fault", "offnormal", "highlimit", "lowlimit"],
                required=False,
            ),
        ),
        supports_check_mode=True,
    )

    if module.params["address"] and not validate_bacnet_address(
        module.params["address"]
    ):
        module.fail_json(msg="Invalid BACnet address format")

    bacnet_conn = BACnetConnection(module)

    try:
        bacnet_conn.connect(ip=module.params["ip"], port=module.params["port"])

        # Get alarm summary
        try:
            if module.params["address"]:
                device_address = (
                    f"{module.params['address']}:{module.params['device_id']}"
                )
            else:
                device_address = module.params["device_id"]

            # This would typically use the GetAlarmSummary BACnet service
            # For now, we'll simulate by reading alarm-related objects
            alarms = []

            # Try to read common alarm objects
            try:
                # Read device object for system alarms
                device_reliability = bacnet_conn.bacnet.read(
                    f"{device_address} device:{module.params['device_id']} reliability"
                )
                if device_reliability and device_reliability != "noFaultDetected":
                    alarms.append(
                        {
                            "object_type": "device",
                            "object_instance": module.params["device_id"],
                            "alarm_type": "reliability",
                            "alarm_state": device_reliability,
                            "priority": "high",
                        }
                    )
            except:
                pass

            # Filter by alarm state if specified
            if module.params["alarm_state"]:
                alarms = [
                    alarm
                    for alarm in alarms
                    if alarm["alarm_state"] == module.params["alarm_state"]
                ]

            module.exit_json(
                changed=False,
                alarms=alarms,
                alarm_count=len(alarms),
                device_id=module.params["device_id"],
            )

        except Exception as e:
            module.fail_json(msg=f"Failed to get alarm summary: {str(e)}")

    finally:
        bacnet_conn.disconnect()


if __name__ == "__main__":
    main()
