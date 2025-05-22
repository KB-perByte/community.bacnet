#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: bacnet_trend_log
short_description: Access BACnet trend log data
description:
    - Reads trend log data from BACnet devices
    - Can retrieve historical data for analysis
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
    trend_log_instance:
        description: Trend log object instance
        type: int
        required: true
    record_count:
        description: Number of records to retrieve
        type: int
        default: 100
    start_time:
        description: Start time for data retrieval (ISO format)
        type: str
        required: false
"""

EXAMPLES = """
- name: Read trend log data
  community.bacnet.bacnet_trend_log:
    device_id: 12345
    address: "192.168.1.100"
    trend_log_instance: 1
    record_count: 50
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
            trend_log_instance=dict(type="int", required=True),
            record_count=dict(type="int", default=100),
            start_time=dict(type="str", required=False),
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

        # Read trend log data
        try:
            if module.params["address"]:
                device_address = (
                    f"{module.params['address']}:{module.params['device_id']}"
                )
            else:
                device_address = module.params["device_id"]

            trend_log_id = f"trendLog:{module.params['trend_log_instance']}"

            # Read trend log buffer
            log_buffer = bacnet_conn.bacnet.read(
                f"{device_address} {trend_log_id} logBuffer"
            )

            # Process the log data
            log_records = []
            for record in log_buffer[: module.params["record_count"]]:
                log_records.append(
                    {
                        "timestamp": (
                            str(record.timestamp)
                            if hasattr(record, "timestamp")
                            else "Unknown"
                        ),
                        "value": (
                            record.value if hasattr(record, "value") else "Unknown"
                        ),
                        "status": (
                            str(record.statusFlags)
                            if hasattr(record, "statusFlags")
                            else "Unknown"
                        ),
                    }
                )

            module.exit_json(
                changed=False,
                records=log_records,
                record_count=len(log_records),
                trend_log_instance=module.params["trend_log_instance"],
            )

        except Exception as e:
            module.fail_json(msg=f"Failed to read trend log: {str(e)}")

    finally:
        bacnet_conn.disconnect()


if __name__ == "__main__":
    main()
