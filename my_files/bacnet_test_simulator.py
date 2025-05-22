import asyncio
import datetime
import BAC0
from BAC0.core.devices.local.factory import binary_output, binary_value

bacnetDeviceId = 3056
bacnetIp = "0.0.0.0/24"

BAC0.log_level("silence")


class FanSystem:
    def __init__(self):
        self.lastFanStatus = False

    def update(self, switchValue, emergencyValue):
        fanStatus = switchValue and not emergencyValue
        changed = fanStatus != self.lastFanStatus
        self.lastFanStatus = fanStatus
        return changed, fanStatus


async def runBacnet():
    try:
        bacnet = BAC0.start(ip=bacnetIp, deviceId=bacnetDeviceId)

        bacnet.this_application.objectName = "FanController"
        bacnet.this_application.vendorName = "BACnet Simulator"
        bacnet.this_application.modelName = "FanControl-1000"
        bacnet.this_application.firmwareRevision = "1.0.0"

        fanStatus = binary_output(
            name="FanStatus",
            instance=1,
            description="Fan operational state",
            presentValue=False,
            is_commandable=False,
        )

        switchStatus = binary_value(
            name="SwitchStatus",
            instance=1,
            description="Main control switch",
            presentValue=False,
            is_commandable=True,
        )

        emergencyStop = binary_value(
            name="EmergencyStop",
            instance=2,
            description="Emergency override button",
            presentValue=False,
            is_commandable=True,
        )

        fanStatus.add_objects_to_application(bacnet)
        switchStatus.add_objects_to_application(bacnet)
        emergencyStop.add_objects_to_application(bacnet)

        fanStatusObj = fanStatus.objects["FanStatus"]
        switchStatusObj = switchStatus.objects["SwitchStatus"]
        emergencyStopObj = emergencyStop.objects["EmergencyStop"]

        fanSystem = FanSystem()

        print(f"BACnet device {bacnetDeviceId} ready at {bacnetIp}")

        while True:
            await asyncio.sleep(0.5)

            switchValue = switchStatusObj.presentValue
            emergencyValue = emergencyStopObj.presentValue

            changed, newFanStatus = fanSystem.update(switchValue, emergencyValue)

            if changed:
                fanStatusObj.presentValue = newFanStatus
                print(f"Fan status changed to: {'ON' if newFanStatus else 'OFF'}")

            if int(datetime.datetime.now().timestamp()) % 5 == 0:
                print(
                    f"State: Fan={fanStatusObj.presentValue}, "
                    f"Switch={switchStatusObj.presentValue}, "
                    f"Emergency={emergencyStopObj.presentValue}"
                )
                await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        print("BACnet server shutting down")
    except Exception as e:
        print(f"System error: {e}")
        if "bacnet" in locals():
            try:
                bacnet.disconnect()
            except:
                pass


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(runBacnet())
    except KeyboardInterrupt:
        print("User interrupted program execution")
    finally:
        pending = asyncio.all_tasks(loop)

        for task in pending:
            task.cancel()

        try:
            loop.run_until_complete(asyncio.sleep(0.1))
        except:
            pass

        loop.close()
