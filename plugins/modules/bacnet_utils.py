#!/usr/bin/python

from bacpypes3.pdu import Address
from bacpypes3.apdu import ErrorPDU, SimpleAckPDU
from bacpypes3.app import BIPSimpleApplication
from bacpypes3.vendor import get_vendor_info


def create_bacnet_client(device_address, network_interface=""):
    """Create BACnet client with proper vendor configuration"""
    vendor_info = get_vendor_info(network_interface)
    return BIPSimpleApplication(
        Address(device_address),
        network_interface=network_interface,
        vendor_info=vendor_info,
    )


def parse_object_identifier(object_type, object_instance, vendor_info):
    """Convert object type/instance to BACnet ObjectIdentifier"""
    return vendor_info.get_object_type(object_type).object_type(
        objectInstance=object_instance
    )


def validate_response(response, expected_type):
    """Validate BACnet response and handle errors"""
    if isinstance(response, ErrorPDU):
        raise RuntimeError(f"BACnet Error: {response.errorCode}")
    if not isinstance(response, expected_type):
        raise RuntimeError(f"Unexpected response type: {type(response)}")
    return response


def convert_property_value(value, property_type):
    """Convert Python values to BACnet primitives"""
    return property_type(value)
