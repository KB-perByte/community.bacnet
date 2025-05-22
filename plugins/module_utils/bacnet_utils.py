# File: plugins/module_utils/bacnet_utils.py
"""
BACnet utility functions for Ansible modules
"""

import sys
import traceback
from ansible.module_utils.basic import missing_required_lib

try:
    import BAC0
    from BAC0.core.devices.local.models import ObjectFactory

    HAS_BAC0 = True
except ImportError:
    BAC0 = None
    HAS_BAC0 = False


class BACnetConnection:
    """
    BACnet connection handler for Ansible modules
    """

    def __init__(self, module):
        self.module = module
        self.bacnet = None
        self.device = None

    def connect(self, ip=None, port=47808, bbmdAddress=None, bbmdTTL=None):
        """
        Establish BACnet connection
        """
        if not HAS_BAC0:
            self.module.fail_json(msg=missing_required_lib("BAC0"))

        try:
            if bbmdAddress and bbmdTTL:
                self.bacnet = BAC0.lite(
                    ip=ip, port=port, bbmdAddress=bbmdAddress, bbmdTTL=bbmdTTL
                )
            else:
                self.bacnet = BAC0.lite(ip=ip, port=port)

            return True
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to connect to BACnet network: {str(e)}",
                exception=traceback.format_exc(),
            )

    def disconnect(self):
        """
        Disconnect from BACnet network
        """
        if self.bacnet:
            self.bacnet.disconnect()

    def discover_devices(self, timeout=30):
        """
        Discover BACnet devices on the network
        """
        try:
            devices = self.bacnet.whois(timeout=timeout)
            return [
                {
                    "device_id": device.deviceInstanceNumber,
                    "address": str(device.address),
                    "name": (
                        device.deviceName
                        if hasattr(device, "deviceName")
                        else "Unknown"
                    ),
                    "vendor": (
                        device.vendorName
                        if hasattr(device, "vendorName")
                        else "Unknown"
                    ),
                }
                for device in devices
            ]
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to discover devices: {str(e)}",
                exception=traceback.format_exc(),
            )

    def get_device(self, device_id, address=None):
        """
        Get a BACnet device by ID
        """
        try:
            if address:
                device_address = f"{address}:{device_id}"
            else:
                device_address = device_id

            self.device = BAC0.device(device_address, device_id, self.bacnet)
            return self.device
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to connect to device {device_id}: {str(e)}",
                exception=traceback.format_exc(),
            )

    def read_property(
        self, device_id, object_type, object_instance, property_name, address=None
    ):
        """
        Read a property from a BACnet object
        """
        try:
            if address:
                device_address = f"{address}:{device_id}"
            else:
                device_address = device_id

            prop_id = f"{object_type}:{object_instance} {property_name}"
            value = self.bacnet.read(f"{device_address} {prop_id}")

            return {
                "value": value,
                "object_type": object_type,
                "object_instance": object_instance,
                "property_name": property_name,
            }
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to read property {property_name}: {str(e)}",
                exception=traceback.format_exc(),
            )

    def write_property(
        self,
        device_id,
        object_type,
        object_instance,
        property_name,
        value,
        address=None,
        priority=None,
    ):
        """
        Write a property to a BACnet object
        """
        try:
            if address:
                device_address = f"{address}:{device_id}"
            else:
                device_address = device_id

            prop_id = f"{object_type}:{object_instance} {property_name}"

            if priority:
                self.bacnet.write(f"{device_address} {prop_id} {value} - {priority}")
            else:
                self.bacnet.write(f"{device_address} {prop_id} {value}")

            return True
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to write property {property_name}: {str(e)}",
                exception=traceback.format_exc(),
            )

    def get_object_list(self, device_id, address=None):
        """
        Get list of objects from a BACnet device
        """
        try:
            if address:
                device_address = f"{address}:{device_id}"
            else:
                device_address = device_id

            # Read the object list property
            object_list = self.bacnet.read(
                f"{device_address} device:{device_id} objectList"
            )

            objects = []
            for obj in object_list:
                obj_type, obj_instance = obj
                objects.append(
                    {
                        "object_type": obj_type,
                        "object_instance": obj_instance,
                        "object_name": f"{obj_type}:{obj_instance}",
                    }
                )

            return objects
        except Exception as e:
            self.module.fail_json(
                msg=f"Failed to get object list: {str(e)}",
                exception=traceback.format_exc(),
            )


def validate_bacnet_address(address):
    """
    Validate BACnet address format
    """
    if not address:
        return False

    # Check for IP:port format
    if ":" in address:
        parts = address.split(":")
        if len(parts) != 2:
            return False
        try:
            # Validate IP
            ip_parts = parts[0].split(".")
            if len(ip_parts) != 4:
                return False
            for part in ip_parts:
                if not 0 <= int(part) <= 255:
                    return False
            # Validate port
            port = int(parts[1])
            if not 0 <= port <= 65535:
                return False
        except ValueError:
            return False

    return True


def validate_object_identifier(object_type, object_instance):
    """
    Validate BACnet object identifier
    """
    valid_object_types = [
        "analogInput",
        "analogOutput",
        "analogValue",
        "binaryInput",
        "binaryOutput",
        "binaryValue",
        "multiStateInput",
        "multiStateOutput",
        "multiStateValue",
        "device",
        "file",
        "group",
        "loop",
        "notificationClass",
        "program",
        "schedule",
        "averaging",
        "multiStateValue",
        "trendLog",
        "lifeSafetyPoint",
        "lifeSafetyZone",
    ]

    if object_type not in valid_object_types:
        return False

    try:
        instance = int(object_instance)
        if not 0 <= instance <= 4194303:  # 2^22 - 1
            return False
    except ValueError:
        return False

    return True
