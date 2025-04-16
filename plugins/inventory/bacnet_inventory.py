from ansible.plugins.inventory import BaseInventoryPlugin
from bacnet_collection.plugins.modules.bacnet_discover import discover_devices


class InventoryModule(BaseInventoryPlugin):
    NAME = "communit.bacnet.bacnet_inventory"

    def verify_file(self, path):
        return super().verify_file(path) and path.endswith("bacnet_inventory.yml")

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path)
        config = self._read_config_data(path)

        devices = discover_devices(
            config.get("network_interface", ""), config.get("timeout", 10)
        )

        for device in devices:
            hostname = f"bacnet_{device['device_id']}"
            self.inventory.add_host(hostname)
            self.inventory.set_variable(hostname, "ansible_host", device["address"])
            self.inventory.set_variable(
                hostname, "bacnet_device_id", device["device_id"]
            )
            self.inventory.set_variable(
                hostname, "bacnet_vendor", device["vendor_name"]
            )

            for obj in device["objects"]:
                group_name = f"bacnet_{obj['type']}"
                self.inventory.add_group(group_name)
                self.inventory.add_child(group_name, hostname)
