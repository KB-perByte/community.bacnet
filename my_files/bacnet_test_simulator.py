#!/usr/bin/env python3
"""
Standalone BACnet simulator for testing the Ansible collection
"""

import time
import random
import threading
import signal
import sys
import argparse

try:
    import BAC0
    from BAC0.core.devices.local.models import (
        analog_input,
        analog_output,
        analog_value,
        binary_input,
        binary_output,
        binary_value,
        multistate_value,
    )
except ImportError:
    print("BAC0 library is required. Install with: pip install BAC0")
    sys.exit(1)


class HVACSimulator:
    """
    Simulates a complete HVAC system with realistic behavior
    """

    def __init__(
        self, device_id=100, device_name="HVAC Unit 1", ip="0.0.0.0", port=47808
    ):
        self.device_id = device_id
        self.device_name = device_name
        self.ip = ip
        self.port = port
        self.bacnet = None
        self.device = None
        self.running = False
        self.simulation_thread = None

        # Simulation variables
        self.zone_temp = 72.0
        self.outside_temp = 85.0
        self.setpoint = 72.0
        self.occupancy = True
        self.fan_status = True
        self.system_mode = 3  # Auto mode
        self.damper_position = 50.0
        self.valve_position = 25.0

    def create_objects(self):
        """Create BACnet objects for the HVAC system"""
        return [
            # Temperature Sensors
            analog_input(
                instance=1,
                name="Zone Temperature",
                properties={
                    "presentValue": self.zone_temp,
                    "units": "degreesFahrenheit",
                    "description": "Zone air temperature sensor",
                },
            ),
            analog_input(
                instance=2,
                name="Outside Air Temperature",
                properties={
                    "presentValue": self.outside_temp,
                    "units": "degreesFahrenheit",
                    "description": "Outside air temperature sensor",
                },
            ),
            analog_input(
                instance=3,
                name="Supply Air Flow",
                properties={
                    "presentValue": 1200.0,
                    "units": "cubicFeetPerMinute",
                    "description": "Supply air flow measurement",
                },
            ),
            analog_input(
                instance=4,
                name="Return Air Temperature",
                properties={
                    "presentValue": 75.0,
                    "units": "degreesFahrenheit",
                    "description": "Return air temperature",
                },
            ),
            # Control Outputs
            analog_output(
                instance=1,
                name="Damper Position",
                properties={
                    "presentValue": self.damper_position,
                    "units": "percent",
                    "description": "Outside air damper position",
                },
            ),
            analog_output(
                instance=2,
                name="Chilled Water Valve",
                properties={
                    "presentValue": self.valve_position,
                    "units": "percent",
                    "description": "Chilled water valve position",
                },
            ),
            analog_output(
                instance=3,
                name="Hot Water Valve",
                properties={
                    "presentValue": 0.0,
                    "units": "percent",
                    "description": "Hot water valve position",
                },
            ),
            # Setpoints and Values
            analog_value(
                instance=1,
                name="Zone Temperature Setpoint",
                properties={
                    "presentValue": self.setpoint,
                    "units": "degreesFahrenheit",
                    "description": "Zone temperature setpoint",
                },
            ),
            analog_value(
                instance=2,
                name="Supply Air Flow Setpoint",
                properties={
                    "presentValue": 1200.0,
                    "units": "cubicFeetPerMinute",
                    "description": "Supply air flow setpoint",
                },
            ),
            # Binary Status Points
            binary_input(
                instance=1,
                name="Occupancy Sensor",
                properties={
                    "presentValue": "active" if self.occupancy else "inactive",
                    "description": "Zone occupancy sensor",
                },
            ),
            binary_input(
                instance=2,
                name="Filter Status",
                properties={
                    "presentValue": "inactive",
                    "description": "Filter maintenance indicator",
                },
            ),
            binary_input(
                instance=3,
                name="High Temperature Alarm",
                properties={
                    "presentValue": "inactive",
                    "description": "High temperature alarm",
                },
            ),
            # Binary Commands
            binary_output(
                instance=1,
                name="Fan Command",
                properties={
                    "presentValue": "active" if self.fan_status else "inactive",
                    "description": "Supply fan start/stop command",
                },
            ),
            binary_output(
                instance=2,
                name="Heating Command",
                properties={
                    "presentValue": "inactive",
                    "description": "Heating enable command",
                },
            ),
            binary_output(
                instance=3,
                name="Cooling Command",
                properties={
                    "presentValue": "active",
                    "description": "Cooling enable command",
                },
            ),
            # Multi-state Objects
            multistate_value(
                instance=1,
                name="System Mode",
                properties={
                    "presentValue": self.system_mode,
                    "stateText": ["Off", "Heat", "Cool", "Auto", "Emergency Heat"],
                    "description": "HVAC system operating mode",
                },
            ),
            multistate_value(
                instance=2,
                name="Fan Mode",
                properties={
                    "presentValue": 2,
                    "stateText": ["Off", "On", "Auto"],
                    "description": "Fan operating mode",
                },
            ),
        ]

    def start(self):
        """Start the HVAC simulator"""
        try:
            print(f"Starting BACnet HVAC simulator...")
            print(f"Device ID: {self.device_id}")
            print(f"Device Name: {self.device_name}")
            print(f"Network: {self.ip}:{self.port}")

            # Initialize BACnet
            self.bacnet = BAC0.lite(ip=self.ip, port=self.port)

            # Create objects
            objects = self.create_objects()

            # Create device
            self.device = BAC0.device(
                name=self.device_name,
                deviceId=self.device_id,
                bacnet=self.bacnet,
                object_list=objects,
            )

            print(f"Device created successfully!")
            print(f"Objects created: {len(objects)}")

            # Start simulation
            self.running = True
            self.simulation_thread = threading.Thread(target=self._simulate)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()

            print("Simulation started. Press Ctrl+C to stop.")
            return True

        except Exception as e:
            print(f"Error starting simulator: {e}")
            return False

    def stop(self):
        """Stop the simulator"""
        print("Stopping simulator...")
        self.running = False

        if self.simulation_thread:
            self.simulation_thread.join(timeout=2)

        if self.bacnet:
            self.bacnet.disconnect()

        print("Simulator stopped.")

    def _simulate(self):
        """Run the HVAC simulation"""
        while self.running:
            try:
                # Simulate temperature changes
                self._update_temperatures()

                # Update occupancy randomly
                if random.random() < 0.1:  # 10% chance each cycle
                    self.occupancy = not self.occupancy

                # Update BACnet objects with new values
                self._update_bacnet_objects()

                time.sleep(5)  # Update every 5 seconds

            except Exception as e:
                print(f"Simulation error: {e}")
                time.sleep(1)

    def _update_temperatures(self):
        """Simulate realistic temperature behavior"""
        # Outside temperature varies throughout the day
        self.outside_temp += random.uniform(-0.5, 0.5)
        self.outside_temp = max(70, min(100, self.outside_temp))

        # Zone temperature is influenced by outside temp, HVAC operation, and occupancy
        temp_influence = 0

        # Outside air influence (when damper is open)
        if self.damper_position > 0:
            temp_influence += (
                (self.outside_temp - self.zone_temp)
                * (self.damper_position / 100)
                * 0.1
            )

        # Cooling influence
        if self.valve_position > 0 and self.fan_status:
            cooling_effect = self.valve_position / 100 * 2.0
            if self.zone_temp > self.setpoint:
                temp_influence -= cooling_effect

        # Occupancy heat gain
        if self.occupancy:
            temp_influence += 0.2

        # Random variations
        temp_influence += random.uniform(-0.1, 0.1)

        self.zone_temp += temp_influence
        self.zone_temp = max(65, min(85, self.zone_temp))

        # Simple control logic
        temp_error = self.zone_temp - self.setpoint

        if self.system_mode == 3:  # Auto mode
            if temp_error > 1.0:  # Too hot
                self.valve_position = min(100, self.valve_position + 5)
                self.damper_position = max(10, min(50, self.damper_position))
            elif temp_error < -1.0:  # Too cold
                self.valve_position = max(0, self.valve_position - 5)
                self.damper_position = max(0, self.damper_position - 5)

    def _update_bacnet_objects(self):
        """Update BACnet object values"""
        if not self.device:
            return

        try:
            # Update analog inputs
            self.device["analogInput:1"].presentValue = round(self.zone_temp, 1)
            self.device["analogInput:2"].presentValue = round(self.outside_temp, 1)
            self.device["analogInput:3"].presentValue = round(
                1200 + random.uniform(-50, 50), 1
            )

            # Update analog outputs
            self.device["analogOutput:1"].presentValue = round(self.damper_position, 1)
            self.device["analogOutput:2"].presentValue = round(self.valve_position, 1)

            # Update binary inputs
            self.device["binaryInput:1"].presentValue = (
                "active" if self.occupancy else "inactive"
            )

            # Update alarms
            high_temp_alarm = self.zone_temp > (self.setpoint + 5)
            self.device["binaryInput:3"].presentValue = (
                "active" if high_temp_alarm else "inactive"
            )

        except Exception as e:
            print(f"Error updating objects: {e}")


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nReceived interrupt signal...")
    if "simulator" in globals():
        simulator.stop()
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="BACnet HVAC Simulator")
    parser.add_argument("--device-id", type=int, default=100, help="BACnet device ID")
    parser.add_argument("--device-name", default="HVAC Unit 1", help="Device name")
    parser.add_argument("--ip", default="0.0.0.0", help="IP address to bind to")
    parser.add_argument("--port", type=int, default=47808, help="Port to bind to")

    args = parser.parse_args()

    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Create and start simulator
    global simulator
    simulator = HVACSimulator(
        device_id=args.device_id,
        device_name=args.device_name,
        ip=args.ip,
        port=args.port,
    )

    if simulator.start():
        try:
            # Keep the main thread alive
            while simulator.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            simulator.stop()
    else:
        print("Failed to start simulator")
        sys.exit(1)


if __name__ == "__main__":
    main()
