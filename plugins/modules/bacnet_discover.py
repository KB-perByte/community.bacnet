#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from bacpypes3.pdu import Address
from bacpypes3.app import BIPSimpleApplication
import asyncio


def discover_devices(network_interface, timeout=10):
    async def _discover():
        app = BIPSimpleApplication(Address(network_interface))
        await app.who_is()
        await asyncio.sleep(timeout)
        return app.devices

    loop = asyncio.new_event_loop()
    devices = loop.run_until_complete(_discover())
    loop.close()
    return [
        {
            "device_id": dev.deviceIdentifier,
            "address": str(dev.address),
            "vendor_name": dev.vendorName,
            "objects": [
                {"type": obj.objectIdentifier[0], "instance": obj.objectIdentifier[1]}
                for obj in dev.objectList
            ],
        }
        for dev in devices
    ]


def run_module():
    module_args = dict(
        network_interface=dict(type="str", required=True),
        timeout=dict(type="int", default=10),
    )

    result = {"changed": False}
    module = AnsibleModule(argument_spec=module_args)

    try:
        devices = discover_devices(
            module.params["network_interface"], module.params["timeout"]
        )
        result["devices"] = devices
    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    run_module()
