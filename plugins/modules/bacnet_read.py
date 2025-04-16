#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from bacpypes3.pdu import Address
from bacpypes3.apdu import ReadPropertyRequest, ReadPropertyACK
from bacpypes3.primitivedata import ObjectIdentifier
from bacpypes3.vendor import get_vendor_info
import bacpypes3.app


def run_module():
    module_args = dict(
        device_address=dict(type="str", required=True),
        object_type=dict(type="str", required=True),
        object_instance=dict(type="int", required=True),
        property_identifier=dict(type="str", required=True),
        network_interface=dict(type="str", default=""),
        timeout=dict(type="int", default=10),
    )

    result = {"changed": False}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        vendor_info = get_vendor_info(module.params["network_interface"])
        device_address = Address(module.params["device_address"])

        client = bacpypes3.app.BIPSimpleApplication(
            device_address,
            network_interface=module.params["network_interface"],
            vendor_info=vendor_info,
        )

        obj_id = ObjectIdentifier(
            f"{module.params['object_type']} {module.params['object_instance']}"
        ).value
        prop_id = vendor_info.get_property_type(
            obj_id[0], module.params["property_identifier"]
        ).propertyIdentifier

        request = ReadPropertyRequest(
            objectIdentifier=obj_id, propertyIdentifier=prop_id
        )
        request.pduDestination = device_address

        response = client.make_request(request, timeout=module.params["timeout"])
        if isinstance(response, ReadPropertyACK):
            result["value"] = response.propertyValue.cast_out()
            result["changed"] = False
        else:
            module.fail_json(msg="Failed to read property", **result)

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    run_module()
