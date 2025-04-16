#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
from bacpypes3.apdu import WritePropertyRequest, SimpleAckPDU
from .bacnet_utils import (
    create_bacnet_client,
    parse_object_identifier,
    validate_response,
    convert_property_value,
)


def run_module():
    module_args = dict(
        device_address=dict(type="str", required=True),
        object_type=dict(type="str", required=True),
        object_instance=dict(type="int", required=True),
        property_identifier=dict(type="str", required=True),
        value=dict(type="raw", required=True),
        priority=dict(type="int", default=None),
        network_interface=dict(type="str", default=""),
        timeout=dict(type="int", default=10),
    )

    result = {"changed": False}
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    try:
        if module.check_mode:
            module.exit_json(**result)

        # Initialize BACnet client
        client = create_bacnet_client(
            module.params["device_address"], module.params["network_interface"]
        )

        # Get vendor-specific type mappings
        vendor_info = client.vendor_info

        # Create object identifier
        obj_id = parse_object_identifier(
            module.params["object_type"], module.params["object_instance"], vendor_info
        )

        # Get property type definition
        prop_def = vendor_info.get_property_type(
            obj_id.objectType, module.params["property_identifier"]
        )

        # Create write request
        request = WritePropertyRequest(
            objectIdentifier=obj_id,
            propertyIdentifier=prop_def.propertyIdentifier,
            propertyValue=convert_property_value(
                module.params["value"], prop_def.property_type
            ),
        )

        if module.params["priority"]:
            request.priority = module.params["priority"]

        # Send request
        response = client.make_request(request, timeout=module.params["timeout"])
        validate_response(response, SimpleAckPDU)

        result["changed"] = True
        result["message"] = "Write operation successful"

    except Exception as e:
        module.fail_json(msg=str(e), **result)

    module.exit_json(**result)


if __name__ == "__main__":
    run_module()
