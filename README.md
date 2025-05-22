# Ansible BACnet Collection

A comprehensive Ansible collection for interacting with BACnet (Building Automation and Control Networks) devices using the BAC0 Python library.

## Features

- **Device Discovery**: Automatically discover BACnet devices on your network
- **Property Operations**: Read and write BACnet object properties
- **Object Management**: List and manage BACnet objects
- **Monitoring**: Subscribe to Change of Value (COV) notifications
- **Testing**: Built-in BACnet simulator for development and testing
- **Trend Data**: Access historical trend log data
- **Alarm Management**: Monitor device alarms and events

## Installation

### Prerequisites

1. Python 3.7+
2. Ansible 2.9+
3. BAC0 Python library

### Install the Collection

```bash
# Install from Ansible Galaxy (when published)
ansible-galaxy collection install community.bacnet

# Or install from Git repository
ansible-galaxy collection install git+https://github.com/yourusername/ansible-bacnet-collection.git
```

### Install Python Dependencies

```bash
pip install BAC0>=22.09.15 ifaddr>=0.1.7 netifaces>=0.11.0
```

## Quick Start

### 1. Discover BACnet Devices

```yaml
- name: Discover BACnet devices
  community.bacnet.bacnet_device_info:
    timeout: 30
  register: devices

- name: Display discovered devices
  debug:
    var: devices.devices
```

### 2. Read Device Properties

```yaml
- name: Read temperature sensor
  community.bacnet.bacnet_read_property:
    device_id: 12345
    address: '192.168.1.100'
    object_type: 'analogInput'
    object_instance: 1
    property_name: 'presentValue'
  register: temperature

- name: Display temperature
  debug:
    msg: 'Current temperature: {{ temperature.value }}°F'
```

### 3. Control Devices

```yaml
- name: Set temperature setpoint
  community.bacnet.bacnet_write_property:
    device_id: 12345
    address: '192.168.1.100'
    object_type: 'analogValue'
    object_instance: 1
    property_name: 'presentValue'
    value: 72.0
    priority: 8
```

### 4. Start Test Simulator

```yaml
- name: Start BACnet simulator for testing
  community.bacnet.bacnet_simulator:
    state: started
    device_id: 999999
    device_name: 'Test HVAC Unit'
    objects:
      - type: 'analogInput'
        instance: 1
        name: 'Zone Temperature'
        present_value: 72.5
      - type: 'binaryInput'
        instance: 1
        name: 'Occupancy Sensor'
        present_value: 1
```

## Modules

### Core Modules

| Module                  | Description                                       |
| ----------------------- | ------------------------------------------------- |
| `bacnet_device_info`    | Discover and get information about BACnet devices |
| `bacnet_read_property`  | Read properties from BACnet objects               |
| `bacnet_write_property` | Write properties to BACnet objects                |
| `bacnet_object_list`    | Get list of objects from a BACnet device          |

### Discovery Modules

| Module          | Description                               |
| --------------- | ----------------------------------------- |
| `bacnet_who_is` | Send Who-Is requests for device discovery |

### Monitoring Modules

| Module                 | Description                                |
| ---------------------- | ------------------------------------------ |
| `bacnet_subscribe_cov` | Subscribe to Change of Value notifications |
| `bacnet_trend_log`     | Read trend log data from devices           |
| `bacnet_alarm_summary` | Get alarm and event summaries              |

### Testing Modules

| Module             | Description                                    |
| ------------------ | ---------------------------------------------- |
| `bacnet_simulator` | Start/stop BACnet device simulator for testing |

## Roles

### bacnet_setup

Sets up the BACnet environment including:

- Installing Python dependencies
- Configuring network settings
- Setting up firewall rules

```yaml
- name: Setup BACnet environment
  include_role:
    name: community.bacnet.bacnet_setup
  vars:
    bacnet_port: 47808
    bacnet_interface: 'eth0'
    configure_firewall: true
```

### bacnet_simulator

Starts and manages the BACnet simulator:

```yaml
- name: Start BACnet simulator
  include_role:
    name: community.bacnet.bacnet_simulator
  vars:
    simulator_device_id: 999999
    simulator_device_name: 'Test Device'
```

## Example Playbooks

The collection includes several example playbooks:

- `playbooks/bacnet_discovery.yml` - Network discovery and inventory
- `playbooks/bacnet_monitoring.yml` - Continuous monitoring setup
- `playbooks/bacnet_control.yml` - Device control operations
- `test_collection.yml` - Complete collection testing

## BACnet Simulator

### Standalone Simulator

For development and testing, use the standalone simulator:

```bash
python test_bacnet_simulator.py --device-id 100 --device-name "HVAC Unit 1"
```

The simulator creates a realistic HVAC system with:

- Temperature sensors (zone, outside air, return air)
- Control outputs (dampers, valves)
- Binary status points (occupancy, alarms)
- Setpoints and system modes

### Simulator Features

- **Realistic Behavior**: Simulates actual HVAC system responses
- **Dynamic Values**: Temperature and status values change over time
- **Control Response**: Responds to write commands
- **Multiple Objects**: Creates a full complement of BACnet objects

## Network Configuration

### Basic Network Setup

```yaml
# Connect to local BACnet network
- community.bacnet.bacnet_device_info:
    ip: '192.168.1.100' # Local interface IP
    port: 47808 # BACnet port
```

### BBMD Configuration

For BACnet networks using BBMD (BACnet Broadcast Management Device):

```yaml
- community.bacnet.bacnet_device_info:
    bbmd_address: '192.168.1.1:47808'
    bbmd_ttl: 30
```

## Advanced Usage

### Monitoring Multiple Points

```yaml
- name: Monitor critical points
  community.bacnet.bacnet_read_property:
    device_id: '{{ item.device_id }}'
    address: '{{ item.address }}'
    object_type: '{{ item.object_type }}'
    object_instance: '{{ item.object_instance }}'
    property_name: 'presentValue'
  loop:
    - device_id: 100
      address: '192.168.1.100'
      object_type: 'analogInput'
      object_instance: 1
    - device_id: 100
      address: '192.168.1.100'
      object_type: 'binaryInput'
      object_instance: 1
  register: monitoring_data
```

### Conditional Control

```yaml
- name: Read current temperature
  community.bacnet.bacnet_read_property:
    device_id: 100
    object_type: 'analogInput'
    object_instance: 1
    property_name: 'presentValue'
  register: current_temp

- name: Adjust setpoint if too hot
  community.bacnet.bacnet_write_property:
    device_id: 100
    object_type: 'analogValue'
    object_instance: 1
    property_name: 'presentValue'
    value: '{{ current_temp.value - 2 }}'
    priority: 8
  when: current_temp.value | float > 75
```

### Error Handling

```yaml
- name: Read property with error handling
  community.bacnet.bacnet_read_property:
    device_id: 12345
    object_type: 'analogInput'
    object_instance: 1
    property_name: 'presentValue'
  register: read_result
  ignore_errors: true

- name: Handle read failure
  debug:
    msg: 'Failed to read property: {{ read_result.msg }}'
  when: read_result.failed
```

## Testing

### Unit Tests

```bash
# Run unit tests
cd tests/unit
python -m pytest
```

### Integration Tests

```bash
# Run integration tests with simulator
ansible-playbook test_collection.yml
```

### Manual Testing

1. Start the simulator:

```bash
python test_bacnet_simulator.py --device-id 999999
```

2. Run discovery:

```bash
ansible-playbook -i localhost, playbooks/bacnet_discovery.yml
```

## Troubleshooting

### Common Issues

1. **Connection Timeout**

   - Check network connectivity
   - Verify BACnet port (47808) is not blocked
   - Ensure device is responding to Who-Is requests

2. **Permission Denied**

   - BACnet uses UDP port 47808, which may require root privileges
   - Consider using higher port numbers for testing

3. **Device Not Found**
   - Verify device ID and address
   - Check if device is on the same network segment
   - Use BBMD if crossing network boundaries

### Debug Mode

Enable verbose logging:

```yaml
- name: Debug BACnet communication
  community.bacnet.bacnet_device_info:
    timeout: 30
  register: result

- debug:
    var: result
    verbosity: 2
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
git clone https://github.com/yourusername/ansible-bacnet-collection.git
cd ansible-bacnet-collection
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## License

GPL-2.0-or-later

## Support

- GitHub Issues: [Report bugs and request features](https://github.com/yourusername/ansible-bacnet-collection/issues)
- Documentation: [Full documentation](https://github.com/yourusername/ansible-bacnet-collection/wiki)
- Community: Join the discussion in GitHub Discussions

## Changelog

### Version 1.0.0

- Initial release
- Core BACnet modules (device info, read/write properties)
- BACnet simulator for testing
- Example playbooks and roles
- Comprehensive documentation
