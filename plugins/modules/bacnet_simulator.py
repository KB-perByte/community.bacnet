#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = """
---
module: bacnet_simulator
short_description: Start/stop BACnet simulator for testing
description:
    - Manages a BACnet device simulator for testing purposes
    - Creates virtual BACnet devices with configurable objects
version_added: "1.0.0"
options:
    state:
        description: State of the simulator
        type: str
        choices: ['started', 'stopped']
        default: 'started'
    device_id:
        description: Simulator device ID
        type: int
        default: 999999
    device_name:
        description: Simulator device name
        type: str
        default: "Test Device"
    ip:
        description: IP address to bind simulator to
        type: str
        default: "0.0.0.0"
    port:
        description: Port to bind simulator to
        type: int
        default: 47808
    objects:
        description: Objects to create in the simulator
        type: list
        elements: dict
        default: []
    daemon:
        description: Run simulator as daemon
        type: bool
        default: true
"""

EXAMPLES = """
- name: Start BACnet simulator with default objects
  community.bacnet.bacnet_simulator:
    state: started
    device_id: 999999
    device_name: "Test HVAC Unit"

- name: Start simulator with custom objects
  community.bacnet.bacnet_simulator:
    state: started
    device_id: 888888
    objects:
      - type: "analogInput"
        instance: 1
        name: "Temperature Sensor"
        present_value: 72.5
      - type: "analogOutput"
        instance: 1
        name: "Damper Position"
        present_value: 50.0
      - type: "binaryInput"
        instance: 1
        name: "Occupancy Sensor"
        present_value: 1

- name: Stop simulator
  community.bacnet.bacnet_simulator:
    state: stopped
"""

import os
import sys
import time
import threading
import signal
from ansible.module_utils.basic import AnsibleModule

try:
    import BAC0
    from BAC0.core.devices.local.models import (
        analog_input,
        analog_output,
        analog_value,
        binary_input,
        binary_output,
        binary_value,
        multistate_input,
        multistate_output,
        multistate_value,
    )

    HAS_BAC0 = True
except ImportError:
    HAS_BAC0 = False


class BACnetSimulator:
    def __init__(self, device_id, device_name, ip="0.0.0.0", port=47808):
        self.device_id = device_id
        self.device_name = device_name
        self.ip = ip
        self.port = port
        self.bacnet = None
        self.device = None
        self.running = False
        self.thread = None

    def create_default_objects(self):
        """Create default test objects"""
        objects = [
            # Analog Inputs (Sensors)
            analog_input(
                instance=1,
                name="Zone Temperature",
                properties={"presentValue": 72.5, "units": "degreesFahrenheit"},
            ),
            analog_input(
                instance=2,
                name="Outside Air Temperature",
                properties={"presentValue": 85.0, "units": "degreesFahrenheit"},
            ),
            analog_input(
                instance=3,
                name="Supply Air Flow",
                properties={"presentValue": 1250.0, "units": "cubicFeetPerMinute"},
            ),
            # Analog Outputs (Actuators)
            analog_output(
                instance=1,
                name="Damper Position",
                properties={"presentValue": 50.0, "units": "percent"},
            ),
            analog_output(
                instance=2,
                name="Chilled Water Valve",
                properties={"presentValue": 25.0, "units": "percent"},
            ),
            # Analog Values (Setpoints)
            analog_value(
                instance=1,
                name="Zone Temperature Setpoint",
                properties={"presentValue": 72.0, "units": "degreesFahrenheit"},
            ),
            analog_value(
                instance=2,
                name="Supply Air Flow Setpoint",
                properties={"presentValue": 1200.0, "units": "cubicFeetPerMinute"},
            ),
            # Binary Inputs (Status)
            binary_input(
                instance=1,
                name="Occupancy Sensor",
                properties={"presentValue": "active"},
            ),
            binary_input(
                instance=2,
                name="Filter Status",
                properties={"presentValue": "inactive"},
            ),
            # Binary Outputs (Commands)
            binary_output(
                instance=1, name="Fan Command", properties={"presentValue": "active"}
            ),
            binary_output(
                instance=2,
                name="Heating Command",
                properties={"presentValue": "inactive"},
            ),
            # Multi-state Values
            multistate_value(
                instance=1,
                name="System Mode",
                properties={
                    "presentValue": 1,
                    "stateText": ["Off", "Heat", "Cool", "Auto"],
                },
            ),
        ]
        return objects

    def create_custom_objects(self, object_configs):
        """Create objects from configuration"""
        objects = []

        object_type_map = {
            "analogInput": analog_input,
            "analogOutput": analog_output,
            "analogValue": analog_value,
            "binaryInput": binary_input,
            "binaryOutput": binary_output,
            "binaryValue": binary_value,
            "multiStateInput": multistate_input,
            "multiStateOutput": multistate_output,
            "multiStateValue": multistate_value,
        }

        for config in object_configs:
            obj_type = config.get("type")
            if obj_type not in object_type_map:
                continue

            obj_class = object_type_map[obj_type]
            properties = {"presentValue": config.get("present_value", 0)}

            # Add additional properties if specified
            if "units" in config:
                properties["units"] = config["units"]
            if "state_text" in config:
                properties["stateText"] = config["state_text"]

            obj = obj_class(
                instance=config.get("instance", 1),
                name=config.get("name", f"{obj_type}_{config.get('instance', 1)}"),
                properties=properties,
            )
            objects.append(obj)

        return objects

    def start(self, custom_objects=None):
        """Start the BACnet simulator"""
        try:
            # Create BACnet network
            self.bacnet = BAC0.lite(ip=self.ip, port=self.port)

            # Create objects
            if custom_objects:
                objects = self.create_custom_objects(custom_objects)
            else:
                objects = self.create_default_objects()

            # Create device
            self.device = BAC0.device(
                name=self.device_name,
                deviceId=self.device_id,
                bacnet=self.bacnet,
                object_list=objects,
            )

            self.running = True
            return True

        except Exception as e:
            raise Exception(f"Failed to start simulator: {str(e)}")

    def stop(self):
        """Stop the BACnet simulator"""
        try:
            self.running = False
            if self.device:
                self.device = None
            if self.bacnet:
                self.bacnet.disconnect()
                self.bacnet = None
            return True
        except Exception as e:
            raise Exception(f"Failed to stop simulator: {str(e)}")

    def is_running(self):
        """Check if simulator is running"""
        return self.running and self.bacnet is not None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type="str", choices=["started", "stopped"], default="started"),
            device_id=dict(type="int", default=999999),
            device_name=dict(type="str", default="Test Device"),
            ip=dict(type="str", default="0.0.0.0"),
            port=dict(type="int", default=47808),
            objects=dict(type="list", elements="dict", default=[]),
            daemon=dict(type="bool", default=True),
        ),
        supports_check_mode=True,
    )

    if not HAS_BAC0:
        module.fail_json(msg="BAC0 library is required for this module")

    state = module.params["state"]
    device_id = module.params["device_id"]
    device_name = module.params["device_name"]
    ip = module.params["ip"]
    port = module.params["port"]
    objects = module.params["objects"]

    simulator = BACnetSimulator(device_id, device_name, ip, port)

    try:
        if state == "started":
            if module.check_mode:
                module.exit_json(changed=True, msg="Would start BACnet simulator")

            success = simulator.start(objects if objects else None)

            if success:
                module.exit_json(
                    changed=True,
                    msg=f"BACnet simulator started with device ID {device_id}",
                    device_id=device_id,
                    device_name=device_name,
                    address=f"{ip}:{port}",
                    running=simulator.is_running(),
                )
            else:
                module.fail_json(msg="Failed to start BACnet simulator")

        elif state == "stopped":
            if module.check_mode:
                module.exit_json(changed=True, msg="Would stop BACnet simulator")

            success = simulator.stop()

            if success:
                module.exit_json(
                    changed=True, msg="BACnet simulator stopped", running=False
                )
            else:
                module.fail_json(msg="Failed to stop BACnet simulator")

    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
